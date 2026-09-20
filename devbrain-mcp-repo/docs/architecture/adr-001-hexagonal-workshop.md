# ADR-001: Arquitetura hexagonal enxuta para o laboratório

## Status

Aceita.

## Contexto

O minicurso atende até 30 pessoas, tem 3h30 e precisa demonstrar um servidor MCP
testável por stdio, HTTP e Lambda. A versão inicial concentrava regra de negócio,
contratos MCP e composition root em `server.py`, o que dificultava explicar testes
sem transporte e a troca de fonte das diretrizes.

## Decisão

Usar `domain/`, `application/` e `adapters/`. Há apenas uma porta de saída:
`EngineeringGuidelinesPort`. MCP, HTTP e Lambda são adaptadores de entrada; o texto
fixo das diretrizes é um adapter de saída do laboratório.

## Alternativas consideradas

| Opção | Vantagem | Custo | Decisão |
|---|---|---|---|
| Arquivo único | menor número de arquivos | mistura responsabilidades | rejeitada |
| Hexagonal enxuta | troca de adapter e testes diretos claros | mais pastas | escolhida |
| DDD completo/microservices | máximo isolamento | conteúdo e operação excessivos | rejeitada |

## Consequências

- Positiva: regras podem ser testadas sem `Client`, porta ou processo.
- Positiva: a fonte das diretrizes pode virar Git/API mantendo os casos de uso.
- Negativa: o aluno precisa navegar por mais arquivos.
- Mitigação: o roteiro abre primeiro `adapters/inbound/mcp.py`, depois segue a seta
  para `application/` e `domain/`.

## Gatilho de revisão

Revisar se o laboratório adicionar I/O real, autenticação, múltiplas fontes de
diretrizes ou operações de escrita.
