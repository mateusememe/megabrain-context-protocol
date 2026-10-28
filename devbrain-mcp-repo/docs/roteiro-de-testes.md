# Roteiro de testes: do zero ao Antigravity

Este guia é para quem nunca mexeu com MCP. Primeiro vêm os conceitos, depois os
comandos, na ordem em que vale a pena testar. Os comandos foram rodados em outubro de
2026 com macOS, `uv` + Python 3.12, MCP Python SDK 2.2, Inspector 2.12, Antigravity CLI
1.4.8 e Claude Code 2.1.287. Em outras versões, um ou outro detalhe de tela pode mudar.

## Parte 1: o que é cada coisa

### O problema

Um LLM (Gemini, Claude, GPT) sabe raciocinar, mas não enxerga o seu repositório, o seu
banco ou as regras do seu time. Cada ferramenta de IA inventava o próprio jeito de
plugar sistemas externos. Com N ferramentas e M sistemas, isso dá N × M integrações
para manter.

### A solução: MCP

MCP (Model Context Protocol) é um protocolo aberto: um contrato comum para uma aplicação
de IA descobrir e usar capabilities de outros sistemas. A analogia de sempre é o USB-C.
Você constrói o "dispositivo" uma vez, e ele funciona em qualquer "computador"
compatível.

> MCP não deixa o modelo mais inteligente. Ele padroniza como o modelo acessa contexto
> e ações.

### As peças

| Peça | O que é | No workshop |
|---|---|---|
| Host | a aplicação onde você conversa com a IA | Antigravity IDE, Antigravity CLI, Claude Code, Gemini CLI |
| MCP Client | a parte do host que fala o protocolo com um servidor | embutido no Antigravity; nos testes, o `Client` do SDK Python |
| MCP Server | o programa que expõe capabilities | o DevBrain (`src/devbrain_mcp/`) |
| Transport | o caminho das mensagens | stdio (processo local) e Streamable HTTP (rede) |
| JSON-RPC | o formato das mensagens | `{"method": "tools/call", "params": {...}}` |

### O que um servidor oferece

| Primitiva | Quem decide usar | Exemplo no DevBrain |
|---|---|---|
| Tool | o modelo decide chamar | `inspect-branch-changes`, `check-pr-readiness`, `analyze-changed-files` |
| Resource | o host ou o usuário anexa como contexto (só leitura) | `repo://engineering-guidelines`, `devbrain://repository/overview` |
| Resource template | o host preenche o `{parâmetro}` da URI | `devbrain://repository/commits/{sha}` |
| Prompt | o usuário escolhe um template | `review-branch`, `review-feature` |

Para entender cada arquivo do servidor, leia o [tour do código](tour-do-codigo.md).

### Como uma chamada acontece

```text
Você: "Essa feature de passkey está pronta para PR?"
  │
Host (Antigravity) ── pergunta ao servidor: quais tools existem? (tools/list)
  │
Modelo lê nome + descrição + schema e decide: chamar check-pr-readiness
  │
Host pede sua aprovação (human-in-the-loop) ── você clica "allow"
  │
MCP Client ── tools/call ──► DevBrain ──► regra em domain/review.py
  │
Resposta estruturada: {"ready": false, "risk": "high", "problems": [...]}
  │
Modelo explica o resultado para você, citando as evidências
```

### Detalhes que fazem diferença

Ninguém escreve JSON Schema à mão. Os type hints da função Python viram o
`inputSchema`, e o retorno Pydantic vira o `outputSchema` e o `structuredContent`.

stdio e HTTP funcionam de jeitos bem diferentes. Com stdio, o host inicia o servidor
como processo filho e conversa por stdin/stdout. É por isso que nada pode ser impresso
em stdout. Com Streamable HTTP, o servidor fica rodando num endereço (`/mcp`), e vários
hosts podem se conectar a ele.

A spec 2026-07-28 é stateless. Cada request HTTP carrega tudo de que precisa, sem
sessão nem handshake obrigatório, e por isso o Cloud Run pode subir quantas instâncias
quiser.

No DevBrain, o MCP é só a porta de entrada (`adapters/inbound/`). A regra de negócio
fica em `domain/review.py`, e dá para testar sem MCP nenhum.

O DevBrain lê o repositório indicado em `DEVBRAIN_REPO_PATH`. Sem a variável, lê o
repositório git da pasta onde o servidor foi iniciado: rodando de dentro de
`devbrain-mcp-repo/`, ele lê o próprio `megabrain-context-protocol`. Sem repositório
nenhum (no Cloud Run), só aparecem as tools de regras puras.

