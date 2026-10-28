"""Casos de uso: o que o DevBrain sabe fazer, independente de MCP, HTTP e nuvem.

Os adapters de entrada (tools, resources e prompts MCP) só traduzem protocolo para
chamadas desta fachada. Se amanhã o DevBrain ganhar uma CLI ou uma API REST, ela
chama exatamente os mesmos métodos.
"""

from __future__ import annotations

from devbrain_mcp.application.ports import (
    EngineeringGuidelinesPort,
    RepositoryError,
    RepositoryPort,
)
from devbrain_mcp.domain.changes import BranchChanges, CommitDetails, summarize_branch
from devbrain_mcp.domain.review import (
    ChangedFilesAnalysis,
    PRReadiness,
    analyze_changed_files,
    evaluate_pr_readiness,
)

MAX_BRANCH_COMMITS = 100
OVERVIEW_COMMITS = 10


class DevBrainUseCases:
    """Fachada dos casos de uso consumidos pelos adaptadores de entrada."""

    def __init__(
        self,
        guidelines: EngineeringGuidelinesPort,
        repository: RepositoryPort | None = None,
    ) -> None:
        self._guidelines = guidelines
        self._repository = repository

    # --- Regras puras: funcionam em qualquer lugar, inclusive no Cloud Run ---------

    def check_pr_readiness(
        self,
        title: str,
        changed_files: list[str],
        has_tests: bool,
        has_docs: bool = False,
    ) -> PRReadiness:
        return evaluate_pr_readiness(title, changed_files, has_tests, has_docs)

    def analyze_changed_files(self, files: list[str]) -> ChangedFilesAnalysis:
        return analyze_changed_files(files)

    def get_engineering_guidelines(self) -> str:
        return self._guidelines.read()

    def build_review_prompt(self, summary: str) -> str:
        return (
            f"Revise esta mudança: {summary}\n\n"
            "Use os recursos e ferramentas DevBrain disponíveis quando forem relevantes. "
            "Aponte riscos, evidências faltantes e uma decisão final de prontidão."
        )

    # --- Repositório real: só existe quando o servidor roda perto do código --------

    @property
    def has_repository(self) -> bool:
        return self._repository is not None

    def _require_repository(self) -> RepositoryPort:
        if self._repository is None:
            raise RepositoryError(
                "Este servidor não tem repositório configurado. "
                "Rode localmente com DEVBRAIN_REPO_PATH apontando para um repositório git."
            )
        return self._repository

    def inspect_branch_changes(self, base: str, head: str) -> BranchChanges:
        repository = self._require_repository()
        commits = repository.commits_between(base, head, MAX_BRANCH_COMMITS + 1)
        files = repository.changed_files(base, head)
        if not commits and not files:
            raise RepositoryError(
                f"Nenhuma diferença entre {base} e {head}. "
                f"Branches locais: {', '.join(repository.local_branches())}."
            )
        return summarize_branch(
            repository=repository.name,
            base=base,
            head=head,
            commits=commits[:MAX_BRANCH_COMMITS],
            files=files,
            truncated=len(commits) > MAX_BRANCH_COMMITS,
        )

    def repository_overview(self) -> str:
        repository = self._require_repository()
        branch = repository.current_branch()
        branches = repository.local_branches()
        commits = repository.recent_commits("HEAD", OVERVIEW_COMMITS)
        lines = [
            f"# Repositório `{repository.name}`",
            "",
            f"- Branch atual: `{branch}`",
            f"- Branches locais: {', '.join(f'`{name}`' for name in branches)}",
            "",
            f"## Últimos {len(commits)} commits em `{branch}`",
            "",
        ]
        lines += [
            f"- `{c.sha}` {c.date} {c.subject}{'' if c.conventional else '  ⚠ não convencional'}"
            for c in commits
        ]
        lines += [
            "",
            "Detalhes de um commit: leia `devbrain://repository/commits/{sha}`.",
            "Mudanças de uma branch: chame a tool `inspect-branch-changes`.",
        ]
        return "\n".join(lines) + "\n"

    def commit_details(self, sha: str) -> CommitDetails:
        return self._require_repository().commit_details(sha)
