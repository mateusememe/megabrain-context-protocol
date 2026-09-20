"""Adapter ASGI -> AWS Lambda para o laboratório.

A Function URL do workshop é pública para reduzir atrito. Em produção, use autenticação,
authorization e uma allowlist de hosts/origins apropriada.
"""

from mangum import Mangum

from devbrain_mcp.server import mcp

app = mcp.streamable_http_app(
    host="0.0.0.0",
    stateless_http=True,
    json_response=True,
)

handler = Mangum(app)
