# MCP Full Arsenal Playbook

**Status**: Ready for review - DO NOT IMPLEMENT YET

This playbook contains copy-pasteable patches and exact steps to drop the **Full Arsenal** into your repo. This includes: S3 audit logging, validation mode, safer origin handling, tight timeouts/retries, diagnostics, metrics, policy gates, and PR-only writes via GitHub App.

---

## 1) Unified Patches (drop into Cursor → "Apply Patch")

> If a file already exists, the patch updates it. If not, it creates it.

### Patch 1: Policy Engine (`netlify/functions/policy.ts`)

```diff
*** Begin Patch
*** Add File: netlify/functions/policy.ts
+// Lightweight policy engine: allow/deny globs, basic secret scanning, max PR size.
+import minimatch from "minimatch";
+
+export type PolicyConfig = {
+  allowGlobs: string[];
+  denyGlobs: string[];
+  maxFilesChanged: number;       // hard cap on number of files per PR
+  maxTotalBytes: number;         // hard cap on byte sum for write_file operations
+  secretRegexes: RegExp[];       // patterns to block exfil/secrets
+};
+
+export type WritePlanItem = {
+  path: string;
+  contentBytes: number;
+};
+
+export function buildDefaultPolicy(): PolicyConfig {
+  const defaultSecretPatterns = [
+    /\bAKIA[0-9A-Z]{16}\b/i,                       // AWS Access Key
+    /\bghp_[0-9A-Za-z]{36}\b/i,                    // GitHub classic token
+    /-----BEGIN(\sRSA)?\sPRIVATE KEY-----/i,       // PEM private keys
+    /\b(xox[baprs]-[0-9A-Za-z-]{10,})\b/i,         // Slack tokens
+    /\bAIza[0-9A-Za-z\-_]{35}\b/i,                 // Google API keys
+  ];
+  return {
+    allowGlobs: (process.env.POLICY_ALLOW_GLOBS || "**/*").split(",").map(s => s.trim()).filter(Boolean),
+    denyGlobs: (process.env.POLICY_DENY_GLOBS || ".env,**/.git/**,**/.ssh/**,**/*.key,**/*.pem,**/*.p12,**/*.pfx,**/*.kdbx").split(",").map(s => s.trim()).filter(Boolean),
+    maxFilesChanged: Number(process.env.POLICY_MAX_FILES || 20),
+    maxTotalBytes: Number(process.env.POLICY_MAX_BYTES || 512 * 1024),
+    secretRegexes: defaultSecretPatterns,
+  };
+}
+
+export function pathAllowed(path: string, cfg: PolicyConfig): { ok: boolean; reason?: string } {
+  for (const d of cfg.denyGlobs) {
+    if (d && minimatch(path, d, { dot: true })) {
+      return { ok: false, reason: `Path '${path}' matches deny rule '${d}'` };
+    }
+  }
+  let allowed = false;
+  for (const a of cfg.allowGlobs) {
+    if (a && minimatch(path, a, { dot: true })) { allowed = true; break; }
+  }
+  if (!allowed) return { ok: false, reason: `Path '${path}' does not match any allow rule` };
+  return { ok: true };
+}
+
+export function scanForSecrets(text: string, cfg: PolicyConfig): { ok: boolean; matches?: string[] } {
+  const hits: string[] = [];
+  for (const re of cfg.secretRegexes) {
+    if (re.test(text)) hits.push(re.source);
+  }
+  return { ok: hits.length === 0, matches: hits };
+}
+
+export function validateWritePlan(plan: WritePlanItem[], cfg: PolicyConfig): { ok: boolean; reason?: string } {
+  if (plan.length > cfg.maxFilesChanged) {
+    return { ok: false, reason: `Plan changes ${plan.length} files; cap is ${cfg.maxFilesChanged}` };
+  }
+  const total = plan.reduce((s, i) => s + (i.contentBytes || 0), 0);
+  if (total > cfg.maxTotalBytes) {
+    return { ok: false, reason: `Plan total size ${total} exceeds cap ${cfg.maxTotalBytes}` };
+  }
+  return { ok: true };
+}
+
*** End Patch
```

### Patch 2: GitHub Helper (`netlify/functions/github.ts`)

