"""Composition root e entrada stdio do DevBrain MCP.

É o único lugar que escolhe *quais* adapters usar. Para ler outro repositório:

    DEVBRAIN_REPO_PATH=~/caminho/do/seu-repo uv run devbrain-mcp

Sem a variável, o servidor usa o repositório git da pasta onde foi iniciado. Se não
houver repositório, ele sobe mesmo assim, só com as regras puras.

Atenção ao transporte stdio: stdout é o canal do protocolo JSON-RPC. Um ``print()``
aqui corromperia a conversa com o host. Diagnóstico vai para stderr, via logging.
"""

import logging
import os

from devbrain_mcp.adapters.inbound.mcp import create_mcp_server
from devbrain_mcp.adapters.outbound.git_repository import GitRepository
from devbrain_mcp.adapters.outbound.static_guidelines import StaticEngineeringGuidelines
from devbrain_mcp.application.ports import RepositoryError
from devbrain_mcp.application.use_cases import DevBrainUseCases

logger = logging.getLogger("devbrain")


def load_repository() -> GitRepository | None:
    """Lê o repositório configurado; ausência de repositório não é erro fatal."""
    path = os.environ.get("DEVBRAIN_REPO_PATH") or os.getcwd()
    try:
        repository = GitRepository(path)
    except RepositoryError as error:
        logger.warning("DevBrain sem repositório: %s", error)
        return None
    logger.info("DevBrain lendo o repositório %s", repository.name)
    return repository


mcp = create_mcp_server(DevBrainUseCases(StaticEngineeringGuidelines(), load_repository()))


def main() -> None:
    """Executa o servidor pelo transporte stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
