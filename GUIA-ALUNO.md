# Guia do aluno: MCP, MegaBrain Context Protocol

## O que você vai construir

Um servidor MCP em Python, o DevBrain, que entrega critérios de engenharia para um
agente:

- `check-pr-readiness`, uma tool
- `analyze-changed-files`, outra tool
- `repo://engineering-guidelines`, um resource
- `review-feature`, um prompt

O repositório de referência vai um pouco além e lê evidências reais do git, sempre em
modo somente leitura: a tool `inspect-branch-changes`, o resource
`devbrain://repository/overview`, o resource template
`devbrain://repository/commits/{sha}` e o prompt `review-branch`. O
`docs/tour-do-codigo.md` explica cada um.

No fim, o mesmo servidor roda localmente por stdio ou como endpoint por Streamable
HTTP. Publicar no Google Cloud Run é um extra para depois do curso (Lab 7).

## Setup

O workshop usa o `uv` para cuidar de Python, dependências, ambiente virtual e execução.

Para o MCP Inspector, você também precisa de Node.js; ele só é usado ali. Antigravity
(ou outro host) é opcional para concluir o núcleo. Google Cloud só aparece no Lab 7.

```bash
uv --version
uv python install 3.12
uv sync
uv run pytest -q
```

O MCP Python SDK aceita Python 3.10+, mas a aula usa 3.12.

## Modelo mental

```text
Você
  |
Host (Antigravity IDE / Antigravity CLI / Gemini CLI / outro)
  |
MCP Client
  |
MCP transport
  |
DevBrain MCP Server
  |
Regras / APIs / dados
```

MCP não é um modelo e não substitui a sua API. Ele define um jeito padrão de uma
aplicação de IA consumir contexto e capabilities.

Vale usar MCP quando agentes ou hosts diferentes precisam descobrir e reaproveitar a
mesma capability. Se só um frontend chama um backend que você já conhece, REST ou gRPC
costumam ser mais simples.

## Lab 1: tool

Abra `src/devbrain_mcp/server.py` para ver onde o servidor é montado. Depois abra
`src/devbrain_mcp/adapters/inbound/tools.py` e procure `check_pr_readiness`. A regra
que ela chama está em `src/devbrain_mcp/domain/review.py`.

Repare em quatro coisas:

1. os type hints viram o `inputSchema`;
2. o retorno `PRReadiness` (Pydantic) vira `outputSchema` + `structuredContent`;
3. a regra de negócio é determinística: mesma entrada, mesma resposta;
4. a tool não recebe uma string genérica para "fazer qualquer coisa".

Essa separação é uma arquitetura hexagonal enxuta. O MCP é o adaptador de entrada, os
casos de uso ficam em `application/` e as regras puras em `domain/`.

No Python, a função se chama `check_pr_readiness`. Para o host, a tool se chama
`check-pr-readiness`, porque é esse o `name` registrado no decorator.

Abra no MCP Inspector:

```bash
uv run mcp dev src/devbrain_mcp/server.py
```

Teste com:

```json
{
  "title": "feat(auth): add passkey login",
  "changed_files": ["src/auth/passkey.py", "src/api/auth.py"],
  "has_tests": false,
  "has_docs": false
}
```

Pergunta para pensar: o que aconteceria se a tool se chamasse `execute` e recebesse só
`{ "query": "..." }`?

## Lab 2: resource

Leia `repo://engineering-guidelines` no Inspector.

Uma regra que ajuda: resource é contexto somente leitura, com um endereço natural;
tool é uma ação que o modelo pode escolher executar.

## Lab 3: prompt

Execute o `review-feature`.

Prompts são templates que o servidor oferece e que o usuário (ou o cliente) escolhe
usar. Não confunda com o modelo escolhendo uma tool sozinho.

## Lab 4: testes

```bash
uv run pytest -q
```

