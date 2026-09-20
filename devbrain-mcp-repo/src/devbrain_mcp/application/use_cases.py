"""Casos de uso independentes de MCP, HTTP e AWS."""

from __future__ import annotations

from devbrain_mcp.application.ports import EngineeringGuidelinesPort
from devbrain_mcp.domain.review import (
    ChangedFilesAnalysis,
    PRReadiness,
    analyze_changed_files,
    evaluate_pr_readiness,
)


class DevBrainUseCases:
    """Fachada dos casos de uso consumidos pelos adaptadores de entrada."""

    def __init__(self, guidelines: EngineeringGuidelinesPort) -> None:
        self._guidelines = guidelines

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
