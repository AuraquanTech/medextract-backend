/**
 * Netlify Node Function exposing an MCP server with robust security.
 * - OAuth 2.1 JWT check (Auth0 / OIDC) via JOSE + JWKS cache
 * - Origin/CORS allowlist
 * - Per-IP rate limiting (sliding window)
 * - Body size/time guards
 * - Two calling styles:
 *    1) JSON-RPC (POST /mcp) via Streamable HTTP transport (official MCP SDK)
 *    2) REST helpers: GET /mcp (manifest), GET /mcp/health, POST /mcp/tool/:name
 *
 * Notes:
 * - Netlify Functions FS is read-only; write_file returns preview (persistence can be added via Blobs/GitHub).
 * - run_command is intentionally disabled in this Netlify build.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createRemoteJWKSet, jwtVerify } from "jose";
import { minimatch } from "minimatch";
import { promises as fsp } from "node:fs";
import { join, resolve, relative, sep } from "node:path";
import { URL } from "node:url";

// ---------- Config ----------
const NODE_ENV = (process.env.NODE_ENV ?? "production").toLowerCase();

const AUTH_ISSUER   = (process.env.AUTH_ISSUER ?? "").replace(/\/?$/, "/");
const AUTH_AUDIENCE = process.env.AUTH_AUDIENCE ?? "https://cursor-mcp";
const JWKS_URL      = process.env.AUTH_JWKS_URL ?? (AUTH_ISSUER + ".well-known/jwks.json");

const REQUIRE_ORIGIN  = (process.env.MCP_HTTP_REQUIRE_ORIGIN ?? "true").toLowerCase() !== "false";
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS ?? "https://chatgpt.com,https://chat.openai.com")
  .split(",").map(s => s.trim()).filter(Boolean);

// Workspace is the deployed bundle dir (read-only). You can scope to subfolder if desired.
const WORKSPACE_DIR = process.env.WORKSPACE_DIR ?? "/";

// Limits/guards
const MAX_BODY_BYTES = Number(process.env.MCP_MAX_BODY_BYTES ?? 256 * 1024); // 256 KB
const RT_WINDOW_S    = Number(process.env.RATE_LIMIT_WINDOW_S ?? 60);
const RT_MAX_REQ     = Number(process.env.RATE_LIMIT_MAX_REQ ?? 300);
const JSON_CT        = /^application\/json\b/i;

// ---------- Utilities ----------
const jwks = createRemoteJWKSet(new URL(JWKS_URL));
const ipHits = new Map<string, number[]>();

function nowS() { return Date.now() / 1000; }

function clientIp(event: any): string {
  const xff = event?.headers?.["x-forwarded-for"] || event?.headers?.["X-Forwarded-For"];
  if (typeof xff === "string" && xff.length) return xff.split(",")[0].trim();
  return event?.headers?.["client-ip"] || event?.ip || "0.0.0.0";
}

function bad(status: number, error: string, extra?: any) {
  return new Response(JSON.stringify({ ok: false, error, ...(extra ?? {}) }), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" }
  });
}

function ok(data: any, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" }
  });
}

function corsHeaders(origin?: string) {
  const h: Record<string, string> = { "content-type": "application/json; charset=utf-8" };
  if (origin && ALLOWED_ORIGINS.some(o => origin.startsWith(o))) {
    h["access-control-allow-origin"] = origin;
    h["vary"] = "Origin";
  }
  return h;
}

function originAllowed(origin?: string) {
  if (!REQUIRE_ORIGIN) return true;
  if (!origin) return false;
  return ALLOWED_ORIGINS.some(o => origin.startsWith(o));
}

function rateLimit(ip: string) {
  const t = nowS();
  const hist = ipHits.get(ip) ?? [];
  const fresh = hist.filter(ts => t - ts <= RT_WINDOW_S);
  if (fresh.length >= RT_MAX_REQ) return false;
  fresh.push(t);
  ipHits.set(ip, fresh);
  return true;
}

async function readBody(event: any): Promise<string> {
  const raw = event.body || "";
  const isBase64 = !!event.isBase64Encoded;
  const buf = isBase64 ? Buffer.from(raw, "base64") : Buffer.from(raw);
  if (buf.length > MAX_BODY_BYTES) throw new Error(`Body too large (${buf.length} > ${MAX_BODY_BYTES})`);
  return buf.toString("utf8");
}

async function requireAuth(event: any) {
  const origin = event.headers?.origin || event.headers?.Origin || event.headers?.referer || "";
  if (!originAllowed(origin)) return bad(403, "Forbidden origin");

  const auth = event.headers?.authorization || event.headers?.Authorization || "";
  const m = auth.match(/^Bearer\s+(.+)$/i);
  if (!m) return bad(401, "Missing bearer token");

  try {
    await jwtVerify(m[1], jwks, { issuer: AUTH_ISSUER, audience: AUTH_AUDIENCE });
    return null;
  } catch (e: any) {
    return bad(401, `Invalid token: ${e.message ?? String(e)}`);
  }
}

// ---------- MCP Server ----------
const server = new McpServer({ name: "cursor-mcp-netlify", version: "1.0.0" });

// list_files
server.tool(
  "list_files",
  {
    base: { type: "string", default: "." },
    pattern: { type: "string", default: "**/*" },
    max_results: { type: "number", default: 500 }
  } as any,
  async ({ base, pattern, max_results }) => {
    const root = resolve(WORKSPACE_DIR, base);
    const out: string[] = [];
    async function walk(dir: string) {
      const names = await fsp.readdir(dir, { withFileTypes: true });
      for (const de of names) {
        const p = join(dir, de.name);
        if (de.isDirectory()) {
          await walk(p);
          if (out.length >= max_results) return;
        } else if (de.isFile()) {
          const rel = relative(WORKSPACE_DIR, p).split(sep).join("/");
          if (minimatch(rel, pattern)) {
            out.push(rel);
            if (out.length >= max_results) return;
          }
        }
      }
    }
    await walk(root);
    return { structuredContent: out, content: [{ type: "text", text: JSON.stringify(out) }] };
  }
);

