"""Demo sem LLM: faz pelo protocolo MCP exatamente o que um agente faria.

Este script é um **MCP Client** de verdade. Ele sobe o DevBrain como subprocesso
(transporte stdio, igual ao Antigravity e ao Claude Code), descobre as capabilities e
encadeia as tools. Útil para:

- mostrar o protocolo passo a passo, sem a "mágica" do modelo no meio;
- ter um plano B se a rede ou o host falharem.

Uso:
    uv run python scripts/demo_sem_llm.py ~/caminho/do/seu-repo main sua-branch
    uv run python scripts/demo_sem_llm.py              # repositório atual, main...HEAD
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def step(number: int, title: str, explanation: str) -> None:
    print(f"\n{'=' * 78}\n{number}. {title}\n{'=' * 78}")
    print(f"   {explanation}\n")


def show(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


async def main(repo_path: str, base: str, head: str) -> None:
    # O host faz isto ao ler o mcp_config.json / .mcp.json: inicia um processo e
    # conversa por stdin/stdout. O env é explícito: clientes MCP não repassam todo o
    # ambiente para o servidor, só o que você declara.
    server = StdioServerParameters(
        command="uv",
        args=["run", "--quiet", "--project", str(PROJECT_ROOT), "devbrain-mcp"],
        env={"DEVBRAIN_REPO_PATH": repo_path},
    )

    async with Client(server, raise_exceptions=True) as client:
        step(1, "Descoberta", "O host conecta e lê nome, versão e instruções do servidor.")
        info = client.server_info
        print(f"   servidor: {info.name} {info.version}  |  protocolo: {client.protocol_version}")
        print(f"   instructions: {client.instructions}")

        step(2, "tools/list", "O modelo só enxerga isto: nome, título, descrição e schema.")
        for tool in (await client.list_tools()).tools:
            arguments = ", ".join(tool.input_schema.get("properties", {}))
            print(f"   - {tool.name} ({tool.title}) ← {arguments}")
            print(f"     {tool.description.splitlines()[0]}")

        step(3, "resources/list e prompts/list", "Contexto e workflows que o usuário escolhe.")
        for resource in (await client.list_resources()).resources:
            print(f"   resource  {resource.uri}  ({resource.title})")
        for template in (await client.list_resource_templates()).resource_templates:
            print(f"   template  {template.uri_template}  ({template.title})")
        for prompt in (await client.list_prompts()).prompts:
            print(f"   prompt    {prompt.name}  ({prompt.title})")

        step(4, "tools/call inspect-branch-changes", f"Evidência real do git: {base}...{head}.")
        inspected = await client.call_tool("inspect-branch-changes", {"base": base, "head": head})
        if inspected.is_error:
            # O mesmo isError que o modelo recebe: a mensagem diz o que corrigir.
            print(f"   isError: true\n   {inspected.content[0].text}")
            return
        changes = inspected.structured_content
        print(f"   repositório: {changes['repository']}")
        print(
            f"   commits: {len(changes['commits'])}  |  arquivos: {len(changes['files'])}  "
            f"|  +{changes['total_additions']} -{changes['total_deletions']}"
        )
        print(f"   has_tests: {changes['has_tests']}  |  has_docs: {changes['has_docs']}")
        print(f"   dependências: {changes['dependency_changes'] or 'nenhuma'}")
        print(f"   commits fora do padrão: {changes['non_conventional_commits'] or 'nenhum'}")
        print(f"   título sugerido: {changes['suggested_title']}")

        step(
            5, "tools/call check-pr-readiness", "O agente encadeia: saída de uma tool vira entrada."
        )
        paths = [file["path"] for file in changes["files"]]
        readiness = (
            await client.call_tool(
                "check-pr-readiness",
                {
                    "title": changes["suggested_title"],
                    "changed_files": paths,
                    "has_tests": changes["has_tests"],
                    "has_docs": changes["has_docs"],
                },
            )
        ).structured_content
        show(readiness)

        step(6, "tools/call analyze-changed-files", "Quem deve revisar e o que olhar primeiro.")
        show((await client.call_tool("analyze-changed-files", {"files": paths})).structured_content)

        step(7, "resources/read de um template", "Detalhe do commit mais antigo da branch.")
        sha = changes["commits"][-1]["sha"]
        commit = await client.read_resource(f"devbrain://repository/commits/{sha}")
        print(commit.contents[0].text[:900])

        step(8, "Erro legível", "Argumento ruim volta como isError para o modelo se corrigir.")
        error = await client.session.call_tool("inspect-branch-changes", {"base": "nao-existe"})
        print(f"   isError: {error.is_error}\n   {error.content[0].text}")


if __name__ == "__main__":
    arguments = sys.argv[1:]
    repo = str(Path(arguments[0]).expanduser().resolve()) if arguments else str(Path.cwd())
    asyncio.run(
        main(
            repo,
            arguments[1] if len(arguments) > 1 else "main",
            arguments[2] if len(arguments) > 2 else "HEAD",
        )
    )
