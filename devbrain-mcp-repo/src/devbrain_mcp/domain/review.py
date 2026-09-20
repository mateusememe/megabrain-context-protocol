"""Regras determinísticas para avaliar mudanças de engenharia.

Este módulo não conhece MCP, HTTP, AWS nem o modo como as diretrizes são
armazenadas. Isso permite exercitar as regras diretamente em testes unitários.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

RISKY_AREAS = ("auth", "payment", "security", "migration", "billing")
CONVENTIONAL_COMMIT = re.compile(
    r"^(feat|fix|docs|refactor|test|chore|perf|build|ci)(\(.+\))?: .+", re.IGNORECASE
)


class PRReadiness(BaseModel):
    """Decisão e evidências da avaliação de um pull request."""

    ready: bool
    risk: Literal["low", "medium", "high"]
    problems: list[str]
    recommendations: list[str]


class ChangedFilesAnalysis(BaseModel):
    """Áreas afetadas e focos sugeridos para revisão."""

    areas: list[str]
    review_focus: list[str] = Field(serialization_alias="reviewFocus")


def evaluate_pr_readiness(
    title: str,
    changed_files: list[str],
    has_tests: bool,
    has_docs: bool = False,
) -> PRReadiness:
    """Aplica as regras de prontidão sem depender de transporte ou infraestrutura."""
    if len(title.strip()) < 3:
        raise ValueError("title precisa ter pelo menos 3 caracteres")
    if not changed_files:
        raise ValueError("changed_files precisa conter ao menos um arquivo")

    problems: list[str] = []
    recommendations: list[str] = []
    lower_files = [path.lower() for path in changed_files]
    touches_risky_area = any(area in path for path in lower_files for area in RISKY_AREAS)
    touches_public_contract = any("api" in path or "schema" in path for path in lower_files)

    if not CONVENTIONAL_COMMIT.match(title):
        problems.append("Título não segue Conventional Commits.")
    if touches_risky_area and not has_tests:
        problems.append("Área de alto risco alterada sem testes automatizados.")
    elif not has_tests:
        recommendations.append("Adicionar testes aumenta a confiança na entrega.")
    if touches_public_contract and not has_docs:
        problems.append("Contrato público alterado sem atualização de documentação.")
    if len(changed_files) > 20:
        recommendations.append("Considere dividir o PR para reduzir a superfície de revisão.")

    risk: Literal["low", "medium", "high"]
    if touches_risky_area:
        risk = "high"
    elif len(changed_files) > 10:
        risk = "medium"
    else:
        risk = "low"

    return PRReadiness(
        ready=not problems,
        risk=risk,
        problems=problems,
        recommendations=recommendations,
    )


def analyze_changed_files(files: list[str]) -> ChangedFilesAnalysis:
    """Classifica arquivos sem acessar o sistema de arquivos do host."""
    if not files:
        raise ValueError("files precisa conter ao menos um arquivo")
    if len(files) > 100:
        raise ValueError("files aceita no máximo 100 itens")

    areas: set[str] = set()
    review_focus: set[str] = set()

    for file in (path.lower() for path in files):
        if "auth" in file or "security" in file:
            areas.add("security")
            review_focus.add("authorization, validation and secret handling")
        if "api" in file or "controller" in file or "route" in file:
            areas.add("api")
            review_focus.add("contract compatibility and error handling")
        if "test" in file or "spec" in file:
            areas.add("tests")
        if "infra" in file or "terraform" in file or "template.yaml" in file:
            areas.add("infrastructure")
            review_focus.add("least privilege, rollback and environment drift")

    if not areas:
        areas.add("application")

    return ChangedFilesAnalysis(areas=sorted(areas), review_focus=sorted(review_focus))
