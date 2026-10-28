"""Regras puras: nenhum MCP, nenhum git, nenhuma rede. Rodam em milissegundos."""

import pytest

from devbrain_mcp.domain.changes import FileChange, make_commit, summarize_branch
from devbrain_mcp.domain.files import is_doc_file, is_test_file, touches_public_contract
from devbrain_mcp.domain.review import analyze_changed_files, evaluate_pr_readiness


def failed_rules(result) -> list[str]:
    return [check.rule for check in result.checks if not check.passed]


def test_domain_rejects_missing_changed_files() -> None:
    with pytest.raises(ValueError, match="changed_files"):
        evaluate_pr_readiness("feat: improve review", [], has_tests=True)


def test_domain_classifies_infrastructure_without_mcp() -> None:
    result = analyze_changed_files(["infrastructure/template.yaml"])

    assert result.areas == ["infrastructure"]
    assert result.review_focus == ["least privilege, rollback and environment drift"]


def test_passkey_change_without_tests_or_docs_is_blocked() -> None:
    result = evaluate_pr_readiness(
        "feat(auth): add passkey login",
        ["src/auth/passkey.py", "src/api/auth.py"],
        has_tests=False,
        has_docs=False,
    )

    assert result.ready is False
    assert result.risk == "high"
    assert result.risk_reason == (
        "Área de alto risco alterada: src/api/auth.py, src/auth/passkey.py."
    )
    assert failed_rules(result) == ["R2", "R3"]
    assert [check.rule for check in result.checks] == ["R1", "R2", "R3", "R4", "R5"]


def test_large_go_branch_with_tests_and_docs_is_ready_with_recommendations() -> None:
    files = [f"internal/service/file_{index}.go" for index in range(20)] + [
        "internal/service/doctor_test.go",
        "internal/mcp/server.go",
        "cmd/quality-gate/main.go",
        "README.md",
        "go.mod",
    ]

    result = evaluate_pr_readiness(
        "feat(mcp): add check_environment tool", files, has_tests=True, has_docs=True
    )

    assert result.ready is True
    assert result.risk == "medium"
    assert result.risk_reason.startswith("Contrato público alterado: cmd/quality-gate/main.go")
    assert result.problems == []
    assert failed_rules(result) == ["R4", "R5"]
    assert len(result.recommendations) == 2


def test_title_outside_conventional_commits_fails_r1() -> None:
    result = evaluate_pr_readiness("ajustes finais", ["src/app.py"], has_tests=True)

    assert result.ready is False
    assert failed_rules(result) == ["R1"]


@pytest.mark.parametrize(
    "path",
    ["test/test_server.py", "internal/service/doctor_test.go", "web/app.spec.ts", "tests/x.py"],
)
def test_test_files_are_recognized_across_languages(path: str) -> None:
    assert is_test_file(path)


def test_docs_and_tests_are_not_public_contracts() -> None:
    assert is_doc_file("docs/api.md")
    assert not touches_public_contract("docs/api.md")
    assert not touches_public_contract("internal/mcp/server_test.go")
    assert touches_public_contract("internal/mcp/server.go")


def test_summarize_branch_derives_evidence_from_raw_git_facts() -> None:
    commits = [
        make_commit("c3", "2026-10-03", "ajustes finais"),
        make_commit("b2", "2026-10-02", "feat(auth): add passkey login"),
        make_commit("a1", "2026-10-01", "chore: bump deps"),
    ]
    files = [
        FileChange(path="src/auth/passkey.py", status="added", additions=10, deletions=0),
        FileChange(path="pyproject.toml", status="modified", additions=1, deletions=1),
    ]

    result = summarize_branch("demo", "main", "HEAD", commits, files)

    assert result.suggested_title == "feat(auth): add passkey login"
    assert result.non_conventional_commits == ["c3"]
    assert result.has_tests is False
    assert result.has_docs is False
    assert result.dependency_changes == ["pyproject.toml"]
    assert (result.total_additions, result.total_deletions) == (11, 1)


def test_docs_only_change_is_low_risk_with_review_focus() -> None:
    result = evaluate_pr_readiness("docs(adr): add ADRs", ["docs/adr/0001.md"], has_tests=False)
    analysis = analyze_changed_files(["docs/adr/0001.md"])

    assert (result.ready, result.risk) == (True, "low")
    assert result.recommendations == []
    assert analysis.review_focus == ["docs match the behavior and are complete, not drafts"]
