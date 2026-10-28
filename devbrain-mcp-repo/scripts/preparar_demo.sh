#!/usr/bin/env bash
# Prepara configs para usar o DevBrain contra um repositório real seu.
#
#   ./scripts/preparar_demo.sh ~/caminho/do/seu-repo
#
# Gera, em demo/<repositório>/ (pasta ignorada pelo git):
#   claude-mcp.json                       -> claude --mcp-config / inspector --config
#   antigravity/.agents/mcp_config.json   -> workspace do Antigravity CLI/IDE
#
# Não altera nenhuma configuração global de host nem o repositório analisado.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
repo_input="${1:-$PWD}"

if ! repo="$(git -C "$repo_input" rev-parse --show-toplevel 2>/dev/null)"; then
  echo "erro: $repo_input não é um repositório git" >&2
  exit 1
fi

name="$(basename "$repo")"
out="$root/demo/$name"
mkdir -p "$out/antigravity/.agents"

(cd "$root" && uv sync --quiet)

python3 - "$root" "$repo" "$out" <<'PY'
import json
import sys
from pathlib import Path

root, repo, out = sys.argv[1:]
server = {
    "command": "uv",
    # --project (e não --directory) mantém a pasta atual do host, e o caminho do
    # repositório vai explícito em env: hosts não repassam todo o ambiente ao servidor.
    "args": ["run", "--quiet", "--project", root, "devbrain-mcp"],
    "env": {"DEVBRAIN_REPO_PATH": repo},
}
config = json.dumps({"mcpServers": {"devbrain": server}}, indent=2) + "\n"
Path(out, "claude-mcp.json").write_text(config)
Path(out, "antigravity", ".agents", "mcp_config.json").write_text(config)
PY

echo "Repositório: $repo"
echo "Branch atual: $(git -C "$repo" rev-parse --abbrev-ref HEAD)"
echo "Branches locais:"
git -C "$repo" for-each-ref --format='  %(refname:short)' refs/heads
echo
echo "1) Sem LLM (protocolo puro):"
echo "   uv run python scripts/demo_sem_llm.py $repo main <branch>"
echo
echo "2) MCP Inspector (o mesmo arquivo de config serve):"
echo "   npx -y @modelcontextprotocol/inspector@2.12.0 --config $out/claude-mcp.json --server devbrain"
echo
echo "3) Claude Code (--setting-sources ignora ~/.claude/settings.json: proxies e"
echo "   flags pessoais ficam de fora da demo):"
echo "   claude --setting-sources project,local --mcp-config $out/claude-mcp.json --strict-mcp-config"
echo
echo "4) Antigravity CLI (ou abra a pasta no Antigravity IDE):"
echo "   cd $out/antigravity && agy"
