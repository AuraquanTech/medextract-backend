from src.cli.auraquan_cli import AuraQuanFoldingEngine

def test_fold_and_verify_roundtrip(tmp_path):
    eng = AuraQuanFoldingEngine()
    att = [{"type":"hipaa_compliance", "status":"compliant"}]
    payload = eng.fold(att, 128)
    assert eng.verify(payload) is True