```diff
*** Begin Patch
*** Add File: netlify/functions/github.ts
+// Minimal GitHub App helper for PR-only writes
+import fetch from "node-fetch";
+
+type CreateBlobResp = { sha: string };
+type CreateTreeResp = { sha: string };
+type CreateCommitResp = { sha: string };
+
+const GH_API = "https://api.github.com";
+
+export type GitHubCtx = {
+  repo: string;            // "owner/name"
+  baseBranch: string;      // e.g., "main"
+  prBranchPrefix: string;  // e.g., "mcp/batch"
+  token: string;           // GitHub App installation token or PAT (installation token preferred)
+};
+
+export async function ensureBranch(ctx: GitHubCtx): Promise<{ baseSha: string; branch: string }> {
+  const headers = ghHeaders(ctx.token);
+  const refResp = await fetch(`${GH_API}/repos/${ctx.repo}/git/ref/heads/${ctx.baseBranch}`, { headers });
+  if (!refResp.ok) throw new Error(`Failed get base ref: ${refResp.status}`);
+  const refJson = await refResp.json() as any;
+  const baseSha = refJson.object.sha;
+  const branch = `${ctx.prBranchPrefix}/${Date.now()}`;
+  const createRef = await fetch(`${GH_API}/repos/${ctx.repo}/git/refs`, {
+    method: "POST",
+    headers,
+    body: JSON.stringify({ ref: `refs/heads/${branch}`, sha: baseSha }),
+  });
+  if (!createRef.ok) throw new Error(`Failed create branch: ${createRef.status}`);
+  return { baseSha, branch };
+}
+
+export async function createFilesCommit(ctx: GitHubCtx, branch: string, baseSha: string, files: { path: string; content: string }[], message: string) {
+  const headers = ghHeaders(ctx.token);
+  // 1) blobs
+  const blobs = await Promise.all(files.map(async f => {
+    const r = await fetch(`${GH_API}/repos/${ctx.repo}/git/blobs`, {
+      method: "POST",
+      headers,
+      body: JSON.stringify({ content: f.content, encoding: "utf-8" })
+    });
+    if (!r.ok) throw new Error(`blob failed for ${f.path}: ${r.status}`);
+    return { path: f.path, sha: (await r.json() as CreateBlobResp).sha, mode: "100644", type: "blob" };
+  }));
+  // 2) tree
+  const treeResp = await fetch(`${GH_API}/repos/${ctx.repo}/git/trees`, {
+    method: "POST",
+    headers,
+    body: JSON.stringify({ base_tree: baseSha, tree: blobs }),
+  });
+  if (!treeResp.ok) throw new Error(`tree failed: ${treeResp.status}`);
+  const treeSha = (await treeResp.json() as CreateTreeResp).sha;
+  // 3) commit
+  const commitResp = await fetch(`${GH_API}/repos/${ctx.repo}/git/commits`, {
+    method: "POST",
+    headers,
+    body: JSON.stringify({ message, tree: treeSha, parents: [baseSha] })
+  });
+  if (!commitResp.ok) throw new Error(`commit failed: ${commitResp.status}`);
+  const commitSha = (await commitResp.json() as CreateCommitResp).sha;
+  // 4) update ref
+  const refResp = await fetch(`${GH_API}/repos/${ctx.repo}/git/refs/heads/${branch}`, {
+    method: "PATCH",
+    headers,
+    body: JSON.stringify({ sha: commitSha, force: false })
+  });
+  if (!refResp.ok) throw new Error(`update ref failed: ${refResp.status}`);
+}
+
+export async function openPullRequest(ctx: GitHubCtx, branch: string, title: string, body: string) {
+  const headers = ghHeaders(ctx.token);
+  const pr = await fetch(`${GH_API}/repos/${ctx.repo}/pulls`, {
+    method: "POST",
+    headers,
+    body: JSON.stringify({ title, head: branch, base: ctx.baseBranch, body }),
+  });
+  if (!pr.ok) throw new Error(`PR failed: ${pr.status}`);
+  return pr.json();
+}
+
+function ghHeaders(token: string) {
+  return {
+    "authorization": `Bearer ${token}`,
+    "accept": "application/vnd.github+json",
+    "user-agent": "nexusmcp-bridge"
+  };
+}
+
*** End Patch
```

### Patch 3: Main MCP Function (`netlify/functions/mcp.ts`)

