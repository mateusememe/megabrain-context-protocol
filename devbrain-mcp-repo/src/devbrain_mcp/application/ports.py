"""Portas que a aplicação espera dos adaptadores externos."""

from __future__ import annotations

from typing import Protocol


class EngineeringGuidelinesPort(Protocol):
    """Fonte read-only das diretrizes que o servidor expõe como resource."""

    def read(self) -> str:
        """Retorna as diretrizes de engenharia vigentes."""