## Parte 2: os comandos

Todos os comandos rodam dentro da pasta `devbrain-mcp-repo/`.

### 0. O que instalar

| Ferramenta | Para quê | macOS |
|---|---|---|
| `uv` | Python, dependências e execução | `brew install uv` |
| Node.js | só para o MCP Inspector | `brew install node` |
| Docker | opcional: testar a imagem do Cloud Run | Docker Desktop |
| Antigravity CLI | host no terminal | `brew install --cask antigravity-cli` |
| Antigravity IDE | host no editor | `brew install --cask antigravity-ide` |
| Claude Code | outro host MCP (opcional) | `brew install --cask claude-code` |
| Google Cloud CLI | só para o extra de deploy | `brew install --cask gcloud-cli` |

### 1. Ambiente, lint e testes

```bash
cd devbrain-mcp-repo
uv sync
uv run ruff check .
uv run pytest -q
```

O esperado é `All checks passed!` e `35 passed`. Os testes de servidor usam o `Client`
MCP oficial dentro do mesmo processo: passam pelo protocolo de verdade, sem rede e sem
LLM. Os testes de git criam um repositório temporário, então não dependem da sua
máquina.

### 2. MCP Inspector, o "Postman" do MCP

```bash
uv run mcp dev src/devbrain_mcp/server.py
```

O terminal mostra `MCP Inspector Web is up and running at: http://127.0.0.1:6274?...`.
Abra essa URL inteira (ela traz um token) e:

1. Em Servers, ligue o toggle. O status muda para Connected.
2. Na aba Tools aparecem `check-pr-readiness`, `analyze-changed-files` e
   `inspect-branch-changes`, marcadas como READ-ONLY.
3. Clique em `check-pr-readiness` e preencha Title = `feat(auth): add passkey login` e
   Changed Files = `["src/auth/passkey.py", "src/api/auth.py"]`. Deixe os checkboxes
   desmarcados e clique em Execute Tool.
4. Olhe também Resources (3 URIs e 1 template) e Prompts (`review-branch` e
   `review-feature`). O painel Messages mostra o JSON-RPC trocado.

> Se o servidor não funciona no Inspector, não adianta culpar o agente.

Quer apontar o Inspector para outro repositório? Exportar `DEVBRAIN_REPO_PATH` antes do
`mcp dev` não funciona, porque o Inspector não repassa a variável ao servidor, e ele
continua lendo a pasta atual. Gere uma config com `env` explícito e passe com
`--config`:

```bash
./scripts/preparar_demo.sh ~/caminho/do/seu-repo
npx -y @modelcontextprotocol/inspector@2.12.0 --config demo/seu-repo/claude-mcp.json --server devbrain
```

O nome da pasta dentro de `demo/` é o nome do seu repositório. O script imprime o
comando exato.

Se o botão Execute não responder, o Inspector também tem modo CLI:

```bash
npx -y @modelcontextprotocol/inspector@2.12.0 --cli --config demo/seu-repo/claude-mcp.json --server devbrain \
  --method tools/call --tool-name inspect-branch-changes --tool-arg base=main --tool-arg head=sua-branch
```

### 3. Servidor HTTP local e smoke test

Terminal 1:

```bash
uv run devbrain-mcp-http
```

Terminal 2:

```bash
uv run python scripts/smoke_http.py
```

Saída esperada:

```text
tools:     ['analyze-changed-files', 'check-pr-readiness', 'inspect-branch-changes']
resources: ['devbrain://repository/overview', 'devbrain://server/guide', 'repo://engineering-guidelines']
prompts:   ['review-branch', 'review-feature']
check-pr-readiness: {'ready': False, 'risk': 'high', 'risk_reason': 'Área de alto risco alterada: src/api/auth.py, src/auth/passkey.py.', 'problems': ['Área de alto risco alterada sem testes automatizados.', 'Contrato público alterado sem atualização de documentação.'], 'recommendations': [], 'checks': [{'rule': 'R1', 'passed': True, ...}, {'rule': 'R2', 'passed': False, ...}, ...]}
```

### 3b. O protocolo sem LLM, num repositório seu

O `scripts/demo_sem_llm.py` é um MCP Client. Ele sobe o DevBrain por stdio, como um
host faria, e encadeia as tools como um agente faria:

