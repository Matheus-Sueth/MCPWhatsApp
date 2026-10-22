# Sueth MCP WhatsApp

Servidor MCP independente para integração com a **WhatsApp Business Cloud API oficial da Meta**, desenvolvido em Python com MCP Streamable HTTP e SQLite.

> Importante: este conector não lê WhatsApp pessoal, não utiliza WhatsApp Web e não recupera histórico anterior à ativação do webhook. O número precisa estar vinculado à WhatsApp Business Platform. O suporte a operações de escrita no ChatGPT depende do plano e das permissões.

## Funcionalidades da V0.1

| Ferramenta | Escopo OAuth | Finalidade |
|---|---|---|
| verificar_status | whatsapp:read | Capacidades sem exibir segredos |
| listar_conversas | whatsapp:read | Lista contatos vistos pelo webhook |
| ler_conversa | whatsapp:read | Até 50 mensagens locais por contato |
| buscar_mensagens | whatsapp:read | Pesquisa textual no histórico armazenado |
| preparar_texto | whatsapp:send | Prévia da mensagem, sem enviar |
| preparar_template | whatsapp:send | Template aprovado e sem parâmetros, sem enviar |
| confirmar_envio | whatsapp:send | Confirma e realiza tentativa única de envio |

Rotas HTTP: GET /healthz, GET/POST /webhooks/whatsapp e /mcp.

O webhook verifica desafio e HMAC SHA-256, usa ID da mensagem para deduplicação e salva texto, contato, tipo, direção, data e status em SQLite. Anexos não são baixados.

## Arquitetura

    ChatGPT / cliente MCP
        | Authorization Code + PKCE / OAuth externo
        v
    Proxy HTTPS ----> /mcp ----> Ferramentas / Banco SQLite
                                        |
                                   Meta Graph API

    Meta WhatsApp Webhook assinado ---> /webhooks/whatsapp --> SQLite

A autenticação remota exige JWT RS256 emitido por um provedor OAuth/OIDC, validação de issuer, audience, expiração, subject e scopes. O código não emite tokens OAuth. O token da Meta fica somente no servidor.

## Execução local em Windows PowerShell

    git clone https://github.com/Matheus-Sueth/MCPWhatsApp.git
    cd MCPWhatsApp
    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -e ".[test]"
    Copy-Item .env.example .env
    # Preencher .env com os dados da Meta
    python -m whatsapp_mcp

No modo local, acesse http://127.0.0.1:8000/mcp e http://127.0.0.1:8000/healthz.

**O modo local não exige OAuth e NUNCA deve ser exposto por proxy, túnel, internet, NAT ou rede de produção.** Para usar o ChatGPT remotamente, selecione MCP_AUTH_MODE=oauth e configure o IdP antes do deploy.

## Configuração da Meta

1. No Meta for Developers, crie/configure um aplicativo com WhatsApp Business Platform e número vinculado.
2. Configure WHATSAPP_PHONE_NUMBER_ID e WHATSAPP_ACCESS_TOKEN. Em produção, prefira token de System User com permissões mínimas.
3. Cadastre https://SEU_DOMINIO/webhooks/whatsapp como callback de webhook, configure WHATSAPP_VERIFY_TOKEN e inscreva o campo messages.
4. Configure WHATSAPP_APP_SECRET (App Secret real), diferente do verify token, para a assinatura X-Hub-Signature-256.
5. Envie uma mensagem ao número Business. Apenas eventos novos começam a alimentar o banco.
6. Ajuste WHATSAPP_GRAPH_VERSION para a versão efetivamente suportada pelo seu aplicativo.

A mensagem de texto livre só pode ser enviada a um contato se houve mensagem recebida dele nas últimas 24 horas. Para iniciar contato fora desta janela, use um template aprovado pela Meta.

## Envio com confirmação

Por padrão MCP_ENABLE_SEND=false. Para testar envio com uma conta autorizada:

    MCP_ENABLE_SEND=true
    MCP_ALLOWED_RECIPIENTS=5511999999999,5511888888888

O fluxo exige preparar_texto ou preparar_template, visualizar a prévia, obter aprovação explícita do usuário e executar confirmar_envio com token_aprovacao e confirmacao_usuario igual a CONFIRMO. A reserva do token é atômica e só pode ser usada uma vez. A confirmação enviada pelo modelo não substitui a aprovação humana da interface de ChatGPT.

Não há retry automático de envio, pois um timeout pode representar entrega incerta. Não use mensagens em massa ou spam.

## Deploy em Docker

    cp .env.example .env
    # Ajuste OAuth, Meta e MCP_BIND_HOST=0.0.0.0 no arquivo .env para ambiente remoto
    mkdir -p data
    # Linux: chown 10001:10001 data && chmod 700 data
    docker compose up --build -d

A porta publicada pelo compose fica em 127.0.0.1:8000 na VPS. Use proxy HTTPS com domínio e Host preservado. Consulte docs/CONFIGURACAO_CHATGPT.md.

## Testes

    pip install -e ".[test]"
    pytest -q

Estão incluídos testes unitários de HMAC, SQLite, idempotência, janela de atendimento e validação de configuração. A integração de ponta a ponta com a Meta e com um IdP real exige credenciais e ambiente de homologação.

## Documentação

- [Configuração ChatGPT e OAuth](docs/CONFIGURACAO_CHATGPT.md)
- [Segurança e privacidade](docs/SEGURANCA.md)
- [Roadmap](docs/ROADMAP.md)

Licença MIT. Projeto independente, sem afiliação à Meta, WhatsApp ou OpenAI.
