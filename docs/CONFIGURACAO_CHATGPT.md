# Conectar o Sueth MCP WhatsApp ao ChatGPT

## Disponibilidade

O ChatGPT usa MCP remoto via HTTPS / Streamable HTTP. Em Plugins, use a opção de adicionar servidor MCP personalizado, se disponível na conta/workspace. Em outubro de 2026, ferramentas de escrita para MCP personalizado estão em beta para Business/Enterprise/Edu; outros planos podem permitir apenas leitura. Confirme as permissões atuais.

Fontes:
- https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt
- https://developers.openai.com/api/docs/guides/custom-mcp-server
- https://developers.openai.com/plugins/build/auth

## OAuth é obrigatório para servidor remoto

Este projeto funciona como **resource server**. Configure seu provedor OAuth 2.1/OIDC, como Keycloak ou Auth0, para:
- Authorization Code e PKCE S256; discovery de OAuth/OIDC acessível por HTTPS.
- Provisionar cliente compatível com CIMD ou Dynamic Client Registration (DCR) conforme sua escolha no ChatGPT e suporte do IdP.
- Publicar JWKS e emitir JWTs assinados em RS256.
- Incluir claims iss, aud, sub, exp e scope. Conceder whatsapp:read a quem pode consultar mensagens e whatsapp:send somente a quem pode enviá-las.
- Configurar refresh token/offline_access quando necessário para manter a sessão no ChatGPT.
- Restringir subjects com OAUTH_ALLOWED_SUBJECTS e proteger os registros da Meta.

Exemplo de .env (substitua os domínios ilustrativos):

    MCP_AUTH_MODE=oauth
    MCP_BIND_HOST=0.0.0.0
    MCP_PUBLIC_HOST=whatsapp-mcp.exemplo.com
    OAUTH_ISSUER_URL=https://auth.exemplo.com/realms/sueth
    OAUTH_JWKS_URL=https://auth.exemplo.com/realms/sueth/protocol/openid-connect/certs
    OAUTH_AUDIENCE=whatsapp-mcp
    OAUTH_RESOURCE_URL=https://whatsapp-mcp.exemplo.com/mcp
    OAUTH_ALLOWED_SUBJECTS=id-do-usuario-autorizado

O JwtVerifier valida a claim aud contra OAUTH_AUDIENCE (não contra a URL); o SDK anuncia OAUTH_RESOURCE_URL no protected resource metadata. Seu IdP precisa emitir o token destinado à API e aceitar fluxos do cliente ChatGPT compatíveis com suas configurações. Este projeto não cria clientes/realms/escopos no IdP automaticamente.

## Deploy HTTPS

1. Configure WABA, webhook e credenciais Meta.
2. Configure o IdP e preencha o .env em modo OAuth.
3. Suba o container na VPS, com ./data gravável pelo UID 10001.
4. Direcione seu domínio HTTPS para 127.0.0.1:8000 via Caddy/Nginx, preservando o Host.
5. Confirme os endpoints /mcp, /.well-known/oauth-protected-resource/mcp, /healthz e /webhooks/whatsapp.
6. Na Meta, registre https://DOMINIO/webhooks/whatsapp e assine o campo messages.
7. Em ChatGPT Web: Plugins > Adicionar servidor MCP personalizado > informe https://DOMINIO/mcp > OAuth > autorize, revise tools e instale.
8. Teste verificar_status e listar_conversas; habilite envio somente com allowlist e após confirmar a disponibilidade de escrita.

## Diagnóstico

- 401: token/issuer/JWKS/audience/subject/scope não corresponde.
- 421: Host enviado ao MCP não corresponde a MCP_PUBLIC_HOST.
- 403 Invalid Origin: configuração MCP_ALLOWED_ORIGINS ausente ou divergente.
- 403 webhook: challenge/verify token ou assinatura App Secret incorretos.
- Lista vazia: histórico anterior não é importado; webhook novo ainda não processado.
- Texto bloqueado: sem mensagem recebida nas últimas 24h, envio desligado ou destino fora da allowlist.
- Sem ferramentas de escrita: o plano/workspace pode restringir ações MCP.