```diff
*** Begin Patch
*** Update File: netlify/functions/mcp.ts
@@
-import { Handler } from "@netlify/functions";
-import minimatch from "minimatch";
+import { Handler } from "@netlify/functions";
+import minimatch from "minimatch";
+import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
+import { buildDefaultPolicy, pathAllowed, scanForSecrets, validateWritePlan } from "./policy";
+import { ensureBranch, createFilesCommit, openPullRequest, GitHubCtx } from "./github";
+import crypto from "crypto";
 
-// === Config ===
-const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || "https://chatgpt.com,https://chat.openai.com")
+// === Config ===
+const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || "https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com")
   .split(",").map(s => s.trim()).filter(Boolean);
 const REQUIRE_ORIGIN = (process.env.MCP_HTTP_REQUIRE_ORIGIN ?? "true").toLowerCase() !== "false";
-const WORKSPACE_DIR = process.env.WORKSPACE_DIR || "/opt/build/repo";
+const WORKSPACE_DIR = process.env.WORKSPACE_DIR || "/opt/build/repo";
+const VALIDATION_MODE = (process.env.VALIDATION_MODE ?? "false").toLowerCase() === "true";  // relaxes some checks during connector add
+const HARD_TIMEOUT_MS = Number(process.env.HARD_TIMEOUT_MS || 8000);                        // per-request cap
+const SOFT_RETRY = Number(process.env.SOFT_RETRY || 1);                                     // light retry for transient ops
+const METRICS_SAMPLE = Number(process.env.METRICS_SAMPLE || 1);                             // 1=every request
+
+// --- S3 audit (optional but recommended) ---
+const AUDIT_S3_BUCKET = process.env.AUDIT_S3_BUCKET || "";
+const AUDIT_S3_PREFIX = (process.env.AUDIT_S3_PREFIX || "mcp/audit").replace(/\/+$/,"");
+const s3 = AUDIT_S3_BUCKET ? new S3Client({ region: process.env.AWS_REGION || "us-east-1" }) : null;
 
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
-  return ALLOWED_ORIGINS.some(p => minimatch(origin, p, { nocase: true }));
+  return ALLOWED_ORIGINS.some(p => minimatch(origin, p, { nocase: true }));
 }
 
 function corsHeaders(origin: string) {
   const allow = originAllowed(origin);
   return {
     "access-control-allow-origin": allow ? origin : "https://chatgpt.com",
     "access-control-allow-credentials": "true",
-    "access-control-allow-headers": "content-type, authorization, mcp-protocol-version, mcp-session-id",
+    "access-control-allow-headers": "content-type, authorization, mcp-protocol-version, mcp-session-id",
     "access-control-allow-methods": "GET, POST, OPTIONS",
     "access-control-max-age": "86400",
   };
 }
 
+async function audit(kind: string, payload: any) {
+  if (!s3 || !AUDIT_S3_BUCKET) return;
+  try {
+    const day = new Date().toISOString().slice(0,10);
+    const id = crypto.randomUUID();
+    const key = `${AUDIT_S3_PREFIX}/${day}/${kind}/${Date.now()}_${id}.json`;
+    await s3.send(new PutObjectCommand({
+      Bucket: AUDIT_S3_BUCKET,
+      Key: key,
+      Body: Buffer.from(JSON.stringify(payload, null, 2)),
+      ContentType: "application/json"
+    }));
+  } catch (e:any) {
+    // Don't throw; keep serving requests
+    console.error("[audit] failed:", e?.message || e);
+  }
+}
+
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
 
+function withTimeout<T>(p: Promise<T>, ms = HARD_TIMEOUT_MS): Promise<T> {
+  return new Promise((resolve, reject) => {
+    const t = setTimeout(() => reject(new Error(`timeout ${ms}ms`)), ms);
+    p.then(v => { clearTimeout(t); resolve(v); })
+     .catch(e => { clearTimeout(t); reject(e); });
+  });
+}
+
 // === Handler ===
 export const handler: Handler = async (event) => {
-  const origin = event.headers?.origin || event.headers?.Origin || event.headers?.referer || "";
-  metrics.requests++; metrics.lastOrigin = origin || "";
+  const origin = event.headers?.origin || event.headers?.Origin || event.headers?.referer || "";
+  if ((metrics.requests++ % METRICS_SAMPLE) === 0) metrics.lastOrigin = origin || "";
 
   // OPTIONS preflight
   if (event.httpMethod === "OPTIONS") {
     return {
       statusCode: 200,
       headers: corsHeaders(origin),
       body: "",
     };
   }
 
-  if (REQUIRE_ORIGIN && !originAllowed(origin)) {
+  if (!VALIDATION_MODE && REQUIRE_ORIGIN && !originAllowed(origin)) {
     return bad(403, "Forbidden origin", origin);
   }
 
-  try {
-    if (event.httpMethod === "GET" && event.path.endsWith("/mcp")) {
-      // Manifest
-      return okJSON(origin, {
-        tools: [
-          { name: "get_diagnostics", description: "Return server diagnostics", inputSchema: { type: "object", properties: {} } },
-          { name: "list_files", description: "List files under workspace", inputSchema: { type: "object", properties: { pattern: { type: "string" } } } },
-          { name: "read_file", description: "Read a file", inputSchema: { type: "object", properties: { path: { type: "string" } }, required: ["path"] } },
-          { name: "write_file", description: "Propose changes (PR-only)", inputSchema: { type: "object", properties: { files: { type: "array", items: { type: "object", properties: { path: { type: "string" }, content: { type: "string" } }, required: ["path","content"] } }, title: { type: "string" }, summary: { type: "string" } }, required: ["files"] } },
-        ],
-      });
-    }
-    if (event.httpMethod === "GET" && event.path.endsWith("/mcp/health")) {
-      return okJSON(origin, { ok: true, startedAt: metrics.startedAt });
-    }
-    if (event.httpMethod === "GET" && event.path.endsWith("/mcp/metrics")) {
-      return okJSON(origin, metrics);
-    }
-    if (event.httpMethod === "POST" && event.path.endsWith("/mcp")) {
-      // JSON-RPC(ish) shim for tools/list & tools/call
-      const body = safeJSON(event.body);
-      if (!body) return bad(400, "Invalid JSON", origin);
-      if (body.method === "tools/list") {
-        return okJSON(origin, {
-          jsonrpc: "2.0",
-          id: body.id ?? null,
-          result: {
-            tools: [
-              { name: "get_diagnostics", description: "Return server diagnostics" },
-              { name: "list_files", description: "List files" },
-              { name: "read_file", description: "Read file" },
-              { name: "write_file", description: "Create PR with changes" },
-            ]
-          }
-        });
-      }
-      if (body.method === "tools/call") {
-        const name = body.params?.name;
-        const args = body.params?.arguments || {};
-        return await routeTool(name, args, origin);
-      }
-      return bad(400, "Unknown method", origin);
-    }
-    return bad(404, "Not Found", origin);
-  } catch (e:any) {
-    console.error(e);
-    return bad(500, e?.message || "Internal error", origin);
-  }
+  try {
+    // --- Manifest & health ---
+    if (event.httpMethod === "GET" && event.path.endsWith("/mcp")) {
+      return okJSON(origin, {
+        tools: [
+          { name: "get_diagnostics", description: "Return server diagnostics", inputSchema: { type: "object", properties: {} } },
+          { name: "list_files", description: "List files under workspace", inputSchema: { type: "object", properties: { pattern: { type: "string" } } } },
+          { name: "read_file", description: "Read a UTF-8 text file", inputSchema: { type: "object", properties: { path: { type: "string" } }, required: ["path"] } },
+          { name: "write_file", description: "PR-only writes via GitHub App", inputSchema: { type: "object", properties: { files: { type: "array", items: { type: "object", properties: { path: { type: "string" }, content: { type: "string" } }, required: ["path","content"] } }, title: { type: "string" }, summary: { type: "string" } }, required: ["files"] } },
+        ],
+      });
+    }
+    if (event.httpMethod === "GET" && event.path.endsWith("/mcp/health")) {
+      return okJSON(origin, { ok: true, startedAt: metrics.startedAt, validationMode: VALIDATION_MODE });
+    }
+    if (event.httpMethod === "GET" && event.path.endsWith("/mcp/metrics")) {
+      return okJSON(origin, metrics);
+    }
+
+    // --- JSON-RPC(ish) entrypoint ---
+    if (event.httpMethod === "POST" && event.path.endsWith("/mcp")) {
+      const body = safeJSON(event.body);
+      if (!body) return bad(400, "Invalid JSON", origin);
+      const id = body.id ?? null;
+      const wrap = async (fn: () => Promise<any>) => {
+        try {
+          const res = await withTimeout(fn());
+          return okJSON(origin, { jsonrpc: "2.0", id, result: res });
+        } catch (e:any) {
+          metrics.lastError = e?.message || String(e);
+          await audit("error", { at: Date.now(), origin, error: metrics.lastError, method: body.method });
+          return okJSON(origin, { jsonrpc: "2.0", id, error: { code: -32603, message: "Internal error", data: { detail: metrics.lastError } } });
+        }
+      };
+      if (body.method === "tools/list") {
+        return okJSON(origin, { jsonrpc: "2.0", id, result: { tools: [
+          { name: "get_diagnostics", description: "Return server diagnostics" },
+          { name: "list_files", description: "List files" },
+          { name: "read_file", description: "Read file" },
+          { name: "write_file", description: "Create PR with changes" },
+        ]}});
+      }
+      if (body.method === "tools/call") {
+        const name = body.params?.name;
+        const args = body.params?.arguments || {};
+        return wrap(() => routeTool(name, args, origin));
+      }
+      return bad(400, "Unknown method", origin);
+    }
+
+    return bad(404, "Not Found", origin);
+  } catch (e:any) {
+    // Convert accidental 500s to JSON-RPC error so ChatGPT doesn't bail
+    console.error("[MCP] Handler error:", e);
+    metrics.lastError = e?.message || "Unhandled";
+    await audit("error", { at: Date.now(), origin, error: metrics.lastError, stack: e?.stack });
+    return okJSON(origin, { jsonrpc: "2.0", id: null, error: { code: -32603, message: "Internal error", data: { detail: metrics.lastError } } });
+  }
 };
 
 function safeJSON(s?: string | null) {
   try { return s ? JSON.parse(s) : null; } catch { return null; }
 }
 
-// --- Tool router (stubs) ---
+// --- Tool router ---
 async function routeTool(name: string, args: any, origin: string) {
-  if (name === "get_diagnostics") {
-    return { startedAt: metrics.startedAt, workspace: WORKSPACE_DIR, lastOrigin: metrics.lastOrigin };
-  }
-  if (name === "list_files") {
-    const pattern = args?.pattern || "**/*";
-    // Shallow fake; in a real impl you'd walk WORKSPACE_DIR
-    return { entries: [{ path: "README.md", size: 12, type: "file" }] };
-  }
-  if (name === "read_file") {
-    const p = String(args?.path || "");
-    if (!p) return { error: "path required" };
-    if (!minimatch(p, "**/*", { dot: true })) return { error: "invalid path" };
-    // demo content
-    return { path: p, content: "Hello from MCP bridge" };
-  }
-  if (name === "write_file") {
-    // v1 PR-only stub
-    return { plan: { changes: (args?.files || []).length }, preview: true, note: "PR-only mode" };
-  }
-  return { error: `Unknown tool: ${name}` };
+  const cfg = buildDefaultPolicy();
+  if (name === "get_diagnostics") {
+    return {
+      startedAt: metrics.startedAt,
+      workspace: WORKSPACE_DIR,
+      lastOrigin: metrics.lastOrigin,
+      validationMode: VALIDATION_MODE,
+      policy: { allow: cfg.allowGlobs, deny: cfg.denyGlobs, maxFiles: cfg.maxFilesChanged, maxBytes: cfg.maxTotalBytes },
+    };
+  }
+  if (name === "list_files") {
+    // Minimal fast list: caller can pass back explicit paths they want to read.
+    const pattern = String(args?.pattern || "**/*");
+    await audit("tool_list_files", { pattern, at: Date.now() });
+    // For Netlify runtime, a full recursive walk can be expensive; respond with pattern echo.
+    return { patternEcho: pattern, note: "Use read_file for explicit files; runtime FS may be ephemeral." };
+  }
+  if (name === "read_file") {
+    const p = String(args?.path || "");
+    if (!p) return { error: "path required" };
+    const gate = pathAllowed(p, cfg);
+    if (!gate.ok) return { error: gate.reason };
+    const fs = await import("fs/promises");
+    const full = `${WORKSPACE_DIR}/${p}`.replace(/\/+/g,"/");
+    const data = await withTimeout(fs.readFile(full, "utf8"));
+    await audit("tool_read_file", { path: p, bytes: Buffer.byteLength(data, "utf8"), at: Date.now() });
+    const secretCheck = scanForSecrets(data, cfg);
+    return { path: p, content: data, secretMatches: secretCheck.ok ? [] : secretCheck.matches };
+  }
+  if (name === "write_file") {
+    // PR-only flow
+    const files = Array.isArray(args?.files) ? args.files : [];
+    if (!files.length) return { error: "files[] required" };
+    const title = String(args?.title || "MCP changes");
+    const summary = String(args?.summary || "Proposed by MCP bridge");
+
+    // Policy: paths + size + secret scan
+    for (const f of files) {
+      const gate = pathAllowed(String(f.path), cfg);
+      if (!gate.ok) return { error: gate.reason };
+      const sec = scanForSecrets(String(f.content), cfg);
+      if (!sec.ok) return { error: `Secret-like content detected in ${f.path}` };
+    }
+    const plan = files.map((f:any) => ({ path: String(f.path), contentBytes: Buffer.byteLength(String(f.content), "utf8") }));
+    const v = validateWritePlan(plan, cfg);
+    if (!v.ok) return { error: v.reason };
+    await audit("tool_write_preview", { title, summary, plan, at: Date.now() });
+
+    // If in validation mode, never create PRs.
+    if (VALIDATION_MODE) {
+      return { preview: true, note: "Validation mode: PR creation disabled", plan };
+    }
+
+    // GitHub context
+    const gh: GitHubCtx = {
+      repo: mustEnv("GITHUB_REPOSITORY"),
+      baseBranch: process.env.GITHUB_BASE_BRANCH || "main",
+      prBranchPrefix: process.env.GITHUB_PR_PREFIX || "mcp/changes",
+      token: mustEnv("GITHUB_TOKEN"),
+    };
+
+    // Open PR with retries
+    const attempt = async () => {
+      const { baseSha, branch } = await ensureBranch(gh);
+      await createFilesCommit(gh, branch, baseSha, files.map((f:any) => ({ path: f.path, content: f.content })), title);
+      const pr = await openPullRequest(gh, branch, title, summary);
+      await audit("tool_write_pr", { prNumber: pr.number, prUrl: pr.html_url, files: plan, at: Date.now() });
+      return { prNumber: pr.number, prUrl: pr.html_url, branch };
+    };
+    try {
+      return await withTimeout(attempt());
+    } catch (e:any) {
+      if (SOFT_RETRY > 0) {
+        try { return await withTimeout(attempt()); } catch {}
+      }
+      const msg = e?.message || "PR flow failed";
+      await audit("error", { at: Date.now(), origin, error: msg, tool: "write_file" });
+      return { error: msg };
+    }
+  }
+  return { error: `Unknown tool: ${name}` };
 }
 
 function mustEnv(k: string): string {
   const v = process.env[k];
   if (!v) throw new Error(`Missing env: ${k}`);
   return v;
 }
*** End Patch
```

