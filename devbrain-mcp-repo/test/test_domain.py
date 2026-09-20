import pytest

from devbrain_mcp.domain.review import analyze_changed_files, evaluate_pr_readiness


def test_domain_rejects_missing_changed_files() -> None:
    with pytest.raises(ValueError, match="changed_files"):
        evaluate_pr_readiness("feat: improve review", [], has_tests=True)


def test_domain_classifies_infrastructure_without_mcp() -> None:
    result = analyze_changed_files(["infrastructure/template.yaml"])

    assert result.areas == ["infrastructure"]
    assert result.review_focus == ["least privilege, rollback and environment drift"]
