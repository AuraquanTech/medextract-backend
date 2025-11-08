@echo off
setlocal enabledelayedexpansion

if "%~1"=="" (
  echo Usage: start_cursor_mcp.bat C:\path\to\workspace
  exit /b 1
)

set WORKSPACE_DIR=%~1

if "%MCP_AUDIT_LOG%"=="" set MCP_AUDIT_LOG=%WORKSPACE_DIR%\.mcp_audit.log

python -u cursor_mcp_server.py

