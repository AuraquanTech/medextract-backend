// netlify/functions/mcp.ts
import { Handler } from "@netlify/functions";
import minimatch from "minimatch";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { buildDefaultPolicy, pathAllowed, scanForSecrets, validateWritePlan } from "./policy";
import { ensureBranch, createFilesCommit, openPullRequest, GitHubCtx } from "./github";
import crypto from "crypto";

// === Config ===
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || "https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com")
  .split(",").map(s => s.trim()).filter(Boolean);
const REQUIRE_ORIGIN = (process.env.MCP_HTTP_REQUIRE_ORIGIN ?? "true").toLowerCase() !== "false";
const WORKSPACE_DIR = process.env.WORKSPACE_DIR || "/opt/build/repo";
const VALIDATION_MODE = (process.env.VALIDATION_MODE ?? "false").toLowerCase() === "true";  // relaxes some checks during connector add
const HARD_TIMEOUT_MS = Number(process.env.HARD_TIMEOUT_MS || 8000);                        // per-request cap
const SOFT_RETRY = Number(process.env.SOFT_RETRY || 1);                                     // light retry for transient ops
const METRICS_SAMPLE = Number(process.env.METRICS_SAMPLE || 1);                             // 1=every request

// --- S3 audit (optional but recommended) ---
const AUDIT_S3_BUCKET = process.env.AUDIT_S3_BUCKET || "";
const AUDIT_S3_PREFIX = (process.env.AUDIT_S3_PREFIX || "mcp/audit").replace(/\/+$/,"");
const AWS_ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID || "";
const AWS_SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY || "";
const s3 = AUDIT_S3_BUCKET && AWS_ACCESS_KEY_ID && AWS_SECRET_ACCESS_KEY 
  ? new S3Client({ 
      region: process.env.AWS_REGION || "us-east-1",
      credentials: {
        accessKeyId: AWS_ACCESS_KEY_ID,
        secretAccessKey: AWS_SECRET_ACCESS_KEY,
      }
    }) 
  : null;

// === Metrics ===
const metrics = {
  startedAt: new Date().toISOString(),
  requests: 0,
  lastOrigin: "" as string,
  lastError: "" as string
};

// === Helpers ===
function originAllowed(origin: string): boolean {
  if (!origin) return !REQUIRE_ORIGIN;
  return ALLOWED_ORIGINS.some(p => minimatch(origin, p, { nocase: true }));
}

function corsHeaders(origin: string) {
  const allow = originAllowed(origin);
  return {
    "access-control-allow-origin": allow ? origin : "https://chatgpt.com",
    "access-control-allow-credentials": "true",
    "access-control-allow-headers": "content-type, authorization, mcp-protocol-version, mcp-session-id",
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-max-age": "86400",
  };
}

async function audit(kind: string, payload: any) {
  if (!s3 || !AUDIT_S3_BUCKET) return;
  try {
    const day = new Date().toISOString().slice(0,10);
    const id = crypto.randomUUID();
    const key = `${AUDIT_S3_PREFIX}/${day}/${kind}/${Date.now()}_${id}.json`;
    await s3.send(new PutObjectCommand({
      Bucket: AUDIT_S3_BUCKET,
      Key: key,
      Body: Buffer.from(JSON.stringify(payload, null, 2)),
      ContentType: "application/json"
    }));
  } catch (e:any) {
    // Don't throw; keep serving requests
    console.error("[audit] failed:", e?.message || e);
  }
}

function okJSON(origin: string, body: any) {
  return {
    statusCode: 200,
    headers: { "content-type": "application/json", ...corsHeaders(origin) },
    body: JSON.stringify(body),
  };
}
function bad(status: number, message: string, origin = "") {
  metrics.lastError = message;
  return {
    statusCode: status,
    headers: { "content-type": "application/json", ...corsHeaders(origin) },
    body: JSON.stringify({ error: message }),
  };
}

function withTimeout<T>(p: Promise<T>, ms = HARD_TIMEOUT_MS): Promise<T> {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error(`timeout ${ms}ms`)), ms);
    p.then(v => { clearTimeout(t); resolve(v); })
     .catch(e => { clearTimeout(t); reject(e); });
  });
}

