"""Como o DevBrain enxerga um caminho de arquivo.

Tudo aqui é heurística sobre *texto* (o caminho), sem abrir arquivo nenhum. Por isso
as regras funcionam igual para um caminho digitado pelo usuário, um caminho vindo do
git ou um caminho inventado pelo modelo, e cabem em testes unitários de uma linha.
"""

from __future__ import annotations

from pathlib import PurePosixPath

# Áreas em que um bug custa caro: exigem testes (regra R2 das diretrizes).
RISKY_AREAS = ("auth", "payment", "security", "migration", "billing")

# Marcadores de contrato público: quem consome isso fica fora do repositório
# (clientes HTTP, usuários de CLI, agentes que chamam tools MCP). Regra R3.
PUBLIC_CONTRACT_MARKERS = ("api", "schema", "openapi", "proto", "/mcp/", "cmd/")

DEPENDENCY_MANIFESTS = (
    "go.mod",
    "go.sum",
    "pyproject.toml",
    "uv.lock",
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "cargo.toml",
    "cargo.lock",
)


def normalize(path: str) -> str:
    """Caminho em minúsculas e com ``/``, para as regras não dependerem do SO."""
    return path.strip().replace("\\", "/").lower()


def is_test_file(path: str) -> bool:
    """Reconhece convenções de teste de Python, Go, JS/TS e Java."""
    normalized = normalize(path)
    name = PurePosixPath(normalized).name
    return (
        "/test/" in f"/{normalized}"
        or "/tests/" in f"/{normalized}"
        or name.startswith("test_")
        or name.endswith(("_test.go", "_test.py"))
        or ".test." in name
        or ".spec." in name
    )


def is_doc_file(path: str) -> bool:
    """README, CHANGELOG, arquivos Markdown e tudo dentro de ``docs/``."""
    normalized = normalize(path)
    name = PurePosixPath(normalized).name
    return (
        normalized.startswith("docs/")
        or "/docs/" in normalized
        or name.startswith(("readme", "changelog"))
        or name.endswith((".md", ".mdx", ".rst"))
    )


def is_dependency_manifest(path: str) -> bool:
    return PurePosixPath(normalize(path)).name in DEPENDENCY_MANIFESTS


def touches_risky_area(path: str) -> bool:
    normalized = normalize(path)
    return not is_test_file(normalized) and any(area in normalized for area in RISKY_AREAS)


def touches_public_contract(path: str) -> bool:
    normalized = f"/{normalize(path)}"
    if is_test_file(normalized) or is_doc_file(normalized):
        return False
    return any(marker in normalized for marker in PUBLIC_CONTRACT_MARKERS)
