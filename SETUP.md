# Setup (Windows + macOS/Linux) & Cursor AI integration

## 1) Install Python & create a virtual environment

### Windows (PowerShell)

1. Install Python 3.10+ from python.org and check "Add to PATH".

2. In your project root:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install mcp pytest
   ```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install mcp anthropic-mcp-sdk pytest
```

## 2) Choose a workspace directory

Use your Cursor project root (the folder visible in Cursor's Explorer). Note the absolute path.

## 3) Configure environment

* Windows (PowerShell):

  ```powershell
  $env:WORKSPACE_DIR = "C:/path/to/your/project"
  $env:MCP_AUDIT_LOG = "$env:WORKSPACE_DIR/.mcp_audit.log"
  ```

* macOS/Linux:

  ```bash
  export WORKSPACE_DIR=/absolute/path/to/project
  export MCP_AUDIT_LOG="$WORKSPACE_DIR/.mcp_audit.log"
  ```

## 4) Run the server

* Windows: `./start_cursor_mcp.ps1 -WorkspaceDir C:/path/to/your/project`

* macOS/Linux: `./start_cursor_mcp.sh`

## 5) Register in ChatGPT Developer Mode

1. ChatGPT → Settings → Developer Mode → MCP Servers.

2. Add the object from `mcp_config.json` (adjust WORKSPACE_DIR path).

3. Save; you should see tools/resources discovered.

## 6) Smoke test

* In a Dev Mode chat: invoke `list_files` (pattern `**/*.py`) and `read_file`.

* Check audit log at `$WORKSPACE_DIR/.mcp_audit.log`.

## Cursor AI tips

* Open the same workspace in Cursor.

* Use ChatGPT Dev Mode MCP tools to manipulate files; Cursor reflects changes instantly.

* For "apply buttons" UX, keep `write_file` in preview mode first; then re-run with `require_confirmation=false` to apply.

