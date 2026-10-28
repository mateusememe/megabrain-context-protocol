# ADR-001: arquitetura hexagonal enxuta para o laboratório

## Status

Aceita.

## Contexto

O minicurso tem até 30 pessoas e 3h30 de duração. Ele precisa mostrar um servidor MCP
que dá para testar por stdio, por HTTP e no Cloud Run. Na primeira versão, regra de
negócio, contratos MCP e composition root ficavam todos no `server.py`. Ficava difícil
explicar como testar a regra sem transporte, e mais difícil ainda trocar a fonte das
diretrizes.

## Decisão

Separar em `domain/`, `application/` e `adapters/`. A primeira versão tinha uma única
porta de saída, `EngineeringGuidelinesPort`; depois entrou a `RepositoryPort`, para ler
o git local. MCP, HTTP e Cloud Run são adaptadores de entrada. O texto fixo das
diretrizes é um adapter de saída do laboratório.

## Alternativas consideradas

| Opção | Vantagem | Custo | Decisão |
|---|---|---|---|
| Arquivo único | menos arquivos | mistura responsabilidades | rejeitada |
| Hexagonal enxuta | troca de adapter e testes diretos | mais pastas | escolhida |
| DDD completo ou microsserviços | isolamento máximo | conteúdo e operação demais para 3h30 | rejeitada |

## Consequências

A regra pode ser testada sem `Client`, porta ou processo, e a fonte das diretrizes
pode virar um arquivo no Git ou uma API sem mudar os casos de uso.

O custo é que o aluno navega por mais arquivos. Para compensar, o roteiro começa em
`adapters/inbound/mcp.py` e segue a seta até `application/` e `domain/`.

## Quando revisar

Se o laboratório ganhar autenticação, várias fontes de diretrizes ou operações de
escrita.