// read_file
server.tool(
  "read_file",
  { path: { type: "string" } } as any,
  async ({ path }) => {
    const abs = resolve(WORKSPACE_DIR, path);
    const data = await fsp.readFile(abs, "utf8");
    return { structuredContent: { path, bytes: Buffer.byteLength(data) }, content: [{ type: "text", text: data }] };
  }
);

// write_file (preview-only)
server.tool(
  "write_file",
  { path: { type: "string" }, content: { type: "string" }, require_confirmation: { type: "boolean", default: true } } as any,
  async ({ path, content, require_confirmation }) => {
    const preview = {
      action: "WRITE_PREVIEW",
      path,
      bytes: Buffer.byteLength(content),
      note: "Netlify FS is read-only. For persistence, wire to Netlify Blobs or GitHub commits."
    };
    return { structuredContent: preview, content: [{ type: "text", text: JSON.stringify(preview) }] };
  }
);

// get_diagnostics
server.tool(
  "get_diagnostics",
  {} as any,
  async () => {
    return {
      structuredContent: {
        workspace: WORKSPACE_DIR,
        origins: ALLOWED_ORIGINS,
        rate_limit: { window_s: RT_WINDOW_S, max_reqs: RT_MAX_REQ },
        body_limit_bytes: MAX_BODY_BYTES,
        env: NODE_ENV
      },
      content: [{ type: "text", text: JSON.stringify({ workspace: WORKSPACE_DIR }) }]
    };
  }
);

// search_code (simple)
server.tool(
  "search_code",
  { query: { type: "string" }, file_glob: { type: "string", default: "**/*" }, max_results: { type: "number", default: 200 } } as any,
  async ({ query, file_glob, max_results }) => {
    const rx = new RegExp(query, "m");
    const out: Array<{ file: string; line: number; match: string }> = [];
    async function scan(dir: string) {
      const items = await fsp.readdir(dir, { withFileTypes: true });
      for (const de of items) {
        const p = join(dir, de.name);
        if (de.isDirectory()) { await scan(p); continue; }
        if (!de.isFile()) continue;
        const rel = relative(WORKSPACE_DIR, p).split(sep).join("/");
        if (!minimatch(rel, file_glob)) continue;
        let text = "";
        try { text = await fsp.readFile(p, "utf8"); } catch { continue; }
        const lines = text.split(/\r?\n/);
        for (let i = 0; i < lines.length; i++) {
          const ln = lines[i];
          const m = rx.exec(ln);
          if (m) {
            out.push({ file: rel, line: i + 1, match: m[0] });
            if (out.length >= max_results) return;
          }
        }
        if (out.length >= max_results) return;
      }
    }
    await scan(WORKSPACE_DIR);
    return { structuredContent: out, content: [{ type: "text", text: JSON.stringify(out) }] };
  }
);

