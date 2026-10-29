# Documentação do DevBrain

Se é a primeira vez aqui, esta ordem funciona bem:

1. [setup.md](setup.md): o que instalar e como saber se o ambiente está ok.
2. [roteiro-de-testes.md](roteiro-de-testes.md): o que é cada peça do MCP e, depois,
   os comandos para testar tudo, do pytest ao Antigravity.
3. [tour-do-codigo.md](tour-do-codigo.md): arquivo por arquivo, onde moram as tools,
   os resources e os prompts, e o caminho de uma chamada.
4. [architecture.md](architecture.md): as camadas e por onde evoluir o servidor. A
   decisão de usar arquitetura hexagonal está registrada em
   [adr-001](architecture/adr-001-hexagonal-workshop.md).

Para consultar quando precisar:

- [troubleshooting.md](troubleshooting.md), quando algo não sobe ou o host não enxerga
  o servidor;
- [security-checklist.md](security-checklist.md), antes de levar um servidor MCP para
  um time de verdade.

Fora da aula, e opcional: [deploy-gcp.md](deploy-gcp.md) publica o servidor no Google
Cloud Run.
