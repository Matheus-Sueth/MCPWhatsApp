# Segurança e privacidade

## Proteções implementadas

- Integração com Cloud API oficial, sem bibliotecas não oficiais do WhatsApp Web.
- GET de verificação de webhook e HMAC SHA-256 de payload bruto no POST.
- Filtro obrigatório por Phone Number ID configurado e limite de 512 KiB por evento.
- Deduplicação por ID de mensagem, limite de 50 registros consultados e sem armazenamento do JSON bruto do webhook.
- SQLite ignorado pelo Git, segredo da Meta apenas em ambiente e usuário de container sem root.
- OAuth remoto com RS256, issuer, expiração, audience, subjects e scopes.
- MCP local restrito ao loopback; não publicar modo local via proxy/túnel.
- DNS rebinding protection com allowlist Host/Origin configurável.
- Envio desligado por padrão, allowlist de destino, janela de atendimento e aprovação em duas etapas.
- Token de aprovação aleatório, armazenado somente por hash, uso único e TTL configurável.
- Sem retry automático de mensagens enviadas.

## Riscos e providências para produção

**Proteção de dados:** SQLite mantém mensagens em texto claro. Restrinja leitura do volume, use criptografia de disco, controle acesso, backups e retenção conforme LGPD e políticas aplicáveis. Não exponha o banco ao frontend público.

**Prompt injection:** o conteúdo de mensagens é texto de terceiros. O cliente/LLM não deve executar instruções inseridas por contatos maliciosos.

**Confirmação:** o valor CONFIRMO não comprova aprovação humana. O cliente MCP deve solicitar aprovação explícita antes de invocar operações de escrita.

**Isolamento:** esta V0.1 é single WABA / single number. Todo subject autorizado para leitura tem acesso a todas as conversas armazenadas; um verdadeiro multi-tenant exige isolamento de banco e autorização por WABA.

**Respostas incertas:** após timeout, mensagem pode ter sido processada pela Meta. Aprovação é consumida e marcada unknown; conferência manual é necessária antes de novo envio.

**Mídia:** arquivo, áudio, vídeo e imagem não são baixados. Só metadados resumidos, como tipo, são armazenados. Não há transcrição.

**Escala:** SQLite e webhook síncrono são suficientes para prototipação e baixo volume, não para carga alta/múltiplas instâncias. Use fila e PostgreSQL em próxima versão.

**Rotação:** mantenha Meta token, App Secret e credenciais OAuth em gerenciador de secrets. Nunca coloque esses valores em Git, logs ou prompts.

**Homologação:** execute teste end-to-end real com Meta, IdP e ChatGPT e uma auditoria de dependências antes de produção. Não envie spam ou mensagens em massa.
