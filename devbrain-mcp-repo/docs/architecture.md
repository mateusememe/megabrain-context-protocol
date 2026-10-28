# Arquitetura do DevBrain MCP

O laboratório usa uma arquitetura hexagonal pequena. Não queremos transformar um
exercício de 3h30 num sistema corporativo. A ideia é que fique claro onde mora cada
decisão, e que dê para trocar o transporte (MCP, HTTP) ou a fonte das diretrizes sem
mexer na regra de negócio.

```text
                    adaptadores de entrada
  stdio ───────┐  src/.../adapters/inbound/mcp.py  ┌────── Streamable HTTP
  MCP host ────┼────────── Tools / Resource / Prompt ┼────── Cloud Run (container)
               │                                      │
               └───────────────┬──────────────────────┘
                               │
                         application
                  DevBrainUseCases (casos de uso)
                               │
                            domain
     regras R1..R5, risco, classificação de arquivos, evidências de branch
                               │
                     portas de saída read-only
          EngineeringGuidelinesPort         RepositoryPort
                   │                              │
      StaticEngineeringGuidelines      GitRepository (git local,
                (lab)                   só no laptop, nunca no Cloud Run)
```

Quem decide o que existe é o composition root. O `server.py` (stdio) e o `http.py`
montam o servidor com `GitRepository`; o `cloud_run.py` monta sem. Tools, resources e
prompts de repositório só são registrados quando há um repositório, e o cliente
percebe a diferença sozinho, no `tools/list`.

## Mapa de código

| Onde | Responsabilidade | Não deve conhecer |
|---|---|---|
| `domain/files.py` | o que é teste, doc, contrato público, dependência | MCP, git, filesystem |
| `domain/review.py` | regras R1..R5, risco e modelos de resultado | MCP, HTTP, nuvem, filesystem |
| `domain/changes.py` | evidências de uma branch (`BranchChanges`) | git, MCP |
| `application/use_cases.py` | orquestra os casos de uso | decorators MCP e transporte |
| `application/ports.py` | contratos para diretrizes e repositório, `RepositoryError` | implementação concreta |
| `adapters/inbound/mcp.py` | monta as primitivas MCP | regras de decisão detalhadas |
| `adapters/inbound/tools.py` | capabilities executáveis, todas read-only | transporte e regra de domínio |
| `adapters/inbound/resources.py` | contexto com URI estável | seleção autônoma de tool |
| `adapters/inbound/prompts.py` | templates e workflows explícitos | regra de domínio detalhada |
| `adapters/outbound/static_guidelines.py` | regras R1..R6 em Markdown | protocolo MCP |
| `adapters/outbound/git_repository.py` | git somente leitura, com validação e limites | protocolo MCP, regras |
| `server.py` | composition root e stdio; lê `DEVBRAIN_REPO_PATH` | regras de negócio |
| `http.py` | o mesmo servidor por Streamable HTTP local | regras de negócio |
| `cloud_run.py` | composition root da nuvem, sem repositório | regras de negócio |

## O caminho de uma chamada de tool

```text
Host -> check-pr-readiness (MCP adapter)
     -> DevBrainUseCases.check_pr_readiness
     -> domain.evaluate_pr_readiness
     -> PRReadiness estruturado -> Host
```

As três tools declaram `read_only_hint=True` e `open_world_hint=False`. Isso é uma
dica para o cliente, e o cliente pode ignorar. A segurança de verdade está no
servidor: ele não tem nenhuma operação de escrita, roda o git sem shell e com
argumentos validados, não deixa o modelo escolher o repositório e não lê o conteúdo
dos arquivos. A lista completa das defesas está no docstring de `git_repository.py`.

Erros esperados (`ValueError` do domínio, `RepositoryError` do adapter) viram
`ToolError` em `tools.py`. Assim a mensagem chega ao modelo com `isError: true`, em vez
de um "Error executing tool" genérico.

## Por onde evoluir

Quer trocar o texto fixo das diretrizes por um arquivo no Git ou uma API? Implemente
`EngineeringGuidelinesPort` num novo adapter de saída e injete no `server.py`. A regra
de prontidão continua onde está; ela não deve ir para o adapter de transporte.

Para uma capability nova, eu sigo esta ordem:

1. regra e teste em `domain/`;
2. caso de uso em `application/`;
3. adapter MCP com schema, descrição e anotações;
4. teste MCP in-process em `test/`.
