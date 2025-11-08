#!/usr/bin/env python3
"""Local health checks for the Cursor MCP Server."""

import asyncio
import time
import cursor_mcp_server as srv

async def main():
    ws = srv.WORKSPACE_DIR
    assert ws.exists(), f"Workspace missing: {ws}"
    
    di = await srv.get_diagnostics()
    assert "workspace" in di and "limits" in di
    
    files = await srv.list_files(".", "**/*", 50)
    print(f"Found {len(files)} files")
    
    if any(f.endswith("README.md") for f in files):
        txt = await srv.read_file("README.md")
        assert isinstance(txt, str)
    
    _ = await srv.search_code("TODO|FIXME", max_results=5)
    
    t0 = time.perf_counter()
    _ = await srv.list_files(".", "**/*.py", 500)
    assert (time.perf_counter() - t0) < 2.0, "List exceeded 2s budget"
    
    print("Health OK")

if __name__ == "__main__":
    asyncio.run(main())

