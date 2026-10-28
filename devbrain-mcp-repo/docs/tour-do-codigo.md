# Tour do código: onde cada conceito de MCP mora

Um passeio pelo DevBrain, arquivo por arquivo. A ordem segue o caminho de uma
chamada: de fora (o host) para dentro (a regra), e depois de volta.

Os comandos para rodar tudo isso estão no [roteiro de testes](roteiro-de-testes.md).

## O mapa em uma tela

```text
src/devbrain_mcp/
├── server.py            composition root (stdio): escolhe os adapters, lê DEVBRAIN_REPO_PATH
├── http.py              mesmo servidor, por Streamable HTTP local (porta 8000)
├── cloud_run.py         composition root da nuvem: SEM repositório
├── adapters/
│   ├── inbound/         ← o protocolo MCP mora aqui, e só aqui
│   │   ├── mcp.py           cria o MCPServer: nome, versão, instructions
│   │   ├── tools.py         o que o MODELO pode chamar
│   │   ├── resources.py     o que o HOST/USUÁRIO pode anexar
│   │   └── prompts.py       workflows que o USUÁRIO escolhe
│   └── outbound/        ← o mundo externo
│       ├── git_repository.py    git somente leitura (o arquivo de segurança)
│       └── static_guidelines.py as regras R1..R6 em Markdown
├── application/
│   ├── ports.py         contratos (Protocol) que os adapters de saída cumprem
│   └── use_cases.py     o que o DevBrain sabe fazer, sem saber de MCP
└── domain/              ← regra pura: sem MCP, sem git, sem rede
    ├── files.py         o que é teste, doc, contrato público, dependência
    ├── review.py        regras R1..R5, risco, focos de revisão
    └── changes.py       evidências de uma branch (BranchChanges)
```

Se for para guardar uma frase só: o MCP é a porta de entrada, e nada mais. Domínio,
aplicação e adapter git não importam nada do SDK MCP, e os 23 testes de domínio e de
git rodam sem ele.

## A jornada de uma chamada

Exemplo: o modelo chama `inspect-branch-changes` com `base="main"` e
`head="feature/passkey"`.

```text
1. Host ──JSON-RPC tools/call──► stdin do processo `uv run devbrain-mcp`
2. SDK MCP valida os argumentos contra o inputSchema
3. adapters/inbound/tools.py   inspect_branch_changes(base, head)
4. application/use_cases.py    DevBrainUseCases.inspect_branch_changes
5. adapters/outbound/git_repository.py
       valida "main" e "feature/passkey" (regex + rev-parse)
       git log main..feature/passkey      → commits
       git diff main...feature/passkey    → arquivos (+/-)
6. domain/changes.py           summarize_branch → has_tests, has_docs, suggested_title...
7. volta como BranchChanges (Pydantic)
8. SDK serializa: structuredContent (JSON) + content (texto) e valida contra o outputSchema
9. ◄──JSON-RPC result── stdout ──► Host ──► modelo
```

Quando dá um erro esperado (uma referência que não existe), a volta é assim:
`RepositoryError` (outbound) → `ToolError` (inbound, em `as_tool_error`) → resultado
com `isError: true` e a mensagem legível.

---

## 1. `server.py`: o composition root

Composition root é o único lugar do código que escolhe implementações. Aqui ele:

- lê `DEVBRAIN_REPO_PATH` ou, sem a variável, usa a pasta atual;
- tenta criar o `GitRepository`. Se não houver repositório, o servidor sobe mesmo
  assim, só com as regras puras, e registra um aviso em stderr;
- monta `DevBrainUseCases(diretrizes, repositório)` e entrega a `create_mcp_server`.

Repare no stdout. No transporte stdio, ele é o canal do JSON-RPC, e um `print()` no
servidor corrompe a conversa. Diagnóstico vai para stderr, via `logging`. Quando você
roda o `demo_sem_llm.py` e aparece um `INFO Tool ... failed` no terminal, é exatamente
isso: log no stderr, protocolo intacto.

Outro detalhe: o `uv run mcp dev src/devbrain_mcp/server.py` procura uma variável
chamada `mcp` (ou `server`, ou `app`) no arquivo. Por isso o objeto fica no nível do
módulo, e não dentro de uma função.

## 2. `adapters/inbound/mcp.py`: identidade do servidor

```python
MCPServer("devbrain", title="DevBrain", version="1.1.0", instructions=INSTRUCTIONS)
```

- `name` e `version` aparecem na descoberta (`initialize`/`discover`).
- `instructions` é um texto que o host recebe na conexão e costuma pôr no contexto do
  modelo. Ele diz quando usar o servidor como um todo. A docstring de cada tool diz
  quando usar aquela tool específica.

## 3. `adapters/inbound/tools.py`: o que o modelo pode fazer

Comece pelo docstring do módulo: ele resume como o modelo escolhe uma tool.

