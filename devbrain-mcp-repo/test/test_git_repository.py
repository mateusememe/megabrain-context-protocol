"""Adapter git contra um repositório real em pasta temporária."""

from pathlib import Path

import pytest

from devbrain_mcp.adapters.outbound.git_repository import GitRepository
from devbrain_mcp.application.ports import RepositoryError


def test_reads_branch_commits_newest_first(repository: GitRepository) -> None:
    commits = repository.commits_between("main", "feature/passkey", limit=10)

    assert [commit.subject for commit in commits] == [
        "ajustes finais",
        "feat(auth): add passkey login",
    ]
    assert [commit.conventional for commit in commits] == [False, True]


def test_changed_files_compare_from_merge_base(repository: GitRepository) -> None:
    files = {change.path: change for change in repository.changed_files("main", "HEAD")}

    assert set(files) == {"src/api/auth.py", "src/auth/passkey.py"}
    assert files["src/auth/passkey.py"].status == "added"
    assert files["src/api/auth.py"].status == "modified"
    assert (files["src/api/auth.py"].additions, files["src/api/auth.py"].deletions) == (1, 1)


def test_repository_name_hides_the_full_path(repository: GitRepository) -> None:
    assert repository.name == "demo-app"
    assert repository.current_branch() == "feature/passkey"
    assert repository.local_branches() == ["feature/passkey", "main"]


@pytest.mark.parametrize("ref", ["--output=/tmp/pwned", "main;rm -rf /", "../../etc", "a..b"])
def test_rejects_refs_that_could_become_git_options(repository: GitRepository, ref: str) -> None:
    with pytest.raises(RepositoryError, match="Referência inválida"):
        repository.commits_between(ref, "HEAD", limit=10)


def test_unknown_ref_explains_which_branches_exist(repository: GitRepository) -> None:
    with pytest.raises(RepositoryError, match="Branches locais: feature/passkey, main"):
        repository.changed_files("develop", "HEAD")


def test_commit_details_lists_touched_files(repository: GitRepository) -> None:
    sha = repository.commits_between("main", "HEAD", limit=10)[1].sha

    details = repository.commit_details(sha)

    assert details.commit.subject == "feat(auth): add passkey login"
    assert {change.path for change in details.files} == {
        "src/api/auth.py",
        "src/auth/passkey.py",
    }


def test_commit_details_rejects_non_hex_sha(repository: GitRepository) -> None:
    with pytest.raises(RepositoryError, match="SHA válido"):
        repository.commit_details("HEAD")


def test_folder_without_git_is_reported(tmp_path: Path) -> None:
    with pytest.raises(RepositoryError, match="não é um repositório git"):
        GitRepository(tmp_path)
