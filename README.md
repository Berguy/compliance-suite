# Compliance Suite

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-black)

**Plataforma web local para auditoria de conformidade LGPD e ISO 27001 em código-fonte.**

O Compliance Suite orquestra três módulos em um pipeline único: escaneia o código em busca de dados sensíveis, classifica os achados por severidade, mapeia cada um ao artigo da LGPD e ao controle da ISO 27001 correspondentes, e entrega o resultado em um dashboard com histórico e relatório em PDF.

---

## Por que este projeto existe

Auditoria de conformidade costuma ser um processo manual, caro e repetitivo: alguém abre o código, procura dados sensíveis a olho, anota o que encontrou numa planilha e tenta lembrar qual artigo da LGPD se aplica a cada achado.

Esse processo tem três falhas previsíveis. É lento. Não é reproduzível — duas pessoas auditando o mesmo código chegam a resultados diferentes. E não deixa rastro: quando o auditor sai, o histórico vai com ele.

O Compliance Suite trata auditoria como pipeline, não como tarefa artesanal. O resultado é rastreável, repetível e documentado — cada achado tem arquivo, linha, severidade, base legal e recomendação de correção.

## Arquitetura

O sistema integra três componentes:

```text
Usuário (navegador)
       │
       ▼
Flask (app.py) ──► pii-guard (scan) ──► findings.json
       │                                    │
       │                                    ▼
       │                          compliance-audit (engine)
       │                                    │
       ▼                                    ▼
Dashboard / PDF ◄─────────────────── relatorio.pdf
```

**1. pii-guard** — escaneia o código-fonte em busca de secrets, credenciais e dados pessoais. Detecta 8 tipos de secret (AWS, GitHub, Google, JWT, chaves privadas, strings de conexão, senhas) e 8 tipos de PII (CPF, CNPJ, RG, e-mail, telefone, CEP, cartão de crédito, nomes).

**2. compliance-audit** — processa os achados brutos, classifica por severidade e mapeia cada um ao artigo da LGPD e ao controle da ISO 27001 aplicáveis.

**3. Compliance Suite (Flask)** — interface web com dashboard, cadastro de clientes, histórico de auditorias e geração de relatórios em PDF.

## O que já funciona

### Gestão de clientes
- Cadastro de clientes com dados de identificação
- Persistência local em JSON
- Vinculação de auditorias a cada cliente

### Execução de auditorias
- Seleção do caminho do projeto a ser auditado
- Execução do scan via pii-guard integrado
- Armazenamento dos findings em JSON estruturado
- Processamento pelo motor de conformidade

### Dashboard e relatórios
- Painel com visão consolidada das auditorias
- Histórico completo por cliente
- Geração de relatório em PDF com ReportLab
- Abertura direta do relatório pelo navegador

### Configuração
- Auditor padrão e escopo configuráveis em `data/settings.json`
- Ícone personalizado para atalho no Windows

## Tecnologias

| Componente | Tecnologia |
|---|---|
| Backend | Python + Flask |
| Frontend | HTML5, CSS3 e JavaScript (vanilla) |
| Templates | Jinja2 |
| Scanner de segurança | pii-guard (regex e entropia) |
| Motor de conformidade | compliance-audit (mapeamento LGPD/ISO) |
| Geração de relatórios | ReportLab |
| Armazenamento | JSON local |
| Processamento de imagem | Pillow |

## Requisitos

- Python 3.10 ou superior
- Windows 10/11 (recomendado) ou Linux/macOS com ajustes no script de inicialização

## Instalação

O projeto depende de dois repositórios complementares. Clone os três lado a lado:

```bash
# 1. Clonar os repositórios
git clone https://github.com/Berguy/compliance-suite.git
git clone https://github.com/Berguy/pii-guard.git

cd compliance-suite

# 2. Criar e ativar o ambiente virtual
python -m venv .venv

# Windows (Git Bash)
source .venv/Scripts/activate
# Linux / macOS
# source .venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt
```

Se preferir instalar manualmente:

```bash
pip install flask pillow reportlab
pip install -e ../pii-guard
```

> **Nota:** o módulo `compliance-audit` é o motor de mapeamento normativo. Enquanto ele não estiver publicado como repositório público, a etapa de classificação por severidade e mapeamento LGPD/ISO precisa ser executada a partir do ambiente local do autor.

## Uso

### Inicialização rápida (Windows)

Dê duplo clique em `run.bat` na pasta do projeto. O navegador abre automaticamente em `http://127.0.0.1:5000`.

### Inicialização manual

```bash
source .venv/Scripts/activate
python app.py
```

Acesse `http://127.0.0.1:5000` no navegador.

### Fluxo de auditoria

1. **Cadastrar cliente** — menu Clientes → Novo Cliente
2. **Executar auditoria** — menu Nova Auditoria → informar o caminho do projeto → Executar
3. **Visualizar relatório** — botão "Abrir Relatório PDF" ou menu Auditorias

## Estrutura do projeto

```text
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
```

## Configuração

O auditor padrão e o escopo podem ser alterados em `data/settings.json`:

```json
{
  "auditor": "Berguy Silva",
  "escopo_padrao": "Código-fonte"
}
```

## Roadmap

| Etapa | Escopo | Status |
|---|---|---|
| Interface web com dashboard | Flask, Jinja2, histórico | Concluída |
| Integração com pii-guard | Execução do scan e captura de findings | Concluída |
| Geração de relatório PDF | ReportLab | Concluída |
| Gestão de clientes | Cadastro e vínculo com auditorias | Concluída |
| Publicação do compliance-audit | Motor de mapeamento como repositório público | Planejada |
| Suíte de testes automatizados | pytest e integração contínua | Planejada |
| Exportação em CSV e JSON | Formatos alternativos de relatório | Planejada |
| Autenticação de usuários | Controle de acesso ao painel | Planejada |

## Contribuindo

Contribuições são bem-vindas. Para mudanças relevantes, abra uma issue descrevendo o problema ou a proposta antes de enviar um pull request.

```bash
git checkout -b feature/nome-da-feature
git commit -m "feat: descrição da mudança"
```

## Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para os termos completos.

## Autor

**Berguy Silva** — Engenheiro de software, pós-graduado em Computação Forense e Perícia Digital e em Gestão de Projetos.

- LinkedIn: https://www.linkedin.com/in/BerguySilva
- GitHub: https://github.com/Berguy
- Email: contato@berguysilva.com.br

**Versão:** 1.0 · **Data:** agosto de 2026
