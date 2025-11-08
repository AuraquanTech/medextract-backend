import pytest
import cursor_mcp_server as srv

@pytest.fixture(autouse=True)
def _tmp_workspace(tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "README.md").write_text("Hello Workspace", encoding="utf-8")
    (ws / "src").mkdir()
    (ws / "src" / "a.py").write_text("print('A')\n# TODO: refactor", encoding="utf-8")
    (ws / "src" / "b.txt").write_text("B", encoding="utf-8")
    (ws / ".env").write_text("SECRET=1", encoding="utf-8")
    monkeypatch.setenv("WORKSPACE_DIR", str(ws))
    srv.WORKSPACE_DIR = ws.resolve()
    return ws

@pytest.mark.asyncio
async def test_list_and_read_basic():
    files = await srv.list_files(".", "src/**/*.py")
    assert any(p.endswith("src/a.py") for p in files)
    
    txt = await srv.read_file("README.md")
    assert "Hello Workspace" in txt

@pytest.mark.asyncio
async def test_read_denylist_blocked():
    with pytest.raises(PermissionError):
        await srv.read_file(".env")

@pytest.mark.asyncio
async def test_write_preview_and_apply():
    preview = await srv.write_file("notes.txt", "x", require_confirmation=True)
    assert "WRITE_PREVIEW" in preview
    
    ok = await srv.write_file("notes.txt", "hello", require_confirmation=False, mode="create")
    assert ok == "OK"
    assert (srv.WORKSPACE_DIR / "notes.txt").read_text(encoding="utf-8") == "hello"

@pytest.mark.asyncio
async def test_run_command_whitelist():
    res = await srv.run_command("git status")
    assert "returncode" in res

@pytest.mark.asyncio
async def test_search_code_regex():
    hits = await srv.search_code(r"TODO", file_glob="**/*.py")
    assert any(h["file"].endswith("a.py") for h in hits)

