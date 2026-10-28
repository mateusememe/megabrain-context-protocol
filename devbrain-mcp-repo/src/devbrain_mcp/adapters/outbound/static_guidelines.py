"""Adapter local de leitura para o laboratório, substituível por API ou Git.

As regras têm identificadores (R1..R6) de propósito: a tool ``check-pr-readiness``
devolve ``checks`` com os mesmos IDs, e o modelo consegue ligar a evidência da tool
à regra escrita aqui. Resource (o *porquê*) + tool (o *resultado*) = resposta citável.
"""

from __future__ import annotations

ENGINEERING_GUIDELINES = """# DevBrain Engineering Guidelines

Regras que o DevBrain aplica a toda mudança. A tool `check-pr-readiness` devolve um
`check` para cada regra de R1 a R5; R6 orienta o desenho das próprias tools.

| ID | Regra | Bloqueia o PR? |
|----|-------|----------------|
| R1 | O título do PR segue Conventional Commits: `tipo(escopo): descrição`. | Sim |
| R2 | Áreas de alto risco (auth, payment, security, migration, billing) exigem testes. | Sim |
| R3 | Mudanças em contratos públicos (API, schema, CLI, tools MCP) exigem documentação. | Sim |
| R4 | PRs com mais de 20 arquivos devem ser divididos. | Não (recomendação) |
| R5 | Dependências alteradas pedem revisão de changelog, licença e CVEs. | Não (recomendação) |
| R6 | Toda operação destrutiva exige confirmação explícita no host. | Desenho de tool |

## Por que cada regra existe

- **R1**: changelog e versionamento semântico são gerados a partir dos títulos.
- **R2**: um bug em autenticação ou cobrança custa mais que o atraso de escrever o teste.
- **R3**: quem consome um contrato público não lê o seu código, lê a documentação.
  Tools MCP contam: o modelo decide chamá-las lendo nome, descrição e schema.
- **R4**: a qualidade da revisão cai quando o diff não cabe na cabeça do revisor.
- **R5**: dependência nova é código de terceiros entrando no produto.
- **R6**: por isso todas as tools do DevBrain são `readOnlyHint: true`.

## Riscos

O campo `risk_reason` da tool diz qual gatilho foi usado, do mais grave para o mais leve:

- `high`: tocou área de alto risco (R2).
- `medium`: tocou contrato público, dependências ou mais de 10 arquivos.
- `low`: o resto.
"""


class StaticEngineeringGuidelines:
    """Implementação em memória adequada ao exercício sem I/O externo."""

    def read(self) -> str:
        return ENGINEERING_GUIDELINES
