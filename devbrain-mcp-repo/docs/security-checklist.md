# Security checklist

- [ ] Menor privilégio para IAM e APIs downstream
- [ ] Não expor uma tool genérica de shell/SQL quando uma capability específica resolve
- [ ] Validar todo input; saída do LLM não é trust boundary
- [ ] Separar read e write
- [ ] Tornar writes idempotentes e usar chaves de idempotência quando necessário
- [ ] Definir timeout e limites de tamanho
- [ ] Redigir secrets de logs
- [ ] Restringir hosts/origins em servidores HTTP
- [ ] Autenticar/autorizar servidores remotos de produção
- [ ] Exigir confirmação humana para operações irreversíveis
- [ ] Tratar conteúdo externo como não confiável (prompt injection)
- [ ] Testar tool descriptions contra instruções ambíguas ou maliciosas
- [ ] Executar `uv lock` e versionar `uv.lock` antes do evento