// === Handler ===
export const handler: Handler = async (event) => {
  const origin = event.headers?.origin || event.headers?.Origin || event.headers?.referer || "";
  if ((metrics.requests++ % METRICS_SAMPLE) === 0) metrics.lastOrigin = origin || "";

  // OPTIONS preflight
  if (event.httpMethod === "OPTIONS") {
    return {
      statusCode: 200,
      headers: corsHeaders(origin),
      body: "",
    };
  }

  if (!VALIDATION_MODE && REQUIRE_ORIGIN && !originAllowed(origin)) {
    return bad(403, "Forbidden origin", origin);
  }

  try {
    // --- Manifest & health ---
    if (event.httpMethod === "GET" && event.path.endsWith("/mcp")) {
      return okJSON(origin, {
        tools: [
          { name: "get_diagnostics", description: "Return server diagnostics", inputSchema: { type: "object", properties: {} } },
          { name: "list_files", description: "List files under workspace", inputSchema: { type: "object", properties: { pattern: { type: "string" } } } },
          { name: "read_file", description: "Read a UTF-8 text file", inputSchema: { type: "object", properties: { path: { type: "string" } }, required: ["path"] } },
          { name: "write_file", description: "PR-only writes via GitHub App", inputSchema: { type: "object", properties: { files: { type: "array", items: { type: "object", properties: { path: { type: "string" }, content: { type: "string" } }, required: ["path","content"] } }, title: { type: "string" }, summary: { type: "string" } }, required: ["files"] } },
        ],
      });
    }
    if (event.httpMethod === "GET" && event.path.endsWith("/mcp/health")) {
      return okJSON(origin, { ok: true, startedAt: metrics.startedAt, validationMode: VALIDATION_MODE });
    }
    if (event.httpMethod === "GET" && event.path.endsWith("/mcp/metrics")) {
      return okJSON(origin, metrics);
    }

    // --- JSON-RPC(ish) entrypoint ---
    if (event.httpMethod === "POST" && event.path.endsWith("/mcp")) {
      const body = safeJSON(event.body);
      if (!body) return bad(400, "Invalid JSON", origin);
      const id = body.id ?? null;
      const wrap = async (fn: () => Promise<any>) => {
        try {
          const res = await withTimeout(fn());
          return okJSON(origin, { jsonrpc: "2.0", id, result: res });
        } catch (e:any) {
          metrics.lastError = e?.message || String(e);
          await audit("error", { at: Date.now(), origin, error: metrics.lastError, method: body.method });
          return okJSON(origin, { jsonrpc: "2.0", id, error: { code: -32603, message: "Internal error", data: { detail: metrics.lastError } } });
        }
      };
      if (body.method === "tools/list") {
        return okJSON(origin, { jsonrpc: "2.0", id, result: { tools: [
          { name: "get_diagnostics", description: "Return server diagnostics" },
          { name: "list_files", description: "List files" },
          { name: "read_file", description: "Read file" },
          { name: "write_file", description: "Create PR with changes" },
        ]}});
      }
      if (body.method === "tools/call") {
        const name = body.params?.name;
        const args = body.params?.arguments || {};
        return wrap(() => routeTool(name, args, origin));
      }
      return bad(400, "Unknown method", origin);
    }

    return bad(404, "Not Found", origin);
  } catch (e:any) {
    // Convert accidental 500s to JSON-RPC error so ChatGPT doesn't bail
    console.error("[MCP] Handler error:", e);
    metrics.lastError = e?.message || "Unhandled";
    await audit("error", { at: Date.now(), origin, error: metrics.lastError, stack: e?.stack });
    return okJSON(origin, { jsonrpc: "2.0", id: null, error: { code: -32603, message: "Internal error", data: { detail: metrics.lastError } } });
  }
};

function safeJSON(s?: string | null) {
  try { return s ? JSON.parse(s) : null; } catch { return null; }
}

