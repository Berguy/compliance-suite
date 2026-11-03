"""Configuração compartilhada dos testes do Compliance Suite."""
 
import json
import sys
import types
from pathlib import Path
 
import pytest
 
 
@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    """Importa o app.py com diretórios isolados e módulos externos simulados."""
 
    # --- Simula compliance_audit.engine e .generators.pdf_generator ---
    pkg_mod = types.ModuleType("compliance_audit")
    engine_mod = types.ModuleType("compliance_audit.engine")
    gen_pkg_mod = types.ModuleType("compliance_audit.generators")
    pdf_mod = types.ModuleType("compliance_audit.generators.pdf_generator")
 
    class FakeReport:
        total_findings = 3
        critical_count = 1
        high_count = 1
        medium_count = 1
        low_count = 0
 
    def fake_generate_audit_report(findings_path, client_name, audit_scope, auditor):
        return FakeReport()
 
    def fake_generate_pdf(report, pdf_path):
        Path(pdf_path).write_bytes(b"%PDF-1.4 fake")
 
    engine_mod.generate_audit_report = fake_generate_audit_report
    pdf_mod.generate_pdf = fake_generate_pdf
 
    monkeypatch.setitem(sys.modules, "compliance_audit", pkg_mod)
    monkeypatch.setitem(sys.modules, "compliance_audit.engine", engine_mod)
    monkeypatch.setitem(sys.modules, "compliance_audit.generators", gen_pkg_mod)
    monkeypatch.setitem(sys.modules, "compliance_audit.generators.pdf_generator", pdf_mod)
 
    # --- Simula pii_guard.cli.main (usado dentro de _run_pii_guard) ---
    pii_pkg = types.ModuleType("pii_guard")
    pii_cli = types.ModuleType("pii_guard.cli")
 
    def fake_pii_main():
        args = sys.argv
        if "--output" in args:
            out = args[args.index("--output") + 1]
            Path(out).write_text(
                json.dumps({"findings": [], "files_scanned": 1}), encoding="utf-8"
            )
 
    pii_cli.main = fake_pii_main
    monkeypatch.setitem(sys.modules, "pii_guard", pii_pkg)
    monkeypatch.setitem(sys.modules, "pii_guard.cli", pii_cli)
 
    # --- Importa o app.py apontando os diretórios para tmp_path ---
    raiz = Path(__file__).resolve().parent.parent
    monkeypatch.syspath_prepend(str(raiz))
 
    if "app" in sys.modules:
        del sys.modules["app"]
 
    import app as app_mod
 
    data_dir = tmp_path / "data"
    out_dir = tmp_path / "output"
    findings_dir = out_dir / "findings"
    relatorios_dir = out_dir / "relatorios"
    for d in (data_dir, findings_dir, relatorios_dir):
        d.mkdir(parents=True, exist_ok=True)
 
    app_mod.DATA_DIR = data_dir
    app_mod.OUTPUT_DIR = out_dir
    app_mod.FINDINGS_DIR = findings_dir
    app_mod.RELATORIOS_DIR = relatorios_dir
    app_mod.CLIENTES_FILE = data_dir / "clientes.json"
    app_mod.AUDITORIAS_FILE = data_dir / "auditorias.json"
    app_mod.SETTINGS_FILE = data_dir / "settings.json"
    app_mod.app.config.update(TESTING=True, SECRET_KEY="teste")
 
    return app_mod
 
 
@pytest.fixture()
def client(app_module):
    """Cliente Flask para requisições nos testes."""
    return app_module.app.test_client()
