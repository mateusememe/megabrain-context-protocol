"""O que mudou entre duas referências de um repositório.

O adapter git (``adapters/outbound/git_repository.py``) só *coleta* fatos crus:
commits e arquivos. A interpretação (tem teste? tem doc? qual título sugerir?) fica
aqui, no domínio, e por isso dá para testar sem git e sem MCP.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from devbrain_mcp.domain.files import is_dependency_manifest, is_doc_file, is_test_file
from devbrain_mcp.domain.review import is_conventional

FileStatus = Literal["added", "modified", "deleted", "renamed", "other"]


class CommitInfo(BaseModel):
    """Um commit, sem autor nem e-mail: o servidor não expõe dados pessoais à toa."""

    sha: str = Field(description="SHA curto do commit.")
    date: str = Field(description="Data do commit (AAAA-MM-DD).")
    subject: str = Field(description="Primeira linha da mensagem.")
    conventional: bool = Field(description="true se o assunto segue Conventional Commits.")


class FileChange(BaseModel):
    """Um arquivo alterado e o tamanho da alteração em linhas."""

    path: str
    status: FileStatus
    additions: int = Field(description="Linhas adicionadas (0 para binários).")
    deletions: int = Field(description="Linhas removidas (0 para binários).")


class CommitDetails(BaseModel):
    """Um commit específico e os arquivos que ele tocou."""

    commit: CommitInfo
    body: str = Field(description="Corpo da mensagem, sem a primeira linha.")
    files: list[FileChange]


class BranchChanges(BaseModel):
    """Evidências reais de uma branch, prontas para alimentar check-pr-readiness."""

    repository: str = Field(description="Nome da pasta do repositório analisado.")
    base: str = Field(description="Referência de comparação, ex.: main.")
    head: str = Field(description="Referência analisada, ex.: HEAD ou nome da branch.")
    commits: list[CommitInfo] = Field(description="Commits em head que não estão em base.")
    files: list[FileChange] = Field(description="Arquivos alterados desde o merge-base.")
    total_additions: int
    total_deletions: int
    has_tests: bool = Field(description="Algum arquivo alterado é de teste.")
    has_docs: bool = Field(description="Algum arquivo alterado é documentação.")
    dependency_changes: list[str] = Field(description="Manifestos de dependência alterados.")
    non_conventional_commits: list[str] = Field(
        description="SHAs de commits cujo assunto não segue Conventional Commits."
    )
    suggested_title: str = Field(
        description="Título sugerido para o PR: o primeiro commit feat/fix da branch."
    )
    truncated: bool = Field(description="true se a lista de commits foi cortada no limite.")


def suggest_title(commits: list[CommitInfo]) -> str:
    """Escolhe o commit mais antigo do tipo feat ou fix; senão, o mais antigo de todos.

    ``commits`` vem do mais novo para o mais antigo, como em ``git log``.
    """
    oldest_first = list(reversed(commits))
    for commit in oldest_first:
        if commit.subject.lower().startswith(("feat", "fix")):
            return commit.subject
    return oldest_first[0].subject if oldest_first else ""


def summarize_branch(
    repository: str,
    base: str,
    head: str,
    commits: list[CommitInfo],
    files: list[FileChange],
    truncated: bool = False,
) -> BranchChanges:
    """Transforma fatos crus do git em evidências que as regras do DevBrain entendem."""
    paths = [change.path for change in files]
    return BranchChanges(
        repository=repository,
        base=base,
        head=head,
        commits=commits,
        files=files,
        total_additions=sum(change.additions for change in files),
        total_deletions=sum(change.deletions for change in files),
        has_tests=any(is_test_file(path) for path in paths),
        has_docs=any(is_doc_file(path) for path in paths),
        dependency_changes=sorted(path for path in paths if is_dependency_manifest(path)),
        non_conventional_commits=[c.sha for c in commits if not is_conventional(c.subject)],
        suggested_title=suggest_title(commits),
        truncated=truncated,
    )


def make_commit(sha: str, date: str, subject: str) -> CommitInfo:
    return CommitInfo(sha=sha, date=date, subject=subject, conventional=is_conventional(subject))
