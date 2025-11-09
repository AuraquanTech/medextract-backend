/**
 * Netlify MCP Server Function
 * 
 * Location: netlify/functions/mcp.ts
 * 
 * Complete implementation with all MCP tools (read_file, list_files, get_diagnostics, search_code)
 */

import { Handler } from "@netlify/functions";
import { minimatch } from "minimatch";
import { promises as fs } from "fs";
import { join, resolve, sep, posix } from "path";

// ---------------------
// Config (env-driven)
// ---------------------
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || "https://chatgpt.com,https://chat.openai.com")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);
const REQUIRE_ORIGIN = (process.env.MCP_HTTP_REQUIRE_ORIGIN ?? "true").toLowerCase() !== "false";

// Rate limiting (fixed window, in-memory; resets as functions cold-start)
const RATE_WINDOW_MS = Number(process.env.RATE_LIMIT_WINDOW_MS || 60_000);
const RATE_MAX_REQ = Number(process.env.RATE_LIMIT_MAX_REQ || 300);
const ipHits: Map<string, number[]> = new Map();

// Workspace (read-only in Netlify build image). We default to the repo root.
const WORKSPACE_ROOT = process.env.WORKSPACE_DIR || process.cwd();

// Denylist for reads/listing to avoid secrets & heavy dirs
const READ_DENYLIST = [
  "**/.git/**", "**/.github/**", "**/.venv/**", "**/node_modules/**", "**/.env*",
  "**/*id_rsa*", "**/*.pem", "**/*.key", "**/*.p12", "**/*.pfx", "**/*.kdbx",
];

// ---------------------
// Helpers
// ---------------------
function bad(statusCode: number, body: string) {
  return { statusCode, body };
}

function originAllowed(origin: string): boolean {
  if (!REQUIRE_ORIGIN) return true;
  if (!origin) return false;
  return ALLOWED_ORIGINS.some((o) => origin.startsWith(o) || minimatch(origin, o));
}

function clientIp(evt: any): string {
  const xff = evt.headers?.["x-forwarded-for"] || evt.headers?.["X-Forwarded-For"]; // Netlify proxy
  if (xff) return String(xff).split(",")[0].trim();
  return (evt as any)?.ip || evt.headers?.["client-ip"] || "";
}

function rateGate(evt: any) {
  const ip = clientIp(evt) || "unknown";
  const now = Date.now();
  const arr = ipHits.get(ip) || [];
  const fresh = arr.filter((t) => now - t < RATE_WINDOW_MS);
  if (fresh.length >= RATE_MAX_REQ) return bad(429, "Too Many Requests");
  fresh.push(now);
  ipHits.set(ip, fresh);
  return null;
}

function isDenied(relPosix: string): boolean {
  return READ_DENYLIST.some((glob) => minimatch(relPosix, glob));
}

function safeJoinWorkspace(...parts: string[]): string {
  const p = resolve(WORKSPACE_ROOT, ...parts);
  const root = resolve(WORKSPACE_ROOT);
  if (!p.startsWith(root + sep) && p !== root) {
    throw new Error(`Path escapes workspace: ${p}`);
  }
  return p;
}

async function readUtf8(pathAbs: string): Promise<string> {
  const buf = await fs.readFile(pathAbs);
  // Limit to ~2MB to protect function mem/time
  const MAX = Number(process.env.MCP_MAX_FILE_BYTES || 2_000_000);
  if (buf.byteLength > MAX) throw new Error(`File exceeds limit (${buf.byteLength} > ${MAX})`);
  return buf.toString("utf8");
}

// ---------------------
// Tool implementations (Node/Netlify friendly)
// ---------------------
async function tool_read_file(params: { path: string; allow_denied_explicit?: boolean }) {
  if (!params?.path) throw new Error("Missing 'path'");
  const abs = safeJoinWorkspace(params.path);
  const rel = posix.join(...abs.replace(resolve(WORKSPACE_ROOT) + sep, "").split(sep));
  if (!params.allow_denied_explicit && isDenied(rel)) throw new Error("Path denylisted");
  const st = await fs.stat(abs).catch(() => null);
  if (!st || !st.isFile()) throw new Error(`Not a file: ${params.path}`);
  return await readUtf8(abs);
}

async function tool_list_files(params: { base?: string; pattern?: string; max_results?: number; include_denied?: boolean; max_depth?: number }) {
  const base = params?.base || ".";
  const pattern = params?.pattern || "**/*";
  const cap = Math.max(1, Math.min(params?.max_results ?? 2000, 5000));
  const maxDepth = params?.max_depth ?? 25;
  const baseAbs = safeJoinWorkspace(base);

  async function walk(dirAbs: string, depth: number, acc: string[]) {
    if (depth > maxDepth || acc.length >= cap) return;
    const entries = await fs.readdir(dirAbs, { withFileTypes: true });
    for (const e of entries) {
      const full = join(dirAbs, e.name);
      const rel = posix.join(...full.replace(resolve(WORKSPACE_ROOT) + sep, "").split(sep));
      if (e.isDirectory()) {
        if (!isDenied(rel)) await walk(full, depth + 1, acc);
      } else if (e.isFile()) {
        if ((params?.include_denied || !isDenied(rel)) && minimatch(rel, pattern)) {
          acc.push(rel);
          if (acc.length >= cap) break;
        }
      }
    }
  }

  const out: string[] = [];
  await walk(baseAbs, 0, out);
  return out;
}

