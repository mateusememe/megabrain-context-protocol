from mcp import Client

from devbrain_mcp.server import mcp


async def test_check_pr_readiness_flags_risky_change_without_tests() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool(
            "check-pr-readiness",
            {
                "title": "feat(auth): add passkey login",
                "changed_files": ["src/auth/passkey.py", "src/api/auth.py"],
                "has_tests": False,
                "has_docs": False,
            },
        )

    assert result.is_error is False
    assert result.structured_content is not None
    assert result.structured_content["ready"] is False
    assert result.structured_content["risk"] == "high"
    assert len(result.structured_content["problems"]) >= 1


async def test_server_exposes_three_mcp_primitives() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

    assert {tool.name for tool in tools.tools} >= {
        "check-pr-readiness",
        "analyze-changed-files",
    }
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in tools.tools)
    assert {resource.name for resource in resources.resources} >= {"engineering-guidelines"}
    assert {prompt.name for prompt in prompts.prompts} >= {"review-feature"}


async def test_resource_and_prompt_follow_their_mcp_contracts() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        resource = await client.read_resource("repo://engineering-guidelines")
        prompt = await client.get_prompt("review-feature", {"summary": "Adicionar login passkey"})

    assert "Mudanças em autenticação exigem testes" in resource.contents[0].text
    assert "Adicionar login passkey" in prompt.messages[0].content.text
