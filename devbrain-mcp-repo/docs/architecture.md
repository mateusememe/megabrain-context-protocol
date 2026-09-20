# Arquitetura — DevBrain MCP

O laboratório usa uma arquitetura hexagonal **enxuta**. O objetivo não é transformar
um exercício de 3h30 em um sistema corporativo; é deixar explícito onde cada decisão
mora e permitir trocar MCP/HTTP ou a fonte das diretrizes sem reescrever a regra de
negócio.

```text
                    adaptadores de entrada
  stdio ───────┐  src/.../adapters/inbound/mcp.py  ┌────── Streamable HTTP
  MCP host ────┼────────── Tools / Resource / Prompt ┼────── Lambda + Mangum
               │                                      │
               └───────────────┬──────────────────────┘
                               │
                         application
                  DevBrainUseCases (casos de uso)
                               │
                            domain
              regras de prontidão e análise de arquivos
                               │
                     porta de saída read-only
                    EngineeringGuidelinesPort
                               │
                 StaticEngineeringGuidelines (lab)
```

## Mapa de código

| Onde | Responsabilidade | Não deve conhecer |
|---|---|---|
| `domain/review.py` | regras determinísticas e modelos de resultado | MCP, HTTP, AWS, filesystem |
| `application/use_cases.py` | orquestra os casos de uso | decorators MCP e transporte |
| `application/ports.py` | contrato para obter diretrizes | implementação concreta |
| `adapters/inbound/mcp.py` | compõe as primitives MCP | regras de decisão detalhadas |
| `adapters/inbound/tools.py` | capabilities executáveis e read-only | transporte e regra de domínio |
| `adapters/inbound/resources.py` | contexto com URI estável | seleção autônoma de tool |
| `adapters/inbound/prompts.py` | templates/workflows explícitos | regra de domínio detalhada |
| `adapters/outbound/static_guidelines.py` | fonte local do laboratório | protocolo MCP |
| `server.py` | composition root e stdio | regras de negócio |
| `http.py` e `lambda_app.py` | adaptadores de transporte | regras de negócio |

## Fluxo de uma tool

```text
Host -> check-pr-readiness (MCP adapter)
     -> DevBrainUseCases.check_pr_readiness
     -> domain.evaluate_pr_readiness
     -> PRReadiness estruturado -> Host
```

As duas tools atuais são explicitamente `read_only_hint=True` e
`open_world_hint=False`. São hints para o cliente, não um controle de segurança;
o servidor continua sem acesso a shell, banco, arquivos ou rede.

## Onde evoluir no exercício

Para trocar o texto fixo por diretrizes em Git ou uma API, implemente
`EngineeringGuidelinesPort` em um novo adapter de saída e injete-o em `server.py`.
Não mova a regra de prontidão para o adapter de transporte.

Para novas capabilities, a sequência é:

1. regra/teste em `domain/`;
2. caso de uso em `application/`;
3. adapter MCP com schema, descrição e anotações de segurança;
4. teste MCP in-process em `test/`.
