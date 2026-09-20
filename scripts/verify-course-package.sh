#!/usr/bin/env sh
set -eu

source_dir="devbrain-mcp-repo"
package_dir="mcp-megabrain-course/repo"

diff -qr -x '.DS_Store' -x '.venv' -x '.pytest_cache' -x '__pycache__' \
  "$source_dir/src" "$package_dir/src"
diff -qr -x '.DS_Store' -x '.pytest_cache' -x '__pycache__' \
  "$source_dir/test" "$package_dir/test"
diff -qr -x '.DS_Store' "$source_dir/docs" "$package_dir/docs"
diff -q "$source_dir/README.md" "$package_dir/README.md"
diff -q "$source_dir/uv.lock" "$package_dir/uv.lock"
diff -q GUIA-INSTRUTOR.md mcp-megabrain-course/guide/GUIA-INSTRUTOR.md
diff -q GUIA-ALUNO.md mcp-megabrain-course/guide/GUIA-ALUNO.md
diff -q REFERENCIAS.md mcp-megabrain-course/guide/REFERENCIAS.md
diff -q PRESENTACAO-REVISAO.md mcp-megabrain-course/PRESENTACAO-REVISAO.md
cmp -s MCP-MegaBrain-Context-Protocol.pptx mcp-megabrain-course/MCP-MegaBrain-Context-Protocol.pptx
cmp -s MCP-MegaBrain-Context-Protocol.pdf mcp-megabrain-course/MCP-MegaBrain-Context-Protocol.pdf

echo "Pacote distribuível sincronizado com a fonte canônica."
