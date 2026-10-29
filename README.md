# MegaBrain Context Protocol

Material do minicurso de MCP (Model Context Protocol) do DevFest 2026. Na aula a gente
constrói o DevBrain, um servidor MCP em Python que ajuda um agente de código a
responder uma pergunta bem concreta: essa branch está pronta para virar PR?

A ideia central é simples. As regras de revisão ficam no código, não no prompt. O
agente descobre as tools do servidor, chama, lê os resources e justifica a resposta
com o que voltou. Como é MCP, o mesmo servidor funciona no Antigravity, no Gemini CLI,
no Claude Code, no GitHub Copilot ou no Codex, sem mudar uma linha.

## Comece aqui

Você precisa de Git, [uv](https://docs.astral.sh/uv/) e um editor. Node.js só entra
para o MCP Inspector. Python não precisa instalar à mão, o uv cuida disso.

```bash
git clone https://github.com/mateusememe/megabrain-context-protocol.git
cd megabrain-context-protocol/devbrain-mcp-repo
uv python install 3.12
uv sync
uv run pytest -q
```

Se os testes passarem, o ambiente está pronto. Daí é seguir o
[guia do aluno](GUIA-ALUNO.md), que tem os labs na ordem da aula.

## O que tem aqui

```text
.
├── GUIA-ALUNO.md            os labs da aula, do primeiro tool ao host real
├── REFERENCIAS.md           links oficiais: spec, SDK, hosts
├── apresentacao/            os slides da palestra, em reveal.js
├── devbrain-mcp-repo/       o servidor MCP
│   ├── src/devbrain_mcp/    código em camadas: domain, application, adapters
│   ├── test/                testes com o Client MCP, sem LLM no meio
│   ├── docs/                roteiro de testes, tour do código, arquitetura
│   ├── configs/             exemplos de config para cada host
│   ├── scripts/             demo do protocolo sem LLM e utilitários
│   └── infrastructure/gcp/  deploy no Google Cloud Run (opcional)
└── .github/workflows/       CI com lint e testes, e o deploy opcional
```

## Por onde ir

| Você quer | Abra |
|---|---|
| acompanhar a aula | [GUIA-ALUNO.md](GUIA-ALUNO.md) |
| testar tudo do zero, comando por comando | [roteiro de testes](devbrain-mcp-repo/docs/roteiro-de-testes.md) |
| achar no código cada conceito de MCP | [tour do código](devbrain-mcp-repo/docs/tour-do-codigo.md) |
| entender as camadas e por que são assim | [arquitetura](devbrain-mcp-repo/docs/architecture.md) |
| conectar Antigravity, Claude Code ou outro host | [README do servidor](devbrain-mcp-repo/README.md) |
| resolver um erro | [troubleshooting](devbrain-mcp-repo/docs/troubleshooting.md) |
| ver todos os docs, na ordem de leitura | [docs/](devbrain-mcp-repo/docs/README.md) |
| rever os slides | [apresentacao/](apresentacao/README.md) |

## Deploy

Fica fora da aula. Dá para terminar tudo só com o Inspector, os testes e um host
local. Se depois você quiser publicar o servidor no Google Cloud Run, o passo a passo
está em [deploy-gcp.md](devbrain-mcp-repo/docs/deploy-gcp.md). O workflow de deploy
deste repositório fica parado até alguém configurar um projeto Google Cloud.

## Quem fez

Maria Beatriz França e Mateus Mendonça Monteiro, para o DevFest 2026. O código está
sob a [licença MIT](LICENSE).
