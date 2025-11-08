# Performance Guidance

- Keep denylist broad to skip large/vendor dirs

- Use `list_files(..., max_results=N)` to cap traversal

- Prefer targeted globs like `src/**/*.ts`

- Set `MCP_MAX_FILE_BYTES` higher only if necessary

- Avoid long-running commands; keep test suites sharded/filtered