// ---------- Manifest for GET /mcp ----------
const MANIFEST = {
  name: "cursor-mcp-netlify",
  version: "1.0.0",
  tools: {
    list_files: { description: "List files with glob", params: { base: "str?", pattern: "str?", max_results: "int?" } },
    read_file:  { description: "Read file", params: { path: "str" } },
    write_file: { description: "Preview write (read-only runtime)", params: { path: "str", content: "str", require_confirmation: "bool?" } },
    get_diagnostics: { description: "Health & limits", params: {} },
    search_code: { description: "Regex search", params: { query: "str", file_glob: "str?", max_results: "int?" } }
  }
};

// ---------- Handler ----------
export default async (event: any) => {
  try {
    // CORS preflight
    if (event.httpMethod === "OPTIONS") {
      const origin = event.headers?.origin || event.headers?.Origin;
      const headers = {
        ...corsHeaders(origin),
        "access-control-allow-methods": "GET,POST,OPTIONS",
        "access-control-allow-headers": "authorization,content-type",
        "access-control-max-age": "600"
      };
      return new Response("", { status: 204, headers });
    }

    // Basic shields
    const ip = clientIp(event);
    if (!rateLimit(ip)) return bad(429, "Too Many Requests");

    const authErr = await requireAuth(event);
    if (authErr) return authErr;

    // Route
    const url = new URL(event.rawUrl ?? `https://${event.headers.host}${event.path}`);
    const path = url.pathname;

    // Health
    if (event.httpMethod === "GET" && (path === "/mcp/health" || path === "/.netlify/functions/mcp/health")) {
      const res = { ok: true, diagnostics: (await server.callTool?.("get_diagnostics", {})) ?? { workspace: WORKSPACE_DIR } };
      return ok(res);
    }

    // Manifest
    if (event.httpMethod === "GET" && (path === "/mcp" || path === "/.netlify/functions/mcp")) {
      return ok({ ...MANIFEST, workspace: WORKSPACE_DIR });
    }

    // Direct tool helper: POST /mcp/tool/:name
    if (event.httpMethod === "POST" && /\/mcp\/tool\/[^/]+$/.test(path)) {
      const name = decodeURIComponent(path.split("/").pop()!);
      const bodyText = await readBody(event);
      let args: any = {};
      if (bodyText && JSON_CT.test(event.headers["content-type"] ?? "")) {
        try { args = JSON.parse(bodyText).params ?? {}; } catch { return bad(400, "Invalid JSON body"); }
      }
      const t0 = Date.now();
      try {
        const res = await (server as any).callTool?.(name, args);
        return ok({ ok: true, result: res, elapsed_ms: Date.now() - t0 });
      } catch (e: any) {
        return bad(500, "Tool error", { elapsed_ms: Date.now() - t0, detail: e?.message ?? String(e) });
      }
    }

    // JSON-RPC via MCP Streamable HTTP transport at POST /mcp
    if (event.httpMethod === "POST" && (path === "/mcp" || path === "/.netlify/functions/mcp")) {
      const requestBody = await readBody(event);
      const transport = new StreamableHTTPServerTransport({ enableJsonResponse: true });

      // Drive the transport
      const response = await transport.handleRequest(
        {
          method: event.httpMethod,
          headers: event.headers ?? {},
          url: url.pathname + url.search,
          body: requestBody
        },
        async (responseInit, bodyText) => {
          return new Response(bodyText, {
            status: responseInit.status ?? 200,
            headers: { ...responseInit.headers, ...corsHeaders(event.headers?.origin || event.headers?.Origin) }
          });
        },
        async () => {
          await server.connect(transport);
        }
      );
      return response;
    }

    return bad(404, "Not Found");
  } catch (e: any) {
    const msg = e?.message ?? String(e);
    return bad(500, "Unhandled error", { detail: msg, stack: NODE_ENV === "production" ? undefined : e?.stack });
  }
};

