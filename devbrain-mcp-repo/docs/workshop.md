# Roteiro do workshop

## Tese

**Construir capabilities reutilizáveis para agentes, não integrações específicas
para um único modelo ou cliente.**

MCP não é LLM, agente, banco de dados nem substituto de REST/gRPC. É a interface
padronizada pela qual uma aplicação de IA descobre e usa contexto e capabilities.

## Núcleo de 2h30

| Tempo | Bloco | Evidência de aprendizagem |
|---|---|---|
| 19:00–19:30 | WHY + história | explica o problema N x M e o papel do protocolo |
| 19:30–20:00 | arquitetura + design | diferencia Host, Client, Server, Tool, Resource e Prompt |
| 20:00–20:35 | build | uma tool com contrato tipado e regra determinística |
| 20:45–21:10 | resource, prompt, Inspector | primitives listadas e exercitadas sem LLM |
| 21:10–21:30 | testes + host | testes MCP in-process verdes; demo de host se disponível |
| 21:30–21:45 | local para remoto | explica stdio e Streamable HTTP |
| 21:45–22:30 | extras | CI/CD, AWS, segurança e Boss Fight |

## Modelo mental

```text
Host (contém MCP Client)
             |
         transporte MCP
             |
Server -> Tools | Resources | Prompts -> APIs, arquivos, DB e serviços
```

Use o DevBrain para mostrar três decisões distintas:

- `check-pr-readiness`: capability executável, estreita e determinística;
- `repo://engineering-guidelines`: contexto read-only com URI estável;
- `review-feature`: template/workflow escolhido explicitamente pelo usuário/host.

## Quando MCP não é a escolha

Se o único consumidor é um frontend chamando um backend, uma API normal costuma ser
mais simples. MCP passa a fazer sentido quando agentes/hosts compatíveis precisam
descobrir e reutilizar capabilities ou contexto de modo padronizado.

## História correta para o slide

- novembro de 2024: Anthropic anuncia MCP;
- 2025: adoção do ecossistema e evolução de transportes;
- dezembro de 2025: MCP torna-se contribuição fundadora da Agentic AI Foundation
  (Linux Foundation);
- julho de 2026: spec `2026-07-28`, core stateless e SDK Python v2.

Não apresente MCP como produto de um único vendor. Também não ensine FastMCP v1,
SSE ou handshakes/sessões antigos como caminho principal atual.
