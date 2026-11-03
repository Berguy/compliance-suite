"""Testes das rotas e da API do Compliance Suite."""
 
import json
 
 
# ---------------------------------------------------------------- páginas
 
def test_index_responde_200(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
 
 
def test_index_com_dados_existentes(client, app_module):
    app_module._save_json(
        app_module.CLIENTES_FILE,
        [{"id": "cl-1", "nome": "Empresa A"}],
    )
    app_module._save_json(
        app_module.AUDITORIAS_FILE,
        [{"id": "aud-1", "data": "2026-01-01", "criticos": 2, "altos": 1}],
    )
    resposta = client.get("/")
    assert resposta.status_code == 200
 
 
def test_nova_auditoria_responde_200(client):
    resposta = client.get("/nova-auditoria")
    assert resposta.status_code == 200
 
 
def test_auditorias_responde_200(client):
    resposta = client.get("/auditorias")
    assert resposta.status_code == 200
 
 
def test_clientes_responde_200(client):
    resposta = client.get("/clientes")
    assert resposta.status_code == 200
 
 
# ---------------------------------------------------------------- clientes
 
def test_criar_cliente_valido(client, app_module):
    resposta = client.post(
        "/clientes/novo",
        data={"nome": "Empresa Teste", "cnpj": "00.000.000/0000-00", "dpo": "Maria"},
        follow_redirects=True,
    )
    assert resposta.status_code == 200
 
    clientes = app_module._load_json(app_module.CLIENTES_FILE)
    assert len(clientes) == 1
    assert clientes[0]["nome"] == "Empresa Teste"
    assert clientes[0]["id"].startswith("cl-")
 
 
def test_criar_cliente_sem_nome_e_rejeitado(client, app_module):
    resposta = client.post(
        "/clientes/novo",
        data={"nome": "   "},
        follow_redirects=True,
    )
    assert resposta.status_code == 200
 
    clientes = app_module._load_json(app_module.CLIENTES_FILE)
    assert clientes == []
 
 
def test_excluir_cliente(client, app_module):
    app_module._save_json(
        app_module.CLIENTES_FILE,
        [{"id": "cl-abc", "nome": "Empresa X"}],
    )
    resposta = client.post("/clientes/cl-abc/excluir")
    assert resposta.status_code == 200
    assert resposta.get_json()["ok"] is True
 
    clientes = app_module._load_json(app_module.CLIENTES_FILE)
    assert clientes == []
 
 
# ---------------------------------------------------------------- auditoria
 
def test_executar_auditoria_sem_pasta_retorna_400(client):
    resposta = client.post("/api/executar-auditoria", json={"pasta": ""})
    assert resposta.status_code == 400
    assert resposta.get_json()["ok"] is False
 
 
def test_executar_auditoria_pasta_inexistente_retorna_400(client):
    resposta = client.post(
        "/api/executar-auditoria",
        json={"pasta": "/caminho/que/nao/existe", "cliente_nome": "Empresa"},
    )
    assert resposta.status_code == 400
    assert "não encontrado" in resposta.get_json()["erro"].lower()
 
 
def test_executar_auditoria_sem_cliente_retorna_400(client, tmp_path):
    resposta = client.post(
        "/api/executar-auditoria",
        json={"pasta": str(tmp_path), "cliente_nome": ""},
    )
    assert resposta.status_code == 400
 
 
def test_executar_auditoria_sem_auditor_retorna_400(client, tmp_path):
    resposta = client.post(
        "/api/executar-auditoria",
        json={"pasta": str(tmp_path), "cliente_nome": "Empresa", "auditor": ""},
    )
    assert resposta.status_code == 400
 
 
def test_executar_auditoria_completa(client, app_module, tmp_path):
    resposta = client.post(
        "/api/executar-auditoria",
        json={
            "pasta": str(tmp_path),
            "cliente_nome": "Empresa Teste",
            "auditor": "Berguy Silva",
            "escopo": "Código-fonte",
        },
    )
    assert resposta.status_code == 200
 
    corpo = resposta.get_json()
    assert corpo["ok"] is True
    assert corpo["audit_id"].startswith("aud-")
    assert corpo["total_findings"] == 3
    assert corpo["criticos"] == 1
    assert corpo["pdf_url"].startswith("/auditorias/")
 
    auditorias = app_module._load_json(app_module.AUDITORIAS_FILE)
    assert len(auditorias) == 1
    assert auditorias[0]["status"] == "concluida"
    assert auditorias[0]["cliente_nome"] == "Empresa Teste"
 
 
# ---------------------------------------------------------------- PDF
 
def test_baixar_pdf_inexistente_retorna_404(client):
    resposta = client.get("/auditorias/aud-nao-existe/pdf")
    assert resposta.status_code == 404
 
 
def test_baixar_pdf_existente(client, app_module, tmp_path):
    pdf = tmp_path / "relatorio.pdf"
    pdf.write_bytes(b"%PDF-1.4 teste")
 
    app_module._save_json(
        app_module.AUDITORIAS_FILE,
        [{"id": "aud-1", "pdf_path": str(pdf)}],
    )
    resposta = client.get("/auditorias/aud-1/pdf")
    assert resposta.status_code == 200
 
 
def test_excluir_auditoria(client, app_module, tmp_path):
    pdf = tmp_path / "relatorio.pdf"
    pdf.write_bytes(b"%PDF-1.4 teste")
 
    app_module._save_json(
        app_module.AUDITORIAS_FILE,
        [{"id": "aud-1", "pdf_path": str(pdf), "findings_path": ""}],
    )
    resposta = client.post("/auditorias/aud-1/excluir")
    assert resposta.status_code == 200
    assert resposta.get_json()["ok"] is True
 
    auditorias = app_module._load_json(app_module.AUDITORIAS_FILE)
    assert auditorias == []
    assert not pdf.exists()
 
 
# ---------------------------------------------------------------- configurações
 
def test_salvar_configuracoes(client, app_module):
    resposta = client.post(
        "/api/configuracoes",
        json={"auditor": "Novo Auditor", "escopo": "Infraestrutura"},
    )
    assert resposta.status_code == 200
    assert resposta.get_json()["ok"] is True
 
    settings = app_module._load_settings()
    assert settings["auditor"] == "Novo Auditor"
    assert settings["escopo_padrao"] == "Infraestrutura"
 
 
def test_settings_padrao_quando_arquivo_nao_existe(app_module):
    settings = app_module._load_settings()
    assert settings["auditor"] == "Berguy Silva"
    assert settings["escopo_padrao"] == "Código-fonte"
 
 
# ---------------------------------------------------------------- utilitários
 
def test_gerar_id_tem_prefixo(app_module):
    identificador = app_module._gerar_id("aud")
    assert identificador.startswith("aud-")
    assert len(identificador) == len("aud-") + 8
 
 
def test_load_json_arquivo_inexistente_retorna_lista(app_module, tmp_path):
    resultado = app_module._load_json(tmp_path / "nao_existe.json")
    assert resultado == []
 
 
def test_save_e_load_json_preserva_conteudo(app_module, tmp_path):
    caminho = tmp_path / "teste.json"
    dados = [{"id": "1", "nome": "Ação com acentuação"}]
    app_module._save_json(caminho, dados)
 
    with open(caminho, encoding="utf-8") as f:
        assert json.load(f) == dados
