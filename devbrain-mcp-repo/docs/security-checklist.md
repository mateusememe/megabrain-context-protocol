# Checklist de segurança

- [ ] Menor privilégio para IAM e para as APIs que o servidor chama
- [ ] Nada de tool genérica de shell ou SQL quando uma capability específica resolve
- [ ] Validar toda entrada: o argumento de uma tool vem do modelo e não é confiável
- [ ] Separar leitura de escrita
- [ ] Escritas idempotentes, com chave de idempotência quando precisar
- [ ] Timeout e limite de tamanho em tudo que vai para fora
- [ ] Nenhum secret nos logs
- [ ] Hosts e origins restritos nos servidores HTTP
- [ ] Servidor remoto com autenticação e autorização (Cloud Run privado com IAM, nunca `--allow-unauthenticated`)
- [ ] Service account de runtime dedicada, sem papéis sobrando
- [ ] CI com Workload Identity Federation, sem chave JSON de service account
- [ ] Confirmação humana para operações irreversíveis
- [ ] Conteúdo externo tratado como não confiável (prompt injection)
- [ ] Descrições das tools testadas contra instruções ambíguas ou maliciosas
- [ ] `uv.lock` gerado e versionado
