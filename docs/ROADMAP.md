# Roadmap MCPWhatsApp

## V0.1 — MVP no repositório

- [x] Estrutura Python / MCP Streamable HTTP / Docker
- [x] API Meta WhatsApp: texto e template simples
- [x] Webhook com desafio e HMAC SHA-256
- [x] SQLite com deduplicação de mensagens
- [x] Ferramentas de listagem, leitura e pesquisa
- [x] Prévia e confirmação de envio com token de uso único
- [x] Janela de 24h, allowlist de contatos, modo read-only padrão
- [x] Resource Server OAuth com verificação JWT RS256
- [x] Testes unitários e documentação inicial
- [ ] Homologação de integração com WABA/IdP/ChatGPT real
- [ ] Revisão de segurança/SAST e testes de carga

## V0.2 — Recursos adicionais

- [ ] Templates com parâmetros, listagem de templates e seus estados
- [ ] Filtro de conversas por data/status e paginação por cursor
- [ ] Histórico de anexos/metadados, mídias e transcrição de áudio
- [ ] Consentimento/opt-in e gerenciamento de contatos
- [ ] Indicadores de custos, envio e falhas

## V0.3 — Escalabilidade e governança

- [ ] Multi-WABA, multiempresa e isolamento de dados
- [ ] PostgreSQL, migrations, fila de webhooks e retries idempotentes
- [ ] Auditoria e retenção configurável de mensagens
- [ ] Dashboard operacional de ferramentas, status e eventos MCP
- [ ] Integração com secrets manager e CI/CD

Não incluir automação não oficial de WhatsApp pessoal nesta linha de produto sem análise independente de riscos, termos e consentimentos.
