"""Smoke test do DevBrain MCP por Streamable HTTP, sem LLM.

Uso:
    uv run python scripts/smoke_http.py                          # http://127.0.0.1:8000/mcp
    uv run python scripts/smoke_http.py http://localhost:8080/mcp  # Docker ou proxy do Cloud Run
"""

from __future__ import annotations

import asyncio
import sys

from mcp import Client

DEFAULT_URL = "http://127.0.0.1:8000/mcp"
PASSKEY_CHANGE = {
    "title": "feat(auth): add passkey login",
    "changed_files": ["src/auth/passkey.py", "src/api/auth.py"],
    "has_tests": False,
    "has_docs": False,
}


async def main(url: str) -> None:
    async with Client(url) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        print("tools:    ", sorted(tool.name for tool in tools.tools))
        print("resources:", sorted(str(resource.uri) for resource in resources.resources))
        print("prompts:  ", sorted(prompt.name for prompt in prompts.prompts))

        result = await client.call_tool("check-pr-readiness", PASSKEY_CHANGE)
        print("check-pr-readiness:", result.structured_content)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL))
