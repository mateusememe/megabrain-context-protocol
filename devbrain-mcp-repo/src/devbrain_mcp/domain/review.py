"""Regras determinísticas para avaliar mudanças de engenharia.

Este módulo é o "cérebro" do DevBrain e **não sabe que MCP existe**: não importa SDK,
não conhece HTTP, git nem nuvem. Ele recebe dados simples e devolve modelos Pydantic.

Por que isso importa numa aula de MCP?

- O modelo de linguagem *decide quando* chamar uma tool; quem *decide o resultado* é
  este código, determinístico e testável. O LLM não "acha" que falta teste: a regra R2
  diz que falta, e o modelo cita a evidência.
- Os modelos Pydantic de saída viram o ``outputSchema`` das tools. Cada campo aqui é
  parte do contrato público que o host valida (veja o bug do ``reviewFocus`` no
  roteiro de testes).
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from devbrain_mcp.domain.files import (
    is_dependency_manifest,
    is_doc_file,
    is_test_file,
    touches_public_contract,
    touches_risky_area,
)

CONVENTIONAL_COMMIT = re.compile(
    r"^(feat|fix|docs|refactor|test|chore|perf|build|ci|style|revert)(\(.+\))?!?: .+",
    re.IGNORECASE,
)
LARGE_PR_FILES = 20
MEDIUM_PR_FILES = 10
MAX_FILES = 300

Risk = Literal["low", "medium", "high"]


class RuleCheck(BaseModel):
    """Uma regra das diretrizes aplicada à mudança, com o motivo do resultado."""

    rule: str = Field(description="Identificador da regra em repo://engineering-guidelines.")
    passed: bool = Field(description="false quando a regra encontrou um problema.")
    detail: str = Field(description="Evidência concreta que o modelo pode citar.")


class PRReadiness(BaseModel):
    """Decisão e evidências da avaliação de um pull request."""

    ready: bool = Field(description="true somente se nenhuma regra bloqueante falhou.")
    risk: Risk = Field(description="Risco estimado pelo tipo e pelo tamanho da mudança.")
    risk_reason: str = Field(description="Por que o risco ficou neste nível.")
    problems: list[str] = Field(description="Bloqueios: precisam ser resolvidos antes do PR.")
    recommendations: list[str] = Field(description="Sugestões que não bloqueiam o PR.")
    checks: list[RuleCheck] = Field(description="Cada regra avaliada, na ordem R1..R5.")


class ChangedFilesAnalysis(BaseModel):
    """Áreas afetadas e focos sugeridos para revisão."""

    areas: list[str] = Field(description="Áreas técnicas tocadas pela mudança.")
    review_focus: list[str] = Field(description="O que um revisor humano deve olhar primeiro.")


def is_conventional(title: str) -> bool:
    return bool(CONVENTIONAL_COMMIT.match(title.strip()))


def evaluate_pr_readiness(
    title: str,
    changed_files: list[str],
    has_tests: bool,
    has_docs: bool = False,
) -> PRReadiness:
    """Aplica as regras R1..R5 de ``repo://engineering-guidelines``.

    Regras que falham com ``problems`` bloqueiam o PR; ``recommendations`` só orientam.
    Erros de entrada levantam ``ValueError`` com uma mensagem pensada para o *modelo*
    ler e corrigir a própria chamada.
    """
    if len(title.strip()) < 3:
        raise ValueError("title precisa ter pelo menos 3 caracteres.")
    if not changed_files:
        raise ValueError(
            "changed_files precisa conter ao menos um arquivo. "
            "Dica: use inspect-branch-changes para obter a lista real do git."
        )
    if len(changed_files) > MAX_FILES:
        raise ValueError(f"changed_files aceita no máximo {MAX_FILES} itens.")

    risky = sorted(path for path in changed_files if touches_risky_area(path))
    contracts = sorted(path for path in changed_files if touches_public_contract(path))
    manifests = sorted(path for path in changed_files if is_dependency_manifest(path))

    checks: list[RuleCheck] = []
    problems: list[str] = []
    recommendations: list[str] = []

    # R1: título no formato Conventional Commits.
    if is_conventional(title):
        checks.append(RuleCheck(rule="R1", passed=True, detail=f'Título "{title}" é válido.'))
    else:
        problems.append("Título não segue Conventional Commits.")
        checks.append(
            RuleCheck(
                rule="R1",
                passed=False,
                detail=f'"{title}" não começa com tipo(escopo): descrição, ex.: feat(auth): ...',
            )
        )

    # R2: área de alto risco exige testes.
    if risky and not has_tests:
        problems.append("Área de alto risco alterada sem testes automatizados.")
        checks.append(
            RuleCheck(rule="R2", passed=False, detail=f"Sem testes para: {', '.join(risky)}.")
        )
    else:
        code_changed = any(not is_doc_file(path) for path in changed_files)
        if not has_tests and code_changed:
            recommendations.append("Adicionar testes aumenta a confiança na entrega.")
        detail = (
            f"Área de risco com testes: {', '.join(risky)}."
            if risky
            else "Nenhuma área de alto risco (auth, payment, security, migration, billing)."
        )
        checks.append(RuleCheck(rule="R2", passed=True, detail=detail))

    # R3: contrato público exige documentação.
    if contracts and not has_docs:
        problems.append("Contrato público alterado sem atualização de documentação.")
        checks.append(
            RuleCheck(rule="R3", passed=False, detail=f"Sem docs para: {', '.join(contracts)}.")
        )
    else:
        detail = (
            f"Contrato público com docs atualizadas: {', '.join(contracts)}."
            if contracts
            else "Nenhum contrato público (API, schema, CLI, tools MCP) alterado."
        )
        checks.append(RuleCheck(rule="R3", passed=True, detail=detail))

    # R4: PR grande deve ser dividido (recomendação, não bloqueio).
    if len(changed_files) > LARGE_PR_FILES:
        recommendations.append("Considere dividir o PR para reduzir a superfície de revisão.")
    checks.append(
        RuleCheck(
            rule="R4",
            passed=len(changed_files) <= LARGE_PR_FILES,
            detail=f"{len(changed_files)} arquivo(s) alterado(s); limite sugerido: "
            f"{LARGE_PR_FILES}.",
        )
    )

    # R5: dependências alteradas pedem revisão de changelog e licença.
    if manifests:
        recommendations.append(
            "Dependências alteradas: revise changelog, licença e vulnerabilidades "
            f"({', '.join(manifests)})."
        )
    checks.append(
        RuleCheck(
            rule="R5",
            passed=not manifests,
            detail=(
                f"Manifestos alterados: {', '.join(manifests)}."
                if manifests
                else "Nenhum manifesto de dependência alterado."
            ),
        )
    )

    risk, risk_reason = classify_risk(risky, contracts, manifests, len(changed_files))

    return PRReadiness(
        ready=not problems,
        risk=risk,
        risk_reason=risk_reason,
        problems=problems,
        recommendations=recommendations,
        checks=checks,
    )


def classify_risk(
    risky: list[str], contracts: list[str], manifests: list[str], file_count: int
) -> tuple[Risk, str]:
    """Primeiro motivo que se aplica, do mais grave para o mais leve."""
    if risky:
        return "high", f"Área de alto risco alterada: {', '.join(risky)}."
    if contracts:
        return "medium", f"Contrato público alterado: {', '.join(contracts)}."
    if manifests:
        return "medium", f"Dependências alteradas: {', '.join(manifests)}."
    if file_count > MEDIUM_PR_FILES:
        return "medium", f"{file_count} arquivos alterados (acima de {MEDIUM_PR_FILES})."
    return "low", "Nenhum gatilho de risco: área comum, sem contrato público nem dependências."


def analyze_changed_files(files: list[str]) -> ChangedFilesAnalysis:
    """Classifica arquivos por área sem acessar o sistema de arquivos do host."""
    if not files:
        raise ValueError("files precisa conter ao menos um arquivo.")
    if len(files) > MAX_FILES:
        raise ValueError(f"files aceita no máximo {MAX_FILES} itens.")

    areas: set[str] = set()
    review_focus: set[str] = set()

    for file in files:
        if touches_risky_area(file):
            areas.add("security")
            review_focus.add("authorization, validation and secret handling")
        if touches_public_contract(file):
            areas.add("api")
            review_focus.add("contract compatibility and error handling")
        if is_test_file(file):
            areas.add("tests")
            review_focus.add("tests cover failure paths, not only the happy path")
        if is_doc_file(file):
            areas.add("docs")
            review_focus.add("docs match the behavior and are complete, not drafts")
        if is_dependency_manifest(file):
            areas.add("dependencies")
            review_focus.add("dependency changelog, license and vulnerabilities")
        lowered = file.lower()
        if "infra" in lowered or "terraform" in lowered or "dockerfile" in lowered:
            areas.add("infrastructure")
            review_focus.add("least privilege, rollback and environment drift")

    if not areas:
        areas.add("application")

    return ChangedFilesAnalysis(areas=sorted(areas), review_focus=sorted(review_focus))
