"""Portas: o que a aplicação precisa do mundo externo, sem saber *como* é feito.

Uma porta é só um ``Protocol``. Hoje as diretrizes vêm de uma string em memória e o
repositório vem do ``git`` local; amanhã podem vir de uma API do GitHub ou de um
banco. Os casos de uso e as tools MCP não mudam uma linha quando o adapter muda.
"""

from __future__ import annotations

from typing import Protocol

from devbrain_mcp.domain.changes import CommitDetails, CommitInfo, FileChange


class RepositoryError(Exception):
    """Falha prevista ao ler o repositório: referência inexistente, git ausente etc.

    A mensagem é escrita para o modelo ler e corrigir a própria chamada.
    """


class EngineeringGuidelinesPort(Protocol):
    """Fonte read-only das diretrizes que o servidor expõe como resource."""

    def read(self) -> str:
        """Retorna as diretrizes de engenharia vigentes, em Markdown."""


class RepositoryPort(Protocol):
    """Leitura somente-leitura de UM repositório escolhido por quem roda o servidor."""

    @property
    def name(self) -> str:
        """Nome curto do repositório (a pasta), sem expor o caminho completo."""

    def current_branch(self) -> str: ...

    def local_branches(self) -> list[str]: ...

    def recent_commits(self, ref: str, limit: int) -> list[CommitInfo]: ...

    def commits_between(self, base: str, head: str, limit: int) -> list[CommitInfo]:
        """Commits alcançáveis por ``head`` e não por ``base`` (``git log base..head``)."""

    def changed_files(self, base: str, head: str) -> list[FileChange]:
        """Arquivos alterados desde o merge-base (``git diff base...head``)."""

    def commit_details(self, sha: str) -> CommitDetails: ...
