"""
Compliance Suite — Aplicativo web local para auditoria de conformidade LGPD/ISO 27000.

Reutiliza os pacotes pii-guard e compliance-audit já desenvolvidos.
Executa localmente no Windows. Abre no navegador automaticamente.
"""

import json
import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from flask import (
    Flask, render_template, request, jsonify,
    send_file, redirect, url_for, flash,
)

# Importar compliance-audit diretamente (já instalado no venv)
from compliance_audit.engine import generate_audit_report
from compliance_audit.generators.pdf_generator import generate_pdf

app = Flask(__name__)
app.secret_key = "compliance-suite-2026"

# ===== DIRETÓRIOS =====
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
FINDINGS_DIR = OUTPUT_DIR / "findings"
RELATORIOS_DIR = OUTPUT_DIR / "relatorios"

for d in [DATA_DIR, OUTPUT_DIR, FINDINGS_DIR, RELATORIOS_DIR]:
    d.mkdir(exist_ok=True, parents=True)

# ===== ARQUIVOS DE DADOS =====
CLIENTES_FILE = DATA_DIR / "clientes.json"
AUDITORIAS_FILE = DATA_DIR / "auditorias.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

# ===== FUNÇÕES DE DADOS =====

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

# ===== ROTAS =====

@app.route("/")
def index():
    """Dashboard com estatísticas e auditorias recentes."""
    clientes = _load_json(CLIENTES_FILE)
    auditorias = _load_json(AUDITORIAS_FILE)
    settings = _load_settings()

    total_criticos = sum(a.get("criticos", 0) for a in auditorias)
    total_altos = sum(a.get("altos", 0) for a in auditorias)

    recentes = sorted(
        auditorias, key=lambda x: x.get("data", ""), reverse=True
    )[:5]

    return render_template(
        "index.html",
        clientes=clientes,
        auditorias=auditorias,
        recentes=recentes,
        total_clientes=len(clientes),
        total_auditorias=len(auditorias),
        total_criticos=total_criticos,
        total_altos=total_altos,
        settings=settings,
    )

@app.route("/nova-auditoria")
def nova_auditoria():
    """Formulário para nova auditoria."""
    clientes = _load_json(CLIENTES_FILE)
    settings = _load_settings()
    return render_template(
        "nova_auditoria.html", clientes=clientes, settings=settings
    )

@app.route("/api/executar-auditoria", methods=["POST"])
def executar_auditoria():
    """Executa o pipeline: pii-guard → compliance-audit → PDF."""
    data = request.json
    pasta = data.get("pasta", "").strip()
    cliente_id = data.get("cliente_id", "")
    cliente_nome = data.get("cliente_nome", "").strip()
    auditor = data.get("auditor", "").strip()
    escopo = data.get("escopo", "Código-fonte").strip()

    # Validações
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
        result = subprocess.run(
            ["pii-guard", pasta, "--format", "json", "--output", findings_path],
            capture_output=True, text=True, timeout=300,
        )

        if result.returncode != 0:
            return jsonify({
                "ok": False,
                "erro": f"pii-guard falhou: {result.stderr}"
            }), 500

        # Passo 2: compliance-audit
        report = generate_audit_report(
            findings_path=findings_path,
            client_name=cliente_nome,
            audit_scope=escopo,
            auditor=auditor,
        )

        # Passo 3: PDF
        generate_pdf(report, pdf_path)

        # Passo 4: registrar
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

    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "erro": "Tempo limite excedido (5 minutos)."}), 500
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

@app.route("/auditorias")
def auditorias():
    """Lista todas as auditorias realizadas."""
    auditorias = _load_json(AUDITORIAS_FILE)
    auditorias_sorted = sorted(
        auditorias, key=lambda x: x.get("data", ""), reverse=True
    )
    return render_template("auditorias.html", auditorias=auditorias_sorted)

@app.route("/auditorias/<audit_id>/pdf")
def baixar_pdf(audit_id):
    """Visualiza o PDF no navegador."""
    auditorias = _load_json(AUDITORIAS_FILE)
    audit = next((a for a in auditorias if a["id"] == audit_id), None)
    if not audit:
        return "Auditoria não encontrada", 404

    pdf_path = audit["pdf_path"]
    if not os.path.exists(pdf_path):
        return "PDF não encontrado", 404

    return send_file(
        pdf_path, as_attachment=False,
        download_name=f"relatorio_{audit_id}.pdf",
    )

@app.route("/auditorias/<audit_id>/excluir", methods=["POST"])
def excluir_auditoria(audit_id):
    """Exclui uma auditoria e seus arquivos."""
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
    """Lista todos os clientes."""
    clientes = _load_json(CLIENTES_FILE)
    return render_template("clientes.html", clientes=clientes)

@app.route("/clientes/novo", methods=["POST"])
def novo_cliente():
    """Cadastra um novo cliente."""
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
    """Exclui um cliente."""
    clientes = _load_json(CLIENTES_FILE)
    clientes = [c for c in clientes if c["id"] != cliente_id]
    _save_json(CLIENTES_FILE, clientes)
    return jsonify({"ok": True})

@app.route("/api/configuracoes", methods=["POST"])
def salvar_configuracoes():
    """Salva configurações do auditor."""
    settings = _load_settings()
    settings["auditor"] = request.json.get("auditor", settings["auditor"])
    settings["escopo_padrao"] = request.json.get("escopo", settings["escopo_padrao"])
    _save_json(SETTINGS_FILE, settings)
    return jsonify({"ok": True})

# ===== INICIALIZAÇÃO =====

if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True, port=5000)