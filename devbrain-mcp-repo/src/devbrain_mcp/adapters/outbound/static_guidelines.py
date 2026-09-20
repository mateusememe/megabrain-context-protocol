"""Adapter local de leitura para o laboratório, substituível por API ou Git."""

from __future__ import annotations

ENGINEERING_GUIDELINES = """# DevBrain Engineering Guidelines

- Mudanças em autenticação exigem testes automatizados.
- Pull requests devem ter título no formato Conventional Commits.
- Mudanças em contratos públicos devem incluir documentação.
- Evite misturar refactor e feature grande no mesmo PR.
- Toda operação destrutiva deve exigir confirmação explícita no host.
"""


class StaticEngineeringGuidelines:
    """Implementação em memória adequada ao exercício sem I/O externo."""

    def read(self) -> str:
        return ENGINEERING_GUIDELINES