```bash
uv run python scripts/demo_sem_llm.py ~/caminho/do/seu-repo main sua-branch
```

Você vê, passo a passo, a descoberta das primitivas, a leitura das evidências do git,
a avaliação do PR e um erro legível quando a branch não existe. Ninguém raciocina ali:
é só protocolo. É exatamente o que o agente vai fazer depois, com a diferença de que
ele escolhe sozinho a ordem.

### 4. O protocolo "cru" com curl

Com o servidor do passo 3 rodando, este comando mostra o que um MCP Client manda de
verdade:

```bash
curl -s -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: tools/call' \
  -H 'Mcp-Name: check-pr-readiness' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}},"name":"check-pr-readiness","arguments":{"title":"feat(auth): add passkey login","changed_files":["src/auth/passkey.py","src/api/auth.py"],"has_tests":false}}}'
```

Para listar as tools, troque o método por `tools/list` e tire `Mcp-Name`, `name` e
`arguments`. Três coisas para reparar:

- `MCP-Protocol-Version` e `_meta`: no core stateless, cada request informa a versão do
  protocolo e as capabilities do cliente. É isso que substitui o antigo handshake.
- `Mcp-Method` e `Mcp-Name` repetem o método e a tool no header. Assim, gateways e load
  balancers conseguem rotear sem abrir o corpo da mensagem.
- Sem esses campos, o servidor responde com erro `-32602` ou `-32020`.

Não faça `GET /mcp` com curl: ele abre um stream que nunca termina.

### 5. Imagem Docker (a mesma do Cloud Run)

```bash
docker build -t devbrain-mcp .
docker run --rm -p 8080:8080 devbrain-mcp
```

Em outro terminal:

```bash
uv run python scripts/smoke_http.py http://localhost:8080/mcp
```

O container roda com um usuário sem privilégios (`uid=10001`) e lê a porta da variável
`PORT`, como o Cloud Run exige.

O esperado é `tools: ['analyze-changed-files', 'check-pr-readiness']`, só duas. Isso é
de propósito: na nuvem não existe o seu repositório, então o `cloud_run.py` não
registra `inspect-branch-changes`, o overview, o template de commits nem o prompt
`review-branch`.

### 6. Antigravity CLI

O repositório já traz `.agents/mcp_config.json`. Quando o workspace é esta pasta, o
Antigravity inicia o DevBrain por stdio sozinho:

```json
{
  "mcpServers": {
    "devbrain": { "command": "uv", "args": ["run", "devbrain-mcp"] },
    "devbrain-cloud-run": { "serverUrl": "http://localhost:8080/mcp", "disabled": true }
  }
}
```

Um teste rápido de descoberta, sem chamar tool nenhuma:

```bash
agy -p "Liste apenas os nomes das ferramentas MCP do servidor devbrain que você tem disponíveis. Não chame nenhuma ferramenta e não edite arquivos."
```

Devem aparecer `check-pr-readiness`, `analyze-changed-files` e `inspect-branch-changes`.
Para apontar o Antigravity para outro repositório, abra o workspace que o
`./scripts/preparar_demo.sh` gera em `demo/<repo>/antigravity`.

Agora a conversa de verdade, no modo interativo:

```bash
agy
```

1. Digite `/mcp` e confira que o `devbrain` está conectado.
2. Mande este prompt, sem dizer qual tool usar:

   > Avalie se a feature "feat(auth): add passkey login" (arquivos src/auth/passkey.py e
   > src/api/auth.py, sem testes e sem docs) está pronta para PR. Use o DevBrain e cite
   > os IDs das regras.

3. Quando o Antigravity pedir aprovação para chamar a tool, escolha allow.

Com o Antigravity CLI 1.4.8, ele chamou `check-pr-readiness` e
`analyze-changed-files`, respondeu `ready: false` com risco alto e montou uma tabela
com R1 a R5: R2 (faltam testes) e R3 (falta documentação) bloqueiam, as outras passam.
Repare que ele leu as definições das tools antes de chamar. É a descoberta acontecendo
na sua frente.

No modo `agy -p` (não interativo), o Antigravity nega sozinho qualquer aprovação
pendente; o log mostra `soft-denying tool confirmation "CallMcpTool"`. Dá para liberar
só as tools do DevBrain sem pergunta, adicionando `mcp(devbrain/*)` em
`permissions.allow` no `~/.gemini/antigravity-cli/settings.json` (ou com `/permissions`
dentro do `agy`). Eu prefiro manter a aprovação: é o exemplo mais concreto de
human-in-the-loop que você vai ver na aula.

