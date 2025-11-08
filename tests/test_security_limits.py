import pytest
import cursor_mcp_server as srv

@pytest.mark.asyncio
async def test_rate_limits(monkeypatch):
    srv.rate_read.max_ops = 3
    for _ in range(3):
        try:
            await srv.list_files(".")
        except Exception:
            pass
    with pytest.raises(RuntimeError):
        await srv.list_files(".")

