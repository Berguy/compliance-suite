cat > README.md << 'READMEEOF'

# Compliance Suite

Sistema web local para auditoria de conformidade **LGPD / ISO 27000** em código-fonte.

## Visão Geral

O Compliance Suite integra três módulos em um pipeline automatizado:

1. **pii-guard** — Escaneia código-fonte em busca de dados sensíveis (secrets, credenciais, PII)
2. **compliance-audit** — Processa os achados, classifica por severidade e mapeia para LGPD/ISO 27001
3. **Compliance Suite (Flask)** — Interface web com dashboard, histórico de auditorias e relatórios em PDF

## Arquitetura

Usuário (navegador)
│
▼
Flask (app.py) ──► pii-guard (scan) ──► findings.json
│ │
│ ▼
│ compliance-audit (engine)
│ │
▼ ▼
Dashboard / PDF ◄───────────────── relatorio.pdf

## Requisitos

- Python 3.10+
- Windows 10/11 (ou Linux/Mac com ajustes no run.sh)
- Pacotes: pii-guard, compliance-audit, Flask, Pillow

## Instalação

```bash
# 1. Clonar os três repositórios lado a lado
git clone https://github.com/Berguy/compliance-suite.git
git clone https://github.com/Berguy/pii-guard.git
cd compliance-suite

# 2. Criar e ativar ambiente virtual
python -m venv .venv
source .venv/Scripts/activate    # Windows (Git Bash)
# source .venv/bin/activate      # Linux / macOS

# 3. Instalar dependências
pip install flask pillow reportlab
pip install -e ../pii-guard

Inicialização rápida (Windows)

Duplo clique em run.bat na pasta do projeto.

source .venv/Scripts/activate
python app.py

O navegador abre automaticamente em http://127.0.0.1:5000.

Fluxo de auditoria

Cadastrar cliente — Menu Clientes → Novo Cliente
Executar auditoria — Menu Nova Auditoria → informar caminho do projeto → Executar
Visualizar relatório — Botão "Abrir Relatório PDF" ou menu Auditorias

Estrutura do Projeto

compliance-suite/
├── app.py                  # Aplicação Flask principal
├── run.bat                 # Inicialização rápida (Windows)
├── requirements.txt        # Dependências Python
├── .gitignore
├── README.md
├── icone.ico               # Ícone do atalho
├── data/                   # Dados persistidos (JSON)
│   ├── clientes.json
│   ├── auditorias.json
│   └── settings.json
├── output/
│   ├── findings/           # Saídas do pii-guard (JSON)
│   └── relatorios/         # Relatórios PDF gerados
└── templates/              # Templates HTML (Jinja2)
    ├── base.html
    ├── index.html
    ├── nova_auditoria.html
    ├── auditorias.html
    └── clientes.html

    TECNOLOGIAS

      Componente                     Tecnologia
    AplicadaBackend            Python + Flask Framework
    Frontend                   HTML5 / CSS3 / JavaScript (Vanilla)
    Scanner de Segurança       pii-guard (Análise baseada em Regex e Entropia)
    Motor de Conformidade      compliance-audit (Lógica de mapeamento LGPD/ISO)
    Geração de Relatórios      ReportLab (Engine de PDF)
    Armazenamento              JSON Local (NoSQL Style)
    Processamento de Imagem    Pillow (Conversão de ativos visuais)

    Configuração
    O auditor padrão e o escopo podem ser alterados em data/settings.json:

    {
  "auditor": "Berguy Silva",
  "escopo_padrao": "Código-fonte"
}

LicençaUso interno.
Desenvolvido por Berguy Silva.

Versão: 1.0
Data: Agosto 2026
READMEEOF

```