### Patch 4: Package Dependencies (`package.json`)

```diff
*** Begin Patch
*** Update File: package.json
@@
 {
   "name": "cursor-mcp-http-bridge",
   "private": true,
-  "engines": { "node": ">=18" },
+  "engines": { "node": ">=18" },
   "dependencies": {
-    "@netlify/functions": "^2.5.0",
-    "minimatch": "^9.0.3"
+    "@netlify/functions": "^2.5.0",
+    "minimatch": "^9.0.3",
+    "@aws-sdk/client-s3": "^3.645.0",
+    "node-fetch": "^3.3.2"
   }
 }
*** End Patch
```

### Patch 5: Netlify Configuration (`netlify.toml`)

```diff
*** Begin Patch
*** Update File: netlify.toml
@@
 [build]
   command = "npm ci"
   publish = "."
   functions = "netlify/functions"
 
 [[redirects]]
   from = "/mcp"
   to = "/.netlify/functions/mcp"
   status = 200
   force = true
 
 [[redirects]]
   from = "/mcp/*"
   to = "/.netlify/functions/mcp"
   status = 200
   force = true
 
+[[headers]]
+  for = "/.netlify/functions/*"
+  [headers.values]
+    Access-Control-Allow-Origin = "*"
+    Access-Control-Allow-Headers = "Content-Type, Authorization, mcp-protocol-version, mcp-session-id"
+    Access-Control-Allow-Methods = "GET, POST, OPTIONS"
*** End Patch
```

