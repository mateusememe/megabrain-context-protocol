# Troubleshooting

| Sintoma | Como diagnosticar | O que fazer |
|---|---|---|
| `uv` não encontrado | `uv --version` | termine a instalação do uv e abra um terminal novo |
| Python ausente ou na versão errada | `uv python install 3.12` | `uv python pin 3.12`, depois `uv sync` |
| Inspector não abre | `node --version`, depois `uv run mcp dev ...` | instale o Node.js; enquanto isso, rode `uv run pytest -q`, que testa o mesmo contrato |
| tool não aparece | `uv run pytest -q` | confira os decorators em `adapters/inbound/` e reinicie o Inspector |
| host não chama a tool | veja se ela aparece no Inspector primeiro | chame a tool à mão no Inspector e melhore nome e descrição antes de mexer no prompt |
| porta HTTP ocupada | `lsof -i :8000` | encerre o processo anterior ou use outra porta |
| Inspector mostra o repositório errado | o `DEVBRAIN_REPO_PATH` exportado não chega ao servidor no `mcp dev` | use `--config` com `env` explícito (veja o [roteiro de testes](roteiro-de-testes.md)) |
| `gcloud` ou Cloud Run indisponível | o deploy é extra | ignore durante a aula; o núcleo não depende da nuvem |

Antes de pedir ajuda, rode `uv run ruff check .` e `uv run pytest -q`. Se os dois
passam, o servidor está bom, e o problema quase sempre está no host ou no Inspector.
