# Command Watcher Feature

## Overview

The Command Watcher provides **real-time monitoring** of command execution, helping debug hanging commands and providing visibility into what's happening during execution.

## Features

### Real-Time Status Updates

The watcher logs command execution stages to `stderr` (visible in terminal):

- **▶️ START**: Command begins execution
- **🔄 MODIFIED**: Command was modified (e.g., `--no-pager` added)
- **🔄 SPAWNING**: Subprocess is being created
- **🔄 EXECUTING**: Command is running (shows PID)
- **🔄 COMPLETED**: Command finished successfully
- **✅ END**: Command completed successfully
- **❌ END**: Command failed or timed out

### Example Output

```
[14:23:45] [INFO] [WATCHER] ▶️  START: git status...
[14:23:45] [INFO] [WATCHER] 🔄 MODIFIED: Added --no-pager flag
[14:23:45] [INFO] [WATCHER] 🔄 SPAWNING: Creating subprocess...
[14:23:45] [INFO] [WATCHER] 🔄 EXECUTING: PID: 12345
[14:23:46] [INFO] [WATCHER] 🔄 COMPLETED: Finished in 150ms
[14:23:46] [INFO] [WATCHER] ✅ END: git status... (rc=0, 150ms, 1024 bytes)
```

## Configuration

### Enable/Disable Watcher

```bash
# Enable (default)
export MCP_ENABLE_WATCHER=true

# Disable
export MCP_ENABLE_WATCHER=false
```

### View Watcher Status

Check watcher status via `get_diagnostics`:

```json
{
  "watcher": {
    "enabled": true,
    "active_commands": 0,
    "recent_commands": [
      {
        "command": "git status",
        "success": true,
        "returncode": 0,
        "elapsed_ms": 150,
        "timestamp": 1234567890.123
      }
    ]
  }
}
```

## How It Helps Debug Hanging Commands

### Problem: Commands Hang Waiting for Input

Common causes:
1. **Git pager** waiting for user input
2. **Credential prompts** waiting for password
3. **Terminal selection mode** (Windows) pausing execution
4. **Editor prompts** waiting for commit message

### Solution: Automatic Fixes

The watcher automatically applies fixes:

1. **Disables Git Pager**: Sets `GIT_PAGER=cat`
2. **Disables System Pager**: Sets `PAGER=cat`
3. **Disables Prompts**: Sets `GIT_TERMINAL_PROMPT=0`
4. **Disables Credential Prompts**: Sets `GIT_ASKPASS=""`
5. **Disables Git Credential Manager**: Sets `GCM_INTERACTIVE=never`
6. **Adds --no-pager Flag**: Automatically adds to git commands
7. **Prevents Input**: Uses `stdin=DEVNULL`

### Status Tracking

The watcher tracks:
- **Command start time**
- **Current status** (running, spawning, executing, etc.)
- **Process ID** (PID)
- **Execution time**
- **Output size**
- **Return code**

## Usage

### Automatic

The watcher is **automatically enabled** and monitors all `run_command` executions.

### Manual Check

```python
# Check watcher status
diagnostics = await get_diagnostics()
print(diagnostics["watcher"])
```

### Disable for Quiet Mode

```bash
export MCP_ENABLE_WATCHER=false
python cursor_mcp_server.py
```

## Troubleshooting

### Commands Still Hanging

1. **Check watcher logs**: Look for where it stops
   - If stops at "SPAWNING": Subprocess creation issue
   - If stops at "EXECUTING": Command is waiting for input
   - If stops at "COMPLETED": Output decoding issue

2. **Check environment variables**: Verify fixes are applied
   ```python
   # In run_command, env vars are set:
   # GIT_PAGER=cat
   # PAGER=cat
   # GIT_TERMINAL_PROMPT=0
   # GIT_ASKPASS=""
   # GCM_INTERACTIVE=never
   ```

3. **Check command modification**: Verify `--no-pager` is added
   ```
   [WATCHER] 🔄 MODIFIED: Added --no-pager flag
   ```

4. **Check timeout**: Commands timeout after 60s by default
   ```
   [WATCHER] 🔄 TIMEOUT: Exceeded 60s timeout
   ```

### Watcher Not Showing Output

1. **Check if enabled**: `MCP_ENABLE_WATCHER=true`
2. **Check stderr**: Output goes to `stderr`, not `stdout`
3. **Check terminal**: Some terminals buffer stderr output

## Technical Details

### Implementation

- **Logging**: Uses Python `logging` module to `stderr`
- **Flush**: Forces `sys.stderr.flush()` after each log
- **Tracking**: Maintains active commands dict and history deque
- **Non-blocking**: Watcher doesn't slow down command execution

### Performance

- **Minimal Overhead**: ~1ms per command for logging
- **Memory Efficient**: History limited to last 50 commands
- **Thread-Safe**: Uses async/await for concurrent commands

## Future Enhancements

Potential improvements:
- **Progress bars** for long-running commands
- **Streaming output** capture and display
- **Command cancellation** via watcher
- **Performance metrics** per command type
- **Alert system** for hanging commands

