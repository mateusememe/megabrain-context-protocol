"""Fixtures compartilhadas: um repositório git de verdade, criado em pasta temporária.

O repositório imita a demo: ``main`` com o código base e ``feature/passkey`` com um
commit convencional, um commit fora do padrão e nenhum teste ou documentação.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from devbrain_mcp.adapters.inbound.mcp import create_mcp_server
from devbrain_mcp.adapters.outbound.git_repository import GitRepository
from devbrain_mcp.adapters.outbound.static_guidelines import StaticEngineeringGuidelines
from devbrain_mcp.application.use_cases import DevBrainUseCases


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=Demo",
            "-c",
            "user.email=demo@example.com",
            "-c",
            "commit.gpgsign=false",
            "-C",
            str(root),
            *args,
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def write(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


@pytest.fixture
def repo_path(tmp_path: Path) -> Path:
    root = tmp_path / "demo-app"
    root.mkdir()
    git(root, "init", "--quiet", "--initial-branch=main")
    write(root, "README.md", "# Demo app\n")
    write(root, "src/api/auth.py", "def login():\n    return 'password'\n")
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "chore: initial commit")

    git(root, "switch", "--quiet", "-c", "feature/passkey")
    write(root, "src/auth/passkey.py", "def verify(challenge):\n    return True\n")
    write(root, "src/api/auth.py", "def login():\n    return 'passkey'\n")
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "feat(auth): add passkey login")
    write(root, "src/auth/passkey.py", "def verify(challenge):\n    return bool(challenge)\n")
    git(root, "commit", "--quiet", "-am", "ajustes finais")
    return root


@pytest.fixture
def repository(repo_path: Path) -> GitRepository:
    return GitRepository(repo_path)


@pytest.fixture
def local_server(repository: GitRepository):
    """Servidor como roda no laptop: regras + repositório git."""
    return create_mcp_server(DevBrainUseCases(StaticEngineeringGuidelines(), repository))


@pytest.fixture
def remote_server():
    """Servidor como roda no Cloud Run: só as regras puras."""
    return create_mcp_server(DevBrainUseCases(StaticEngineeringGuidelines()))
