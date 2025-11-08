import time
import pytest
import cursor_mcp_server as srv

@pytest.mark.asyncio
async def test_list_perf_budget(tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    ws.mkdir()
    for i in range(800):
        p = ws / f"f{i}.txt"
        p.write_text("x", encoding="utf-8")
    
    monkeypatch.setenv("WORKSPACE_DIR", str(ws))
    srv.WORKSPACE_DIR = ws.resolve()
    
    t0 = time.perf_counter()
    files = await srv.list_files(".", "**/*.txt", max_results=500)
    assert len(files) == 500
    assert (time.perf_counter() - t0) < 2.0