// --- Tool router ---
async function routeTool(name: string, args: any, origin: string) {
  const cfg = buildDefaultPolicy();
  if (name === "get_diagnostics") {
    return {
      startedAt: metrics.startedAt,
      workspace: WORKSPACE_DIR,
      lastOrigin: metrics.lastOrigin,
      validationMode: VALIDATION_MODE,
      policy: { allow: cfg.allowGlobs, deny: cfg.denyGlobs, maxFiles: cfg.maxFilesChanged, maxBytes: cfg.maxTotalBytes },
    };
  }
  if (name === "list_files") {
    // Minimal fast list: caller can pass back explicit paths they want to read.
    const pattern = String(args?.pattern || "**/*");
    await audit("tool_list_files", { pattern, at: Date.now() });
    // For Netlify runtime, a full recursive walk can be expensive; respond with pattern echo.
    return { patternEcho: pattern, note: "Use read_file for explicit files; runtime FS may be ephemeral." };
  }
  if (name === "read_file") {
    const p = String(args?.path || "");
    if (!p) return { error: "path required" };
    const gate = pathAllowed(p, cfg);
    if (!gate.ok) return { error: gate.reason };
    const fs = await import("fs/promises");
    const full = `${WORKSPACE_DIR}/${p}`.replace(/\/+/g,"/");
    const data = await withTimeout(fs.readFile(full, "utf8"));
    await audit("tool_read_file", { path: p, bytes: Buffer.byteLength(data, "utf8"), at: Date.now() });
    const secretCheck = scanForSecrets(data, cfg);
    return { path: p, content: data, secretMatches: secretCheck.ok ? [] : secretCheck.matches };
  }
  if (name === "write_file") {
    // PR-only flow
    const files = Array.isArray(args?.files) ? args.files : [];
    if (!files.length) return { error: "files[] required" };
    const title = String(args?.title || "MCP changes");
    const summary = String(args?.summary || "Proposed by MCP bridge");

    // Policy: paths + size + secret scan
    for (const f of files) {
      const gate = pathAllowed(String(f.path), cfg);
      if (!gate.ok) return { error: gate.reason };
      const sec = scanForSecrets(String(f.content), cfg);
      if (!sec.ok) return { error: `Secret-like content detected in ${f.path}` };
    }
    const plan = files.map((f:any) => ({ path: String(f.path), contentBytes: Buffer.byteLength(String(f.content), "utf8") }));
    const v = validateWritePlan(plan, cfg);
    if (!v.ok) return { error: v.reason };
    await audit("tool_write_preview", { title, summary, plan, at: Date.now() });

    // If in validation mode, never create PRs.
    if (VALIDATION_MODE) {
      return { preview: true, note: "Validation mode: PR creation disabled", plan };
    }

    // GitHub context
    const gh: GitHubCtx = {
      repo: mustEnv("GITHUB_REPOSITORY"),
      baseBranch: process.env.GITHUB_BASE_BRANCH || "main",
      prBranchPrefix: process.env.GITHUB_PR_PREFIX || "mcp/changes",
      token: mustEnv("GITHUB_TOKEN"),
    };

    // Open PR with retries
    const attempt = async () => {
      const { baseSha, branch } = await ensureBranch(gh);
      await createFilesCommit(gh, branch, baseSha, files.map((f:any) => ({ path: f.path, content: f.content })), title);
      const pr = await openPullRequest(gh, branch, title, summary);
      await audit("tool_write_pr", { prNumber: pr.number, prUrl: pr.html_url, files: plan, at: Date.now() });
      return { prNumber: pr.number, prUrl: pr.html_url, branch };
    };
    try {
      return await withTimeout(attempt());
    } catch (e:any) {
      if (SOFT_RETRY > 0) {
        try { return await withTimeout(attempt()); } catch {}
      }
      const msg = e?.message || "PR flow failed";
      await audit("error", { at: Date.now(), origin, error: msg, tool: "write_file" });
      return { error: msg };
    }
  }
  return { error: `Unknown tool: ${name}` };
}

function mustEnv(k: string): string {
  const v = process.env[k];
  if (!v) throw new Error(`Missing env: ${k}`);
  return v;
}