Este é o JSON que o modelo recebe de verdade no `tools/list` para uma tool (encurtei o
`outputSchema`):

```json
{
  "name": "inspect-branch-changes",
  "title": "Inspecionar mudanças da branch",
  "description": "Lê do git os commits e arquivos que um PR de head para base traria.\n\n        Somente leitura, no repositório configurado por quem roda o servidor. ...",
  "inputSchema": {
    "type": "object",
    "properties": {
      "base": {"default": "main", "description": "Branch de destino do PR, ex.: main ou develop.", "type": "string"},
      "head": {"default": "HEAD", "description": "Branch ou commit a avaliar. HEAD = branch atual.", "type": "string"}
    }
  },
  "outputSchema": {"type": "object", "properties": "…(BranchChanges)…"},
  "annotations": {"readOnlyHint": true, "openWorldHint": false}
}
```

De onde vem cada campo:

| Campo no JSON | De onde vem no Python |
|---|---|
| `name` | `@mcp.tool(name="inspect-branch-changes")` |
| `title` | `@mcp.tool(title="...")`, o rótulo para humanos na interface do host |
| `description` | a docstring da função, literalmente, com indentação e tudo |
| `inputSchema.properties.base` | `base: Annotated[str, Field(description=...)] = "main"` |
| `outputSchema` | o tipo de retorno `-> BranchChanges` (Pydantic) |
| `annotations` | `ToolAnnotations(read_only_hint=True, open_world_hint=False)` |

Algumas decisões aqui merecem atenção.

O nome diz a intenção. É `check-pr-readiness`, e não `run_rules_v2`, porque o modelo
escolhe pelo nome antes mesmo de ler a descrição.

A descrição diz o que vem depois. A frase "Use depois de inspect-branch-changes" foi o
que fez o Claude encadear as tools sem ninguém pedir.

Erros esperados viram `ToolError`. O `as_tool_error` converte `ValueError` e
`RepositoryError` em `ToolError`. Sem isso, o SDK trata a exceção como crash, e o modelo
recebe só "Error executing tool check-pr-readiness", sem saber o que corrigir. Foi assim
até a versão 1.0; hoje o teste
`test_invalid_arguments_reach_the_model_as_a_readable_error` cobre o caso.

A `inspect-branch-changes` só é registrada se houver repositório
(`if not use_cases.has_repository: return`). O cliente descobre o que existe pelo
`tools/list`, e o Cloud Run nunca anuncia uma tool que não funcionaria lá.

## 4. `adapters/inbound/resources.py`: contexto somente leitura

| URI | Tipo | Conteúdo |
|---|---|---|
| `repo://engineering-guidelines` | estático | regras R1..R6 e o porquê de cada uma |
| `devbrain://server/guide` | estático | manual do servidor: tools, resources, prompts e limites |
| `devbrain://repository/overview` | estático, só com repositório | branch atual, branches e últimos 10 commits |
| `devbrain://repository/commits/{sha}` | template | um commit e os arquivos que ele tocou |

Qual a diferença entre resource e tool? Quem decide ler um resource é o host ou o
usuário: anexar, citar com `@`, abrir num painel. Chamar uma tool é decisão do modelo.
Na prática a linha é menos nítida, porque alguns hosts dão ao modelo uma ferramenta
para ler resources. No Claude Code, ela se chama `ReadMcpResourceTool`.

A URI com `{sha}` é um template: aparece em `resources/templates/list`, não em
`resources/list`, e o host preenche o parâmetro. O SDK aplica `ResourceSecurity` aos
parâmetros (bloqueia `..`, caminho absoluto e byte nulo), e o adapter git ainda exige
que o SHA seja hexadecimal.

Para erros, os resources levantam `ResourceError`, que vira um erro de protocolo com a
mensagem. Qualquer outra exceção vira um erro genérico.

E por que as regras têm ID? A tool devolve `checks` com `rule: "R4"`, e o resource
explica a R4. O modelo junta os dois, o resultado da tool e a justificativa do
resource, e a resposta fica citável. No Antigravity, isso aparece como uma tabela de
R1 a R5 com o status de cada uma.

## 5. `adapters/inbound/prompts.py`: workflows que o usuário escolhe

- `review-feature(summary)`: devolve um texto simples.
- `review-branch(base, head)`: devolve duas mensagens. A primeira é um passo a passo;
  a segunda é um `EmbeddedResource` com as diretrizes. O prompt já leva o contexto junto.

No Claude Code, o prompt vira o comando `/mcp__devbrain__review-branch main <branch>`.
Um prompt não executa nada sozinho. Ele orienta o modelo, que continua chamando as
tools e pedindo aprovação como sempre.

## 6. `application/`: portas e casos de uso

- `ports.py` define `RepositoryPort` e `EngineeringGuidelinesPort` como `Protocol`.
  Trocar o git local pela API do GitHub é escrever outro adapter que cumpra a porta.
  Tools, casos de uso e domínio não mudam.
