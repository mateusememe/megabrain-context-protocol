# Troubleshooting e failsafe ao vivo

| Sintoma | Diagnóstico rápido | Fallback seguro |
|---|---|---|
| `uv` não encontrado | `uv --version` | concluir instalação antes da aula; usar ZIP/repo já clonado |
| Python ausente/errado | `uv python install 3.12` | `uv python pin 3.12`, depois `uv sync` |
| Inspector não abre | `node --version`, depois `uv run mcp dev ...` | usar `uv run pytest -q` e mostrar o contrato pelo teste |
| tool não aparece | `uv run pytest -q` | conferir decorators em `adapters/inbound/` e reiniciar Inspector |
| host não chama tool | listar no Inspector primeiro | demonstrar chamada manual e melhorar nome/docstring, sem forçar prompt |
| porta HTTP ocupada | encerrar processo local anterior | manter a explicação remota e voltar ao Inspector |
| AWS/SAM indisponível | não diagnosticar cloud no núcleo | usar diagrama e workflow; deploy fica para o instrutor/pós-evento |

## Checkpoints a preparar antes do evento

Publique tags ou branches a partir de commits verdes:

1. `starter`: projeto com dependências e teste inicial;
2. `checkpoint-1`: tools;
3. `checkpoint-2`: resource + prompt + testes;
4. `final`: HTTP, CI/CD e material de produção.

Cada checkpoint precisa passar `uv run ruff check .` e `uv run pytest -q`.
O servidor e o Inspector são a trilha obrigatória; host e AWS nunca bloqueiam a aula.