async function tool_get_diagnostics() {
  return {
    workspace: WORKSPACE_ROOT,
    limits: { read: [100, 3600], write: [50, 3600], command: [20, 3600] },
    denylist: READ_DENYLIST,
    perf_probe_ms: 0,
  };
}

async function tool_write_file(_params: any) {
  // Netlify Functions filesystem is ephemeral at runtime; prefer PR-based writes.
  return {
    error: "NotImplemented",
    message: "Use PR-based writes via GitHub App in production. Ephemeral FS on Netlify."
  };
}

async function tool_search_code(params: { query: string; file_glob?: string; max_results?: number }) {
  const query = params?.query;
  if (!query) throw new Error("Missing 'query'");
  const fileGlob = params?.file_glob || "**/*";
  const cap = Math.max(1, Math.min(params?.max_results ?? 200, 1000));
  const files = await tool_list_files({ pattern: fileGlob, max_results: cap });
  const rx = new RegExp(query, "m");
  const hits: Array<{ file: string; line: number; match: string }> = [];
  for (const rel of files) {
    if (hits.length >= cap) break;
    try {
      const abs = safeJoinWorkspace(rel);
      const text = await readUtf8(abs);
      if (!rx.test(text)) continue;
      // quick line scan
      const lines = text.split(/\n/);
      lines.forEach((ln, idx) => {
        if (rx.test(ln) && hits.length < cap) hits.push({ file: rel, line: idx + 1, match: ln.slice(0, 400) });
      });
    } catch {}
  }
  return hits;
}

// Registry
const TOOLS: Record<string, { fn: (p: any) => Promise<any>; description: string; params: Record<string, string> }> = {
  read_file: { fn: tool_read_file, description: "Read a UTF-8 file", params: { path: "string", allow_denied_explicit: "boolean?" } },
  list_files: { fn: tool_list_files, description: "List files using glob", params: { base: "string?", pattern: "string?", max_results: "number?", include_denied: "boolean?", max_depth: "number?" } },
  write_file: { fn: tool_write_file, description: "Write a file (PR-based recommended)", params: { path: "string", content: "string" } },
  get_diagnostics: { fn: tool_get_diagnostics, description: "Health & limits", params: {} },
  search_code: { fn: tool_search_code, description: "Regex search across files", params: { query: "string", file_glob: "string?", max_results: "number?" } },
};

const RESOURCES = { workspace_tree: "File list", workspace_summary: "Summary", readme: "README" };
const PROMPTS = ["code_review", "debug_assistant", "refactor_suggestion"];

// ---------------------
// Router
// ---------------------
export const handler: Handler = async (event) => {
  try {
    // Origin & rate guard
    const origin = event.headers?.origin || event.headers?.Origin || event.headers?.referer || "";
    if (!originAllowed(origin)) return bad(403, "Forbidden origin");
    const gated = rateGate(event);
    if (gated) return gated;

    const { httpMethod, path } = event;
    const urlPath = (path || event.rawUrl || "").replace(/^https?:\/\/[^/]+/, "");

    // Health
    if (httpMethod === "GET" && urlPath.endsWith("/mcp/health")) {
      return {
        statusCode: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ ok: true, diagnostics: await tool_get_diagnostics() }),
      };
    }

    // Manifest
    if (httpMethod === "GET" && (urlPath.endsWith("/mcp") || urlPath.endsWith("/mcp/"))) {
      return {
        statusCode: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: "cursor-mcp-netlify", version: "1.0", tools: mapToolsForManifest(), resources: RESOURCES, prompts: PROMPTS, workspace: WORKSPACE_ROOT }),
      };
    }

    // Tool call: POST /mcp/tool/:name
    const toolMatch = urlPath.match(/\/mcp\/tool\/([^/?#]+)/);
    if (httpMethod === "POST" && toolMatch) {
      const name = decodeURIComponent(toolMatch[1]);
      const reg = TOOLS[name];
      if (!reg) return bad(404, `Unknown tool: ${name}`);
      const body = parseJson(event.body);
      const params = (body?.params ?? {}) as any;

      const t0 = Date.now();
      try {
        const result = await reg.fn(params);
        const elapsed_ms = Date.now() - t0;
        return json200({ ok: true, result, elapsed_ms });
      } catch (e: any) {
        const elapsed_ms = Date.now() - t0;
        return json200({ ok: false, error: e?.message || String(e), elapsed_ms });
      }
    }

    return bad(404, "Not found");
  } catch (e: any) {
    console.error("mcp handler error", e);
    return { statusCode: 500, body: e?.message || String(e) };
  }
};

function mapToolsForManifest() {
  const out: Record<string, any> = {};
  for (const [k, v] of Object.entries(TOOLS)) out[k] = { description: v.description, params: v.params };
  return out;
}

function parseJson(s?: string | null) {
  if (!s) return {};
  try { return JSON.parse(s); } catch { return {}; }
}

function json200(obj: any) {
  return { statusCode: 200, headers: { "content-type": "application/json" }, body: JSON.stringify(obj) };
}
