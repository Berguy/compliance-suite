"""
Compliance Suite — Aplicativo web local para auditoria de conformidade LGPD/ISO 27000.
"""

import io
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from flask import (
    Flask, render_template, request, jsonify,
    send_file, redirect, url_for, flash,
)

from compliance_audit.engine import generate_audit_report
from compliance_audit.generators.pdf_generator import generate_pdf

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
FINDINGS_DIR = OUTPUT_DIR / "findings"
RELATORIOS_DIR = OUTPUT_DIR / "relatorios"

for d in [DATA_DIR, OUTPUT_DIR, FINDINGS_DIR, RELATORIOS_DIR]:
    d.mkdir(exist_ok=True, parents=True)

CLIENTES_FILE = DATA_DIR / "clientes.json"
AUDITORIAS_FILE = DATA_DIR / "auditorias.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

def _load_json(path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _load_settings():
    default = {"auditor": "Berguy Silva", "escopo_padrao": "Código-fonte"}
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            default.update(saved)
    return default

def _gerar_id(prefixo):
    return f"{prefixo}-{uuid.uuid4().hex[:8]}"

def _run_pii_guard(pasta, findings_path):
    """
    Executa o pii-guard diretamente via import Python.
    Retorna (sucesso: bool, erro: str).
    IMPORTANTE: verifica se o arquivo foi gerado ANTES de checar exit code.
    """
    original_argv = sys.argv.copy()
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    sys.stdout = stdout_buffer
    sys.stderr = stderr_buffer

    sys.argv = ["pii-guard", pasta, "--format", "json", "--output", findings_path]

    try:
        try:
            from pii_guard.cli import main
        except ImportError:
            from pii_guard.__main__ import main

        main()

        # VERIFICAR ARQUIVO PRIMEIRO — independente do exit code
        if os.path.exists(findings_path):
            return True, ""

        stdout_msg = stdout_buffer.getvalue()
        stderr_msg = stderr_buffer.getvalue()
        return False, f"pii-guard terminou mas não gerou arquivo. stdout: {stdout_msg} | stderr: {stderr_msg}"

    except SystemExit as e:
        # VERIFICAR ARQUIVO PRIMEIRO — mesmo com exit code != 0
        if os.path.exists(findings_path):
            return True, ""

        stdout_msg = stdout_buffer.getvalue()
        stderr_msg = stderr_buffer.getvalue()
        all_output = stdout_msg + stderr_msg
        return False, f"pii-guard falhou (código {e.code}): {all_output}"

    except Exception as e:
        # VERIFICAR ARQUIVO PRIMEIRO — mesmo com exceção
        if os.path.exists(findings_path):
            return True, ""

        stdout_msg = stdout_buffer.getvalue()
        stderr_msg = stderr_buffer.getvalue()
        return False, f"Erro ao executar pii-guard: {str(e)}\nstdout: {stdout_msg}\nstderr: {stderr_msg}"

    finally:
        sys.argv = original_argv
        sys.stdout = original_stdout
        sys.stderr = original_stderr

@app.route("/")
def index():
    clientes = _load_json(CLIENTES_FILE)
    auditorias = _load_json(AUDITORIAS_FILE)
    settings = _load_settings()
    total_criticos = sum(a.get("criticos", 0) for a in auditorias)
    total_altos = sum(a.get("altos", 0) for a in auditorias)
    recentes = sorted(auditorias, key=lambda x: x.get("data", ""), reverse=True)[:5]
    return render_template(
        "index.html", clientes=clientes, auditorias=auditorias,
        recentes=recentes, total_clientes=len(clientes),
        total_auditorias=len(auditorias), total_criticos=total_criticos,
        total_altos=total_altos, settings=settings,
    )

@app.route("/nova-auditoria")
def nova_auditoria():
    clientes = _load_json(CLIENTES_FILE)
    settings = _load_settings()
    return render_template("nova_auditoria.html", clientes=clientes, settings=settings)

@app.route("/api/executar-auditoria", methods=["POST"])
def executar_auditoria():
    data = request.json
    pasta = data.get("pasta", "").strip()
    cliente_id = data.get("cliente_id", "")
    cliente_nome = data.get("cliente_nome", "").strip()
    auditor = data.get("auditor", "").strip()
    escopo = data.get("escopo", "Código-fonte").strip()

    if not pasta:
        return jsonify({"ok": False, "erro": "Informe o caminho da pasta ou arquivo."}), 400
    if not os.path.exists(pasta):
        return jsonify({"ok": False, "erro": f"Caminho não encontrado: {pasta}"}), 400
    if not cliente_nome:
        return jsonify({"ok": False, "erro": "Selecione ou informe o nome do cliente."}), 400
    if not auditor:
        return jsonify({"ok": False, "erro": "Informe o nome do auditor."}), 400

    audit_id = _gerar_id("aud")
    findings_path = str(FINDINGS_DIR / f"{audit_id}_findings.json")
    pdf_path = str(RELATORIOS_DIR / f"{audit_id}_relatorio.pdf")

    try:
        # Passo 1: pii-guard
        sucesso, erro = _run_pii_guard(pasta, findings_path)
        if not sucesso:
            return jsonify({"ok": False, "erro": erro}), 500

        # Passo 2: compliance-audit
        report = generate_audit_report(
            findings_path=findings_path,
            client_name=cliente_nome,
            audit_scope=escopo,
            auditor=auditor,
        )
        generate_pdf(report, pdf_path)

        # Passo 3: registrar
        auditorias = _load_json(AUDITORIAS_FILE)
        auditorias.append({
            "id": audit_id,
            "cliente_id": cliente_id,
            "cliente_nome": cliente_nome,
            "pasta_auditada": pasta,
            "auditor": auditor,
            "escopo": escopo,
            "data": datetime.now().isoformat(),
            "total_findings": report.total_findings,
            "criticos": report.critical_count,
            "altos": report.high_count,
            "medios": report.medium_count,
            "baixos": report.low_count,
            "findings_path": findings_path,
            "pdf_path": pdf_path,
            "status": "concluida",
        })
        _save_json(AUDITORIAS_FILE, auditorias)

        return jsonify({
            "ok": True,
            "audit_id": audit_id,
            "total_findings": report.total_findings,
            "criticos": report.critical_count,
            "altos": report.high_count,
            "medios": report.medium_count,
            "baixos": report.low_count,
            "pdf_url": f"/auditorias/{audit_id}/pdf",
        })

    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

@app.route("/auditorias")
def auditorias():
    auditorias = _load_json(AUDITORIAS_FILE)
    auditorias_sorted = sorted(auditorias, key=lambda x: x.get("data", ""), reverse=True)
    return render_template("auditorias.html", auditorias=auditorias_sorted)

@app.route("/auditorias/<audit_id>/pdf")
def baixar_pdf(audit_id):
    auditorias = _load_json(AUDITORIAS_FILE)
    audit = next((a for a in auditorias if a["id"] == audit_id), None)
    if not audit:
        return "Auditoria não encontrada", 404
    pdf_path = audit["pdf_path"]
    if not os.path.exists(pdf_path):
        return "PDF não encontrado", 404
    return send_file(pdf_path, as_attachment=False, download_name=f"relatorio_{audit_id}.pdf")

@app.route("/auditorias/<audit_id>/excluir", methods=["POST"])
def excluir_auditoria(audit_id):
    auditorias = _load_json(AUDITORIAS_FILE)
    audit = next((a for a in auditorias if a["id"] == audit_id), None)
    if not audit:
        return jsonify({"ok": False, "erro": "Auditoria não encontrada"}), 404
    for path_key in ["findings_path", "pdf_path"]:
        path = audit.get(path_key, "")
        if path and os.path.exists(path):
            os.remove(path)
    auditorias = [a for a in auditorias if a["id"] != audit_id]
    _save_json(AUDITORIAS_FILE, auditorias)
    return jsonify({"ok": True})

@app.route("/clientes")
def clientes():
    clientes = _load_json(CLIENTES_FILE)
    return render_template("clientes.html", clientes=clientes)

@app.route("/clientes/novo", methods=["POST"])
def novo_cliente():
    clientes = _load_json(CLIENTES_FILE)
    cliente = {
        "id": _gerar_id("cl"),
        "nome": request.form.get("nome", "").strip(),
        "cnpj": request.form.get("cnpj", "").strip(),
        "dpo": request.form.get("dpo", "").strip(),
        "contato": request.form.get("contato", "").strip(),
        "criado_em": datetime.now().isoformat(),
    }
    if not cliente["nome"]:
        flash("Nome do cliente é obrigatório.", "erro")
        return redirect(url_for("clientes"))
    clientes.append(cliente)
    _save_json(CLIENTES_FILE, clientes)
    flash(f"Cliente '{cliente['nome']}' cadastrado.", "ok")
    return redirect(url_for("clientes"))

@app.route("/clientes/<cliente_id>/excluir", methods=["POST"])
def excluir_cliente(cliente_id):
    clientes = _load_json(CLIENTES_FILE)
    clientes = [c for c in clientes if c["id"] != cliente_id]
    _save_json(CLIENTES_FILE, clientes)
    return jsonify({"ok": True})

@app.route("/api/configuracoes", methods=["POST"])
def salvar_configuracoes():
    settings = _load_settings()
    settings["auditor"] = request.json.get("auditor", settings["auditor"])
    settings["escopo_padrao"] = request.json.get("escopo", settings["escopo_padrao"])
    _save_json(SETTINGS_FILE, settings)
    return jsonify({"ok": True})

if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
