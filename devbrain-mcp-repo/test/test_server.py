"""O servidor visto por um MCP Client real, dentro do mesmo processo.

``Client(server)`` fala o protocolo de verdade (tools/list, tools/call,
resources/read, prompts/get), mas sem rede e sem LLM. É assim que se testa um
servidor MCP antes de plugar em qualquer host.
"""

from mcp import Client

PASSKEY_CHANGE = {
    "title": "feat(auth): add passkey login",
    "changed_files": ["src/auth/passkey.py", "src/api/auth.py"],
    "has_tests": False,
    "has_docs": False,
}


async def test_check_pr_readiness_flags_risky_change_without_tests(remote_server) -> None:
    async with Client(remote_server, raise_exceptions=True) as client:
        result = await client.call_tool("check-pr-readiness", PASSKEY_CHANGE)

    assert result.is_error is False
    assert result.structured_content["ready"] is False
    assert result.structured_content["risk"] == "high"
    assert result.structured_content["problems"] == [
        "Área de alto risco alterada sem testes automatizados.",
        "Contrato público alterado sem atualização de documentação.",
    ]
    assert [check["rule"] for check in result.structured_content["checks"]] == [
        "R1",
        "R2",
        "R3",
        "R4",
        "R5",
    ]


async def test_analyze_changed_files_matches_its_output_schema(remote_server) -> None:
    async with Client(remote_server, raise_exceptions=True) as client:
        result = await client.call_tool(
            "analyze-changed-files", {"files": ["src/auth/passkey.py", "src/api/auth.py"]}
        )

    assert result.is_error is False
    assert result.structured_content == {
        "areas": ["api", "security"],
        "review_focus": [
            "authorization, validation and secret handling",
            "contract compatibility and error handling",
        ],
    }


async def test_invalid_arguments_reach_the_model_as_a_readable_error(remote_server) -> None:
    async with Client(remote_server) as client:
        result = await client.call_tool(
            "check-pr-readiness", {**PASSKEY_CHANGE, "changed_files": []}
        )

    assert result.is_error is True
    assert "changed_files precisa conter ao menos um arquivo" in result.content[0].text


async def test_tools_publish_titles_descriptions_and_read_only_hints(local_server) -> None:
    async with Client(local_server, raise_exceptions=True) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert set(tools) == {"check-pr-readiness", "analyze-changed-files", "inspect-branch-changes"}
    for tool in tools.values():
        assert tool.title
        assert tool.annotations.read_only_hint is True
        assert tool.output_schema is not None
    title_schema = tools["check-pr-readiness"].input_schema["properties"]["title"]
    assert title_schema["description"] == "Título proposto para o pull request."


async def test_remote_server_only_exposes_pure_rules(remote_server) -> None:
    async with Client(remote_server, raise_exceptions=True) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

    assert {tool.name for tool in tools.tools} == {"check-pr-readiness", "analyze-changed-files"}
    assert {str(resource.uri) for resource in resources.resources} == {
        "repo://engineering-guidelines",
        "devbrain://server/guide",
    }
    assert {prompt.name for prompt in prompts.prompts} == {"review-feature"}


async def test_inspect_branch_changes_returns_real_git_evidence(local_server) -> None:
    async with Client(local_server, raise_exceptions=True) as client:
        result = await client.call_tool("inspect-branch-changes", {"base": "main"})

    changes = result.structured_content
    assert changes["repository"] == "demo-app"
    assert [file["path"] for file in changes["files"]] == [
        "src/api/auth.py",
        "src/auth/passkey.py",
    ]
    assert changes["has_tests"] is False
    assert changes["has_docs"] is False
    assert changes["suggested_title"] == "feat(auth): add passkey login"
    assert len(changes["non_conventional_commits"]) == 1


async def test_inspect_branch_changes_explains_unknown_branch(local_server) -> None:
    async with Client(local_server) as client:
        result = await client.call_tool("inspect-branch-changes", {"base": "develop"})

    assert result.is_error is True
    assert "Branches locais: feature/passkey, main" in result.content[0].text


async def test_resources_and_templates_expose_repository_context(local_server) -> None:
    async with Client(local_server, raise_exceptions=True) as client:
        templates = await client.list_resource_templates()
        overview = await client.read_resource("devbrain://repository/overview")
        changes = await client.call_tool("inspect-branch-changes", {})
        sha = changes.structured_content["commits"][-1]["sha"]
        commit = await client.read_resource(f"devbrain://repository/commits/{sha}")

    assert [t.uri_template for t in templates.resource_templates] == [
        "devbrain://repository/commits/{sha}"
    ]
    assert "Branch atual: `feature/passkey`" in overview.contents[0].text
    assert "⚠ não convencional" in overview.contents[0].text
    assert '"subject": "feat(auth): add passkey login"' in commit.contents[0].text


async def test_resource_and_prompt_follow_their_mcp_contracts(remote_server) -> None:
    async with Client(remote_server, raise_exceptions=True) as client:
        resource = await client.read_resource("repo://engineering-guidelines")
        prompt = await client.get_prompt("review-feature", {"summary": "Adicionar login passkey"})

    assert "| R2 |" in resource.contents[0].text
    assert "Adicionar login passkey" in prompt.messages[0].content.text


async def test_review_branch_prompt_embeds_the_guidelines_resource(local_server) -> None:
    async with Client(local_server, raise_exceptions=True) as client:
        prompt = await client.get_prompt("review-branch", {"base": "main", "head": "HEAD"})

    instructions, guidelines = prompt.messages
    assert 'Chame `inspect-branch-changes` com base="main"' in instructions.content.text
    assert guidelines.content.type == "resource"
    assert str(guidelines.content.resource.uri) == "repo://engineering-guidelines"
