# Security Design & Hardening

## Controls

- Workspace sandboxing by path resolution (no traversal)

- Rate limits: reads(100/hr), writes(50/hr), commands(20/hr)

- Audit logs: structured JSON per call

- Command whitelist: tight regex list

- Denylist: secrety globs to avoid accidental reads

- File-size guard: `MCP_MAX_FILE_BYTES` (default 1MB)

## Guidance

- Run under a non-privileged OS user

- Keep whitelist minimal (`git status`, tests, etc.)

- Forward audit log to SIEM

- Consider storing server code outside the workspace

## Future Hardening

- Token-bucket per-client identity

- Write quotas per minute/hour

- Write shadowing + atomic replace

- Secret detection on read/write