Para registrar o servidor globalmente (funciona em qualquer pasta):

```bash
agy mcp add devbrain -- uv --directory "$PWD" run devbrain-mcp
agy mcp list
```

### 7. Antigravity IDE

1. Abra a pasta `devbrain-mcp-repo` no Antigravity IDE.
2. No painel do agente, vá em `…` → MCP Servers → Manage MCP Servers. O View raw
   config mostra o JSON.
3. Em Settings → Customizations → Installed MCP Servers, clique em Refresh. O
   `devbrain` aparece.
4. Mande o mesmo prompt do passo 6 e escolha allow na primeira chamada.

A IDE lê o mesmo `.agents/mcp_config.json` do CLI.

### 8. Claude Code

Mesmo servidor, outro host, e nenhuma linha do DevBrain muda. O Claude Code lê o
`.mcp.json` desta pasta, no mesmo formato `mcpServers` do Antigravity:

```json
{ "mcpServers": { "devbrain": { "command": "uv", "args": ["run", "devbrain-mcp"] } } }
```

Um teste não interativo. O `--allowedTools` libera só as tools do DevBrain nesta
execução, sem mudar configuração nenhuma:

```bash
claude -p "Avalie se a feature 'feat(auth): add passkey login' (arquivos src/auth/passkey.py e src/api/auth.py, sem testes e sem docs) está pronta para PR. Use as ferramentas DevBrain quando forem relevantes e cite as evidências." \
  --mcp-config .mcp.json --strict-mcp-config \
  --allowedTools "mcp__devbrain__check-pr-readiness,mcp__devbrain__analyze-changed-files"
```

O Claude deve chamar `check-pr-readiness` (`ready: false`, `risk: high`) e
`analyze-changed-files` (`areas: ["api", "security"]`) e citar os dois resultados. No
Claude, uma tool MCP vira `mcp__<servidor>__<tool>`; é esse o nome que vai no
`--allowedTools`.

Se o Claude responder sem chamar tool nenhuma, veja se o seu `~/.claude/settings.json`
manda as requisições para algum proxy (`ANTHROPIC_BASE_URL`). Nos nossos testes, um
proxy local fez as definições das tools MCP se perderem no caminho. Acrescentar
`--setting-sources project,local` ignora esse arquivo só naquela execução.

Para um repositório seu, use a config que o `./scripts/preparar_demo.sh` gera:
`claude --mcp-config demo/seu-repo/claude-mcp.json --strict-mcp-config`. Dentro da
sessão, o prompt MCP vira comando: `/mcp__devbrain__review-branch main HEAD`.

No modo interativo:

```bash
claude
```

1. Na primeira vez, o Claude pergunta se você confia no servidor `devbrain` do
   `.mcp.json`. Aprove. Antes disso, `claude mcp list` mostra `Pending approval`.
2. Digite `/mcp` e confira que o `devbrain` está conectado.
3. Mande o mesmo prompt do passo 6 e aprove a chamada da tool quando ele pedir.

Para registrar o servidor só para você, fora do `.mcp.json`:

```bash
claude mcp add devbrain -- uv --directory "$PWD" run devbrain-mcp
```

> Uma história real: no primeiro teste com o Claude, `analyze-changed-files` falhava
> com `Structured content does not match the tool's output schema`. O `outputSchema`
> publicado exigia `review_focus`, mas a resposta saía como `reviewFocus`, por causa de
> um alias do Pydantic. O Claude valida o resultado contra o schema e recusou a
> resposta. O bug foi corrigido e hoje está coberto por
> `test_analyze_changed_files_matches_its_output_schema`. Quando alguém perguntar por
> que o contrato importa, conte essa.

### 9. Cloud Run (extra, precisa de billing)

```bash
export GCP_PROJECT_ID=seu-projeto
./infrastructure/gcp/bootstrap.sh
./infrastructure/gcp/deploy.sh
gcloud run services proxy devbrain-mcp --region southamerica-east1 --port 8080
```

Com o proxy aberto, rode o mesmo smoke test do passo 5. Pare o container Docker antes,
porque os dois usam a porta 8080:

```bash
uv run python scripts/smoke_http.py http://localhost:8080/mcp
```

No Antigravity, troque `"disabled": true` para `false` em `devbrain-cloud-run` e clique
em Refresh. GitHub Actions, detalhes e limpeza estão em `docs/deploy-gcp.md`.
