"""Prompts MCP: templates de workflow que o **usuário** escolhe explicitamente.

No Claude Code um prompt vira o comando ``/mcp__devbrain__review-branch``; em outros
hosts aparece num menu. O servidor devolve *mensagens prontas*, às vezes com um
resource embutido, e o host as coloca na conversa. O prompt não executa nada: ele
orienta o modelo a usar as tools na ordem certa.
"""

from __future__ import annotations

from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver import UserMessage
from mcp.types import EmbeddedResource, TextResourceContents
from pydantic import Field

from devbrain_mcp.application.use_cases import DevBrainUseCases

REVIEW_BRANCH_STEPS = """Revise a branch `{head}` como se fosse abrir um PR para `{base}`.

Siga estes passos e mostre a evidência de cada um:

1. Chame `inspect-branch-changes` com base="{base}" e head="{head}".
2. Chame `check-pr-readiness` usando o `suggested_title` (ou um título melhor em
   Conventional Commits), a lista de `files[].path`, `has_tests` e `has_docs`
   devolvidos no passo 1.
3. Chame `analyze-changed-files` com os mesmos caminhos.
4. Responda em português com:
   - **Veredito**: pronto ou não pronto, e o risco;
   - **Evidências**: uma linha por regra (R1..R5) citando o `detail` do check;
   - **Commits**: quantos, e quais fogem do padrão;
   - **Foco de revisão**: o que um revisor humano deve olhar primeiro;
   - **Próximos passos**: no máximo três ações concretas.

Não invente fatos que as tools não devolveram. As diretrizes do time estão abaixo."""


def register_prompts(mcp: MCPServer, use_cases: DevBrainUseCases) -> None:
    """Registra prompts sem confundi-los com seleção autônoma de tools."""

    @mcp.prompt(name="review-feature", title="Revisar feature descrita em texto")
    def review_feature(
        summary: Annotated[str, Field(description="O que a feature faz, em uma frase.")],
    ) -> str:
        """Prepara uma revisão de feature usando as convenções e tools DevBrain."""
        return use_cases.build_review_prompt(summary)

    if not use_cases.has_repository:
        return

    @mcp.prompt(name="review-branch", title="Revisar branch real com evidências do git")
    def review_branch(
        base: Annotated[str, Field(description="Branch de destino, ex.: main.")] = "main",
        head: Annotated[str, Field(description="Branch a revisar. HEAD = atual.")] = "HEAD",
    ) -> list[UserMessage]:
        """Workflow completo: inspeciona a branch, aplica as regras e gera o parecer."""
        guidelines = EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri="repo://engineering-guidelines",
                mime_type="text/markdown",
                text=use_cases.get_engineering_guidelines(),
            ),
        )
        return [
            UserMessage(REVIEW_BRANCH_STEPS.format(base=base, head=head)),
            UserMessage(guidelines),
        ]
