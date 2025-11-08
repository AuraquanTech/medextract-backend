# Cursor MCP Server

**Full-featured MCP server connecting Cursor AI and ChatGPT Developer Mode**

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Windows
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Workspace

Edit `mcp_config.json` and set your `WORKSPACE_DIR`:

```json
{
  "mcpServers": {
    "cursor-mcp": {
      "command": "python",
      "args": ["-u", "cursor_mcp_server.py"],
      "env": {
        "WORKSPACE_DIR": "C:/path/to/your/workspace"
      }
    }
  }
}
```

### 3. Start Server

**Windows:**
```powershell
.\start_cursor_mcp.ps1 -WorkspaceDir "C:\path\to\workspace"
```

**macOS/Linux:**
```bash
export WORKSPACE_DIR=/path/to/workspace
./start_cursor_mcp.sh
```

### 4. Register in ChatGPT Developer Mode

1. Open ChatGPT → Settings → Developer Mode → MCP Servers
2. Add the configuration from `mcp_config.json`
3. Save and verify tools are discovered

## 📋 Features

### Tools
- `read_file` - Read files from workspace
- `list_files` - List files with glob patterns
- `write_file` - Write files (with preview mode)
- `run_command` - Execute whitelisted commands
- `get_diagnostics` - Health and security diagnostics
- `search_code` - Regex search across codebase

### Resources
- `workspace_tree` - Full file tree
- `workspace_summary` - Workspace overview
- `readme` - README.md content

### Prompts
- `code_review` - Code review assistant
- `debug_assistant` - Debugging helper
- `refactor_suggestion` - Refactoring suggestions

## 🔒 Security

- Workspace sandboxing (no path traversal)
- Rate limiting (100 reads/hr, 50 writes/hr, 20 commands/hr)
- Command whitelist (git, npm, pytest, etc.)
- File denylist (.env, .git, node_modules, etc.)
- Audit logging (all operations logged)

## 🧪 Testing

```bash
# Set workspace for tests
$env:WORKSPACE_DIR = "C:\path\to\test\workspace"

# Run tests
pytest tests/
```

## 📚 Documentation

- `SETUP.md` - Detailed setup instructions
- `SECURITY.md` - Security design and hardening
- `BEST_PRACTICES.md` - Usage best practices
- `PERF.md` - Performance optimization guide

## 🔧 Configuration

### Environment Variables

- `WORKSPACE_DIR` - Workspace root directory (required)
- `MCP_AUDIT_LOG` - Audit log path (default: `.mcp_audit.log`)
- `MCP_MAX_FILE_BYTES` - Max file size (default: 1MB)

### Rate Limits

- Reads: 100 per hour
- Writes: 50 per hour
- Commands: 20 per hour

### Allowed Commands

- `git status`, `git diff`
- `npm test`, `pnpm test`, `yarn test`
- `pytest`, `python -m pytest`
- `node -v`

## 🐛 Troubleshooting

### Server won't start
- Check Python version (3.10+)
- Verify dependencies: `pip install -r requirements.txt`
- Check `WORKSPACE_DIR` is set correctly

### Tools not appearing in ChatGPT
- Verify MCP config in ChatGPT settings
- Check server is running (stdio mode)
- Review audit log for errors

### Permission errors
- Verify workspace path is correct
- Check file isn't in denylist (.env, .git, etc.)
- Ensure workspace directory exists

## 📝 License

See LICENSE file for details.