- `RepositoryError` mora na aplicação, porque adapters de saída a levantam e adapters
  de entrada a traduzem.
- `use_cases.py` tem dois blocos: regras puras, que funcionam em qualquer lugar, e
  repositório, que exige o adapter git. `inspect_branch_changes` busca 101 commits para
  saber se precisa marcar `truncated`.

## 7. `adapters/outbound/git_repository.py`: o arquivo de segurança

O docstring lista as cinco defesas. Vale parar em cada linha desta tabela:

| Linha de código | Ataque que ela impede |
|---|---|
| caminho só via `DEVBRAIN_REPO_PATH` | modelo pedindo para ler `~/.ssh` ou outro repositório |
| `subprocess.run([...])`, sem `shell=True` | injeção de comando com `;`, `&&`, `$(...)` |
| `SAFE_REF` não aceita `-` no início | `--output=/tmp/x` virando opção do git |
| `--end-of-options` no `rev-parse` | segunda barreira contra o mesmo ataque |
| `core.fsmonitor=false` | `.git/config` malicioso executando um programa no `git status` |
| `GIT_OPTIONAL_LOCKS=0` | o servidor "somente leitura" escrevendo `index.lock` |
| `--no-ext-diff --no-textconv` | drivers de diff externos configurados no repositório |
| timeout de 10 s, limites de 100 commits e 500 arquivos | servidor travado ou resposta gigante no contexto do modelo |

Repare também nos dois pontos e nos três pontos. `git log base..head` lista os commits
que estão em head e não em base, ou seja, o que o PR traria. `git diff base...head`
compara a partir do merge-base, como a aba "Files changed" do GitHub, e ignora o que
mudou só em base.

O `CommitInfo` não tem autor nem e-mail. A interface MCP expõe só o que a regra
precisa, e nada além.

## 8. `domain/`: a regra pura

- `files.py` responde "o que é este caminho?": é teste (Python, Go, JS/TS), é doc, é
  contrato público (`api`, `schema`, `cmd/`, `/mcp/`...), é manifesto de dependência?
- `review.py` aplica R1..R5. Cada regra gera um `RuleCheck` com evidência concreta.
  `classify_risk` devolve o risco e o motivo (`risk_reason`). Esse campo existe porque,
  num teste, o Claude reclamou que a tool dizia `medium` sem explicar por quê.
- `changes.py` transforma fatos crus do git em evidências: `has_tests`, `has_docs`,
  `non_conventional_commits`, `suggested_title`.

Quem decide se falta teste não é o modelo, é o `is_test_file`. O modelo decide quando
perguntar e como explicar a resposta. Eu acho essa a divisão mais importante do
workshop inteiro.

Os modelos Pydantic são contrato público: cada `Field(description=...)` vai para o
`outputSchema`. Quando o nome serializado divergiu do schema (`reviewFocus` contra
`review_focus`), o Claude Code recusou a resposta. Quem consome um contrato valida o
contrato.

## 9. `http.py` e `cloud_run.py`: transporte é detalhe

- `http.py`: o mesmo `mcp` de `server.py` (com repositório), servido em
  `http://127.0.0.1:8000/mcp`.
- `cloud_run.py`: outro composition root, sem repositório, escutando na `PORT` do
  Cloud Run.
- Os dois usam `stateless_http=True, json_response=True`. Cada POST carrega versão e
  capabilities (spec 2026-07-28) e recebe um JSON simples, sem sessão, e por isso o
  Cloud Run pode subir quantas instâncias quiser.

## 10. Os testes como documentação

| Arquivo | O que prova | Precisa de |
|---|---|---|
| `test/test_domain.py` | regras R1..R5, risco, classificação de arquivos | nada |
| `test/test_git_repository.py` | adapter git e ataques de injeção | `git` |
| `test/test_server.py` | o protocolo de verdade com `Client(server)` in-process | nada de rede |
| `test/test_cloud_run.py` | porta do Cloud Run e servidor sem repositório | nada |
| `test/conftest.py` | cria um repositório git de verdade numa pasta temporária | `git` |

A fixture do `conftest.py` monta `main` e `feature/passkey`, com um commit
convencional e outro fora do padrão. Nenhum teste depende de repositório da sua
máquina.

## Exercícios

1. Crie a regra R7, "migrations exigem rollback documentado". Escreva o teste em
   `test_domain.py`, a regra em `review.py` e a linha em `static_guidelines.py`. Depois
   confira o `check` novo no Inspector.
2. Escreva um adapter novo: implemente `EngineeringGuidelinesPort` lendo o
   `CONTRIBUTING.md` do repositório configurado. Na composição, só o `server.py` muda.
3. Crie a tool `list-branches`, somente leitura, com `Field(description=...)` em cada
   argumento. Teste com `Client(server)` antes de plugar num host.
4. Tente fazer a `inspect-branch-changes` ler um arquivo fora do repositório. Qual das
   defesas bloqueou?
