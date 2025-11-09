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
- `reset_context` - Reset context tracker (after large operations)

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

## 📊 Context Summarization

**Auto-summarization at 85% context usage**

The server automatically summarizes content when context usage reaches 85% of the maximum:

- **Automatic**: Triggers at 85% threshold (configurable)
- **Smart summarization**: Keeps important sections (headers, definitions, key patterns)
- **Transparent**: Adds metadata headers showing original vs. summarized size
- **Per-tool**: Works across `read_file`, `list_files`, `search_code`, and resources

### How it works

1. Tracks character count across all operations
2. When usage reaches 85% of `MCP_CONTEXT_MAX_CHARS`, automatically summarizes
3. Summarization strategy:
   - **Text files**: Keeps first 20%, last 20%, summarizes middle 60% (keeps key patterns)
   - **File lists**: Groups by extension, shows counts and top files
   - **Search results**: Keeps top 5 files, summarizes others

### Configuration

```bash
# Set max context size (default: 100,000 chars)
export MCP_CONTEXT_MAX_CHARS=150000

# Set threshold (default: 0.85 = 85%)
export MCP_CONTEXT_SUMMARY_THRESHOLD=0.90

# Disable summarization
export MCP_CONTEXT_SUMMARY_ENABLED=false
```

### Monitoring

Check context usage via `get_diagnostics`:
```json
{
  "context": {
    "max_chars": 100000,
    "current_chars": 85000,
    "usage_pct": 85.0,
    "summary_threshold": 0.85,
    "summarization_enabled": true,
    "recent_summaries": [...]
  }
}
```

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
- `MCP_MAX_FILE_BYTES` - Max file size (default: 2MB)
- `MCP_CONTEXT_MAX_CHARS` - Max context size before summarization (default: 100,000 chars)
- `MCP_CONTEXT_SUMMARY_THRESHOLD` - Threshold for auto-summarization (default: 0.85 = 85%)
- `MCP_CONTEXT_SUMMARY_ENABLED` - Enable/disable auto-summarization (default: `true`)

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