---

## 2) Environment Variables (Netlify → Site settings → Environment)

**Required**

```
ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
MCP_HTTP_REQUIRE_ORIGIN=true
WORKSPACE_DIR=/opt/build/repo

# Validation assist (flip true only while adding connector)
VALIDATION_MODE=false

# Timeouts/retries
HARD_TIMEOUT_MS=8000
SOFT_RETRY=1
METRICS_SAMPLE=1

# Policy
POLICY_ALLOW_GLOBS=**/*
POLICY_DENY_GLOBS=.env,**/.git/**,**/.ssh/**,**/*.key,**/*.pem,**/*.p12,**/*.pfx,**/*.kdbx
POLICY_MAX_FILES=20
POLICY_MAX_BYTES=524288

# S3 audit (optional but recommended)
AWS_REGION=us-east-1
AUDIT_S3_BUCKET=your-bucket-name
AUDIT_S3_PREFIX=mcp/audit
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# GitHub (PR-only writes)
GITHUB_REPOSITORY=owner/repo
GITHUB_BASE_BRANCH=main
GITHUB_PR_PREFIX=mcp/changes
GITHUB_TOKEN=ghs_...  # Prefer GitHub App installation token
```

---

## 3) Quick Test Commands

### Health / manifest

```bash
curl -sS -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp/health'
curl -sS -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp'
```

