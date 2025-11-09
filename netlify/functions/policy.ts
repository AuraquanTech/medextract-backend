// Lightweight policy engine: allow/deny globs, basic secret scanning, max PR size.
import minimatch from "minimatch";

export type PolicyConfig = {
  allowGlobs: string[];
  denyGlobs: string[];
  maxFilesChanged: number;       // hard cap on number of files per PR
  maxTotalBytes: number;         // hard cap on byte sum for write_file operations
  secretRegexes: RegExp[];       // patterns to block exfil/secrets
};

export type WritePlanItem = {
  path: string;
  contentBytes: number;
};

export function buildDefaultPolicy(): PolicyConfig {
  const defaultSecretPatterns = [
    /\bAKIA[0-9A-Z]{16}\b/i,                       // AWS Access Key
    /\bghp_[0-9A-Za-z]{36}\b/i,                    // GitHub classic token
    /-----BEGIN(\sRSA)?\sPRIVATE KEY-----/i,       // PEM private keys
    /\b(xox[baprs]-[0-9A-Za-z-]{10,})\b/i,         // Slack tokens
    /\bAIza[0-9A-Za-z\-_]{35}\b/i,                 // Google API keys
  ];
  return {
    allowGlobs: (process.env.POLICY_ALLOW_GLOBS || "**/*").split(",").map(s => s.trim()).filter(Boolean),
    denyGlobs: (process.env.POLICY_DENY_GLOBS || ".env,**/.git/**,**/.ssh/**,**/*.key,**/*.pem,**/*.p12,**/*.pfx,**/*.kdbx").split(",").map(s => s.trim()).filter(Boolean),
    maxFilesChanged: Number(process.env.POLICY_MAX_FILES || 20),
    maxTotalBytes: Number(process.env.POLICY_MAX_BYTES || 512 * 1024),
    secretRegexes: defaultSecretPatterns,
  };
}

export function pathAllowed(path: string, cfg: PolicyConfig): { ok: boolean; reason?: string } {
  for (const d of cfg.denyGlobs) {
    if (d && minimatch(path, d, { dot: true })) {
      return { ok: false, reason: `Path '${path}' matches deny rule '${d}'` };
    }
  }
  let allowed = false;
  for (const a of cfg.allowGlobs) {
    if (a && minimatch(path, a, { dot: true })) { allowed = true; break; }
  }
  }
  if (!allowed) return { ok: false, reason: `Path '${path}' does not match any allow rule` };
  return { ok: true };
}

export function scanForSecrets(text: string, cfg: PolicyConfig): { ok: boolean; matches?: string[] } {
  const hits: string[] = [];
  for (const re of cfg.secretRegexes) {
    if (re.test(text)) hits.push(re.source);
  }
  return { ok: hits.length === 0, matches: hits };
}

export function validateWritePlan(plan: WritePlanItem[], cfg: PolicyConfig): { ok: boolean; reason?: string } {
  if (plan.length > cfg.maxFilesChanged) {
    return { ok: false, reason: `Plan changes ${plan.length} files; cap is ${cfg.maxFilesChanged}` };
  }
  const total = plan.reduce((s, i) => s + (i.contentBytes || 0), 0);
  if (total > cfg.maxTotalBytes) {
    return { ok: false, reason: `Plan total size ${total} exceeds cap ${cfg.maxTotalBytes}` };
  }
  return { ok: true };
}

