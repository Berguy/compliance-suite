# Compliance Suite
 
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-black)
![CI](https://github.com/Berguy/compliance-suite/actions/workflows/ci.yml/badge.svg)
![Tests](https://img.shields.io/badge/tests-22%20passing-brightgreen)
 
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
 
**2. compliance-audit** — processa os achados brutos, calcula risco quantitativo em matriz 5×5 (ISO 27005), gera plano de remediação priorizado e mapeia cada achado ao artigo da LGPD e ao controle da ISO 27001 aplicáveis.
 
**3. Compliance Suite (Flask)** — interface web com dashboard, cadastro de clientes, histórico de auditorias e geração de relatórios em PDF.
 
## Ecossistema
 
O Compliance Suite é a camada de interface de um conjunto de três projetos que se complementam:
 
| Projeto | Função | Repositório |
|---|---|---|
| pii-guard | Scanner de secrets e PII | [github.com/Berguy/pii-guard](https://github.com/Berguy/pii-guard) |
| compliance-audit | Motor de mapeamento LGPD/ISO | [github.com/Berguy/compliance-audit](https://github.com/Berguy/compliance-audit) |
| compliance-suite | Interface web e relatórios | este repositório |
 
Cada um funciona de forma independente. Juntos, formam um pipeline completo de auditoria de conformidade.
 
## O que já funciona
 
### Gestão de clientes
- Cadastro de clientes com dados de identificação (nome, CNPJ, DPO, contato)
- Persistência local em JSON
- Vinculação de auditorias a cada cliente
- Exclusão de clientes com validação de nome obrigatório
 
### Execução de auditorias
- Seleção do caminho do projeto a ser auditado
- Execução do scan via pii-guard integrado
- Armazenamento dos findings em JSON estruturado
- Processamento pelo motor de conformidade
- Registro de contadores por severidade (crítico, alto, médio, baixo)
 
### Dashboard e relatórios
- Painel com visão consolidada das auditorias
- Histórico completo por cliente, ordenado por data
- Geração de relatório em PDF com ReportLab
- Abertura direta do relatório pelo navegador
- Exclusão de auditoria com remoção dos arquivos associados
 
### Configuração
- Auditor padrão e escopo configuráveis em `data/settings.json`
- Chave de sessão e modo debug controlados por variável de ambiente
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
| Testes | pytest |
| Lint | Ruff |
 
## Requisitos
 
- Python 3.10 ou superior
- Windows 10/11 (recomendado) ou Linux/macOS com ajustes no script de inicialização
 
## Instalação
 
O projeto depende de dois repositórios complementares. Clone os três lado a lado:
 
```bash
# 1. Clonar os repositórios
git clone https://github.com/Berguy/compliance-suite.git
git clone https://github.com/Berguy/pii-guard.git
git clone https://github.com/Berguy/compliance-audit.git
 
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
 
### Instalação via Git (sem clonar os módulos)
 
Se você só quer usar a ferramenta, sem modificar os módulos:
 
```bash
pip install flask pillow reportlab
pip install git+https://github.com/Berguy/pii-guard.git
pip install git+https://github.com/Berguy/compliance-audit.git
```
 
## Configuração
 
O auditor padrão e o escopo podem ser alterados em `data/settings.json`:
 
```json
{
  "auditor": "Berguy Silva",
  "escopo_padrao": "Código-fonte"
}
```
 
### Variáveis de ambiente
 
| Variável | Função | Padrão |
|---|---|---|
| `SECRET_KEY` | Chave de sessão do Flask, usada para assinar cookies | `dev-only` |
| `DEBUG` | `1` ativa o modo debug, `0` desativa | `1` |
 
A aplicação funciona sem configurar nada. Se as variáveis não existirem, os valores padrão são usados automaticamente — o que é adequado para uso local.
 
Para uso em rede ou produção, defina os dois valores antes de iniciar:
 
```bash
# Linux / macOS
export SECRET_KEY="sua-chave-aleatoria-aqui"
export DEBUG="0"
python app.py
 
# Windows (PowerShell)
$env:SECRET_KEY="sua-chave-aleatoria-aqui"
$env:DEBUG="0"
python app.py
```
 
> **Por que isso importa:** a chave de sessão assina o cookie que guarda as mensagens de confirmação do sistema. Com uma chave conhecida, alguém pode forjar um cookie válido. Como o repositório é público, definir uma chave própria evita esse risco. O modo debug, por sua vez, expõe o depurador interativo do Flask, que permite executar código pelo navegador — por isso deve ficar desligado fora do ambiente de desenvolvimento.
 
### Inicialização rápida com debug desligado
 
Se você usa o `run.bat` no dia a dia e quer abrir a aplicação em modo normal, edite o arquivo e adicione a variável antes do comando:
 
```bat
@echo off
set DEBUG=0
.venv\Scripts\python.exe app.py
```
 
Assim o atalho abre sem o depurador, e o modo debug fica disponível apenas quando você o ativa manualmente pelo terminal.
 
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
 
## Testes
 
O projeto usa pytest. Para executar:
 
```bash
pip install -r requirements-dev.txt
pytest
```
 
A suíte tem 22 testes cobrindo:
 
- Rotas de página (dashboard, nova auditoria, auditorias, clientes)
- Cadastro e exclusão de clientes, incluindo validação de nome obrigatório
- Execução de auditoria, com os quatro casos de validação que retornam erro 400
- Download de PDF existente e inexistente
- Exclusão de auditoria com remoção dos arquivos
- Configurações e valores padrão
- Funções utilitárias de persistência JSON
 
A integração contínua roda em Python 3.11, 3.12 e 3.13, com lint via Ruff.
 
## Estrutura do projeto
 
```text
compliance-suite/
├── app.py                  # Aplicação Flask principal
├── run.bat                 # Inicialização rápida (Windows)
├── requirements.txt        # Dependências Python
├── requirements-dev.txt    # Dependências de teste e lint
├── pytest.ini              # Configuração do pytest
├── .gitignore
├── README.md
├── LICENSE
├── icone.ico               # Ícone do atalho
├── .github/
│   └── workflows/
│       └── ci.yml          # Integração contínua
├── data/                   # Dados persistidos (JSON)
│   ├── clientes.json
│   ├── auditorias.json
│   └── settings.json
├── output/
│   ├── findings/           # Saídas do pii-guard (JSON)
│   └── relatorios/         # Relatórios PDF gerados
├── tests/                  # Suíte de testes (pytest)
│   ├── conftest.py
│   ├── test_app.py
│   └── test_smoke.py
└── templates/              # Templates HTML (Jinja2)
    ├── base.html
    ├── index.html
    ├── nova_auditoria.html
    ├── auditorias.html
    └── clientes.html
```
 
## Roadmap
 
| Etapa | Escopo | Status |
|---|---|---|
| Interface web com dashboard | Flask, Jinja2, histórico | Concluída |
| Integração com pii-guard | Execução do scan e captura de findings | Concluída |
| Geração de relatório PDF | ReportLab | Concluída |
| Gestão de clientes | Cadastro e vínculo com auditorias | Concluída |
| Publicação do compliance-audit | Motor de mapeamento como repositório público | Concluída |
| Suíte de testes automatizados | 22 testes com pytest | Concluída |
| Integração contínua | GitHub Actions em Python 3.11, 3.12 e 3.13 | Concluída |
| Chave de sessão por variável de ambiente | Remoção da chave fixa no código | Concluída |
| Modo debug por variável de ambiente | Remoção do debug fixo no código | Concluída |
| Exportação em CSV e JSON | Formatos alternativos de relatório | Planejada |
| Autenticação de usuários | Controle de acesso ao painel | Planejada |
 
## Contribuindo
 
Contribuições são bem-vindas. Para mudanças relevantes, abra uma issue descrevendo o problema ou a proposta antes de enviar um pull request.
 
```bash
git checkout -b feature/nome-da-feature
pytest          # garanta que os testes passam
git commit -m "feat: descrição da mudança"
```
 
## Licença
 
Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para os termos completos.
 
## Autor
 
**Berguy Silva** — Engenheiro de software, pós-graduado em Computação Forense e Perícia Digital e em Gestão de Projetos.
 
- LinkedIn: https://www.linkedin.com/in/BerguySilva
- GitHub: https://github.com/Berguy
- Email: contato@berguysilva.com.br
 
**Versão:** 1.2 · **Data:** novembro de 2026
O que mudou nesta versão
A tabela de variáveis de ambiente agora documenta SECRET_KEY e DEBUG, os dois nomes usados no app.py.
Adicionada explicação de por que o modo debug deve ficar desligado fora do ambiente de desenvolvimento: ele expõe o depurador interativo do Flask, que permite executar código pelo navegador.
Adicionado exemplo de configuração das duas variáveis em Linux/macOS e Windows PowerShell.
Adicionada seção sobre como desligar o debug no run.bat, para quem usa o atalho no dia a dia.
Adicionada a etapa "Modo debug por variável de ambiente" ao roadmap como concluída.
Versão atualizada de 1.1 para 1.2.
Pendências no repositório
Criar o arquivo requirements.txt com flask, pillow, reportlab, pii-guard e compliance-audit via git+https.
Criar o arquivo requirements-dev.txt com pytest e ruff.
Criar o arquivo LICENSE com o texto MIT.
Adicionar a pasta tests/ com conftest.py, test_app.py e test_smoke.py.
Adicionar o arquivo pytest.ini.
Adicionar o workflow .github/workflows/ci.yml.