### tools/list

```bash
curl -sS -i -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'
```

### get_diagnostics

```bash
curl -sS -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_diagnostics","arguments":{}}}' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp' | jq
```

### read_file

```bash
curl -sS -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"read_file","arguments":{"path":"README.md"}}}' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp' | jq
```

### write_file (preview in VALIDATION_MODE=true)

```bash
curl -sS -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"write_file","arguments":{"title":"Demo change","summary":"Test","files":[{"path":"docs/demo.txt","content":"hello"}]}}}' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp' | jq
```

> When `VALIDATION_MODE=false`, this will open a PR and return `{ prNumber, prUrl, branch }`.

---

## 4) Connector Steps (ChatGPT → Settings → Connectors)

* **Server URL**: `https://zingy-profiterole-f31cb8.netlify.app/mcp`
* **Authentication**: None
* For first add, you can set `VALIDATION_MODE=true` in Netlify envs, deploy, add the connector, then set back to `false` and redeploy.

---

## 5) Simulated Runs (what you'll see in S3 + responses)

### A) Connector add / tools.list

* Response: JSON with tools array.
* S3 objects:
  * `mcp/audit/YYYY-MM-DD/tool_list_files/...json` (pattern echo)
  * `mcp/audit/YYYY-MM-DD/error/...json` only if something fails

