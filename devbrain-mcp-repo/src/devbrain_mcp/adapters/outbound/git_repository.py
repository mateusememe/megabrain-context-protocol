"""Adapter de saída: lê UM repositório git local, somente leitura.

Este é o arquivo mais importante para discutir **segurança de servidores MCP**. O
modelo de linguagem escolhe os argumentos das tools; trate cada argumento como
entrada não confiável, exatamente como num endpoint HTTP público.

Defesas usadas aqui, de fora para dentro:

1. **Fronteira definida por quem roda o servidor.** O caminho do repositório vem de
   ``DEVBRAIN_REPO_PATH`` (ou da pasta atual), nunca de um argumento de tool. O modelo
   não consegue pedir "leia /etc ou ~/.ssh".
2. **Nada de shell.** ``subprocess.run`` recebe uma lista de argumentos; não existe
   string de comando para injetar ``; rm -rf``.
3. **Referências validadas.** ``base``/``head``/``sha`` passam por regex e não podem
   começar com ``-`` (senão ``--output=/tmp/x`` viraria uma *opção* do git).
4. **Git sem efeitos colaterais.** ``GIT_OPTIONAL_LOCKS=0`` evita escrever no índice,
   ``core.fsmonitor=false`` impede que um ``.git/config`` malicioso execute programas,
   ``--no-ext-diff``/``--no-textconv`` desligam drivers externos de diff.
5. **Limites.** Timeout por comando, teto de commits e de arquivos.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from devbrain_mcp.application.ports import RepositoryError
from devbrain_mcp.domain.changes import (
    CommitDetails,
    CommitInfo,
    FileChange,
    FileStatus,
    make_commit,
)

GIT_TIMEOUT_SECONDS = 10
MAX_FILES = 500
SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/~^-]{0,119}$")
SAFE_SHA = re.compile(r"^[0-9a-fA-F]{4,40}$")
FIELD_SEPARATOR = "\x1f"  # caractere de controle que não aparece em mensagens de commit
STATUS_BY_LETTER: dict[str, FileStatus] = {
    "A": "added",
    "M": "modified",
    "D": "deleted",
    "R": "renamed",
}


class GitRepository:
    """Implementa ``RepositoryPort`` chamando o executável ``git``."""

    def __init__(self, path: str | Path) -> None:
        candidate = Path(path).expanduser()
        if not candidate.is_dir():
            raise RepositoryError(f"DEVBRAIN_REPO_PATH não é uma pasta: {candidate}")
        self._root = candidate
        try:
            # Sobe até a raiz do repositório, mesmo que o caminho aponte para uma subpasta.
            self._root = Path(self._git("rev-parse", "--show-toplevel").strip())
        except RepositoryError as error:
            raise RepositoryError(f"{candidate} não é um repositório git: {error}") from None

    @property
    def name(self) -> str:
        return self._root.name

    # --- Consultas -------------------------------------------------------------

    def current_branch(self) -> str:
        return self._git("rev-parse", "--abbrev-ref", "HEAD").strip()

    def local_branches(self) -> list[str]:
        output = self._git("for-each-ref", "--format=%(refname:short)", "refs/heads")
        return sorted(line for line in output.splitlines() if line)

    def recent_commits(self, ref: str, limit: int) -> list[CommitInfo]:
        self._resolve(ref)
        return self._log(f"--max-count={limit}", ref)

    def commits_between(self, base: str, head: str, limit: int) -> list[CommitInfo]:
        self._resolve(base)
        self._resolve(head)
        # Dois pontos: commits de head que ainda não estão em base (o que o PR traria).
        return self._log(f"--max-count={limit}", f"{base}..{head}")

    def changed_files(self, base: str, head: str) -> list[FileChange]:
        self._resolve(base)
        self._resolve(head)
        # Três pontos: diff a partir do merge-base, exatamente o que a aba
        # "Files changed" de um PR mostra, ignorando o que mudou só em base.
        return self._diff_files("diff", f"{base}...{head}")

    def commit_details(self, sha: str) -> CommitDetails:
        if not SAFE_SHA.match(sha):
            raise RepositoryError(f"'{sha}' não é um SHA válido (4 a 40 caracteres hex).")
        self._resolve(sha)
        fields = self._git(
            "show",
            "--no-patch",
            f"--format=%h{FIELD_SEPARATOR}%cs{FIELD_SEPARATOR}%s{FIELD_SEPARATOR}%b",
            sha,
            "--",
        ).split(FIELD_SEPARATOR, 3)
        files = self._diff_files("diff-tree", "--root", "-r", "--no-commit-id", sha)
        return CommitDetails(
            commit=make_commit(fields[0], fields[1], fields[2]),
            body=fields[3].strip() if len(fields) > 3 else "",
            files=files,
        )

    # --- Detalhes de implementação -----------------------------------------------

    def _resolve(self, ref: str) -> None:
        """Valida o formato e confirma que a referência existe."""
        if not SAFE_REF.match(ref) or ".." in ref:
            raise RepositoryError(
                f"Referência inválida: '{ref}'. Use nomes como main, HEAD~3 ou feature/x."
            )
        try:
            self._git("rev-parse", "--verify", "--quiet", "--end-of-options", f"{ref}^{{commit}}")
        except RepositoryError:
            branches = ", ".join(self.local_branches()) or "nenhuma"
            raise RepositoryError(
                f"A referência '{ref}' não existe em {self.name}. Branches locais: {branches}."
            ) from None

    def _log(self, *args: str) -> list[CommitInfo]:
        separator = FIELD_SEPARATOR
        output = self._git("log", f"--format=%h{separator}%cs{separator}%s", *args, "--")
        commits = []
        for line in output.splitlines():
            sha, date, subject = line.split(separator, 2)
            commits.append(make_commit(sha, date, subject))
        return commits

    def _diff_files(self, command: str, *args: str) -> list[FileChange]:
        common = ("--no-renames", "--no-ext-diff", "--no-textconv", "-z")
        numstat = self._git(command, "--numstat", *common, *args).split("\0")
        statuses = self._git(command, "--name-status", *common, *args).split("\0")

        status_by_path: dict[str, FileStatus] = {}
        for letter, path in zip(statuses[0::2], statuses[1::2], strict=False):
            if path:
                status_by_path[path] = STATUS_BY_LETTER.get(letter[:1], "other")

        changes: list[FileChange] = []
        for entry in numstat:
            if not entry:
                continue
            additions, deletions, path = entry.split("\t", 2)
            changes.append(
                FileChange(
                    path=path,
                    status=status_by_path.get(path, "other"),
                    # Arquivos binários aparecem como "-\t-\tcaminho" no numstat.
                    additions=int(additions) if additions.isdigit() else 0,
                    deletions=int(deletions) if deletions.isdigit() else 0,
                )
            )
        if len(changes) > MAX_FILES:
            raise RepositoryError(
                f"{len(changes)} arquivos alterados; o limite é {MAX_FILES}. "
                "Compare referências mais próximas."
            )
        return changes

    def _git(self, *args: str) -> str:
        env = {
            **os.environ,
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_PAGER": "cat",
            "LC_ALL": "C",
        }
        command = [
            "git",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.quotepath=false",
            "-C",
            str(self._root),
            *args,
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=GIT_TIMEOUT_SECONDS,
                env=env,
                check=False,
            )
        except FileNotFoundError:
            raise RepositoryError("O executável git não está instalado neste ambiente.") from None
        except subprocess.TimeoutExpired:
            raise RepositoryError(f"git {args[0]} passou de {GIT_TIMEOUT_SECONDS}s.") from None
        if result.returncode != 0:
            message = result.stderr.strip().splitlines()
            raise RepositoryError(message[0] if message else f"git {args[0]} falhou.")
        return result.stdout