Os testes usam o `Client` oficial conectado ao próprio `MCPServer`, no mesmo processo.
Não sobe subprocesso nem abre porta, mas a chamada passa pela camada real do protocolo.
E não precisa de LLM nenhum: se o teste passa, o contrato está certo.

## Lab 5: host real

O repositório já traz `.agents/mcp_config.json`. O Antigravity IDE e o Antigravity CLI
leem esse arquivo quando o workspace é a pasta `devbrain-mcp-repo`.

### Antigravity CLI

```bash
brew install --cask antigravity-cli   # ou o instalador em antigravity.google/download
cd devbrain-mcp-repo
agy
```

Na sessão, digite `/mcp` e veja se o `devbrain` aparece conectado.

### Antigravity IDE

1. Abra a pasta `devbrain-mcp-repo`.
2. No painel do agente, vá em `…` → MCP Servers → Manage MCP Servers.
3. Em Settings → Customizations → Installed MCP Servers, clique em Refresh.
4. Na primeira chamada da tool, escolha allow.

Outros hosts seguem a mesma ideia: o comando `uv` com os argumentos `run devbrain-mcp`
(por exemplo, `gemini mcp add devbrain uv run devbrain-mcp`).

Um prompt para testar:

> Avalie se a feature "feat(auth): add passkey login" (arquivos src/auth/passkey.py e
> src/api/auth.py, sem testes e sem docs) está pronta para PR. Use o DevBrain e cite os
> IDs das regras.

Não diga qual tool usar. A graça é ver o agente descobrir sozinho. No nosso teste, o
Antigravity chamou `check-pr-readiness` e `analyze-changed-files` e montou uma tabela
de R1 a R5, com R2 e R3 bloqueando o PR.

## Lab 6: HTTP

```bash
uv run mcp run src/devbrain_mcp/server.py --transport streamable-http
```

Endpoint local:

```text
http://127.0.0.1:8000/mcp
```

stdio funciona muito bem quando o host inicia um processo local. Streamable HTTP é o
caminho quando o endpoint é compartilhado ou remoto.

## Lab 7 (extra): Google Cloud Run

> Este lab não faz parte da aula. Faça depois, se quiser publicar o servidor na nuvem.

O mesmo servidor vira um container. Para testar a imagem localmente (precisa de
Docker):

```bash
docker build -t devbrain-mcp .
docker run --rm -p 8080:8080 devbrain-mcp
```

No Cloud Run (precisa de um projeto Google Cloud com billing):

```bash
export GCP_PROJECT_ID=seu-projeto
./infrastructure/gcp/bootstrap.sh
./infrastructure/gcp/deploy.sh
gcloud run services proxy devbrain-mcp --region southamerica-east1 --port 8080
agy mcp add devbrain-cloud-run http://localhost:8080/mcp
```

O serviço é privado: só quem tem permissão IAM no projeto chega ao endpoint, e o
`proxy` autentica com a sua conta `gcloud`. Os detalhes estão em `docs/deploy-gcp.md`.

## Se algo falhar

O caminho principal não depende de nuvem nem de um host específico. Se o Inspector ou
o agente falharem, rode `uv run pytest -q`, leia os contratos e siga com o exercício.
O `docs/troubleshooting.md` tem os diagnósticos mais comuns.

## Desafio

Implemente uma tool nova:

```text
get-review-checklist
```

Ela precisa:

- receber `risk: low | medium | high`;
- devolver uma saída tipada;
- incluir security review e testes quando o risco for `high`;
- ter pelo menos um teste com `Client(mcp)`.

## Checklist de produção

- type hints e schemas coerentes
- capability específica, nada de tool genérica
- menor privilégio
- nenhum secret no código
- escrita idempotente
- confirmação humana para ações irreversíveis
- timeout e limites
- logging e tracing
- autenticação e autorização
- dados externos tratados como não confiáveis
- `uv.lock` gerado e versionado

## Referências

As referências oficiais estão em `REFERENCIAS.md`.