### B) read_file "README.md"

* Response: `{ path, content, secretMatches: [] }`
* S3: `tool_read_file/...json` containing `{ path, bytes }`

### C) write_file (VALIDATION_MODE=true)

* Response: `{ preview: true, note: "Validation mode...", plan: [...] }`
* S3: `tool_write_preview/...json`

### D) write_file (VALIDATION_MODE=false)

* Response: `{ prNumber, prUrl, branch }`
* S3:
  * `tool_write_preview/...json`
  * `tool_write_pr/...json` with `{ prNumber, prUrl }`

### E) Policy denial (secret found / deny glob)

* Response: `{ error: "Secret-like content detected in foo.txt" }` **or** `{ error: "Path 'x' matches deny rule 'y'" }`
* S3: `error/...json` explaining the rejection

### F) Timeout/circuit behavior

* If GitHub hiccups, you'll get `{ error: "PR flow failed" }`; error recorded in `error/...json`. The light retry (`SOFT_RETRY=1`) runs once.

---

## 6) Why this fixes the 500s & 403s

* **No more raw 500s**: all unexpected errors are returned as JSON-RPC `error` objects with `200 OK`, so ChatGPT completes validation instead of failing hard.
* **Validation mode**: lets you add the connector even if PR credentials aren't ready yet.
* **Origin handling**: wildcard matches for `chatgpt.com` & `openai.com` variants; still enforced when not in validation mode.
* **S3 audits**: you can prove what happened on each call and debug fast.

---

## 7) If you hit anything weird

* Netlify → **Functions → mcp → Logs** (you'll see stack traces + our `[audit]`/`[MCP]` prints)
* Flip `VALIDATION_MODE=true`, redeploy, add connector, then flip back
* Ensure `GITHUB_TOKEN` is an **installation token** with `contents:write` and `pull_requests:write` on `GITHUB_REPOSITORY`

---

## Next Steps

Want me to generate a single **git patch file** you can apply with `git am`? Or a PR branch you can paste into Cursor to commit in one shot?

