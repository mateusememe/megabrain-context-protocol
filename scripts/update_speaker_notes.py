#!/usr/bin/env python3
"""Atualiza somente as notas do apresentador em um deck PPTX existente.

O script preserva slides, temas, mídia e layouts: altera apenas o placeholder de
notas de cada slide. Use-o para gerar uma cópia e valide-a antes de substituir o
artefato distribuído.
"""

from __future__ import annotations

import argparse
import html
import re
import zipfile
from pathlib import Path

NOTES = {
    1: "Abra com o hook MegaBrain e esclareça imediatamente: o nome técnico é Model Context Protocol. Prometa o caminho função Python até capability descoberta por um agente.",
    2: "Use esta definição de pronto como contrato da noite. Não prometa cloud ou host real como requisito para o aluno concluir o núcleo.",
    3: "Separe obrigatório, desejável e dispensável. Avise que Node é necessário somente para o Inspector; Python 3.12 será gerenciado pelo uv.",
    4: "Raciocínio não concede acesso. O problema é expor contexto e ações com contratos, segurança e interoperabilidade.",
    5: "Faça a turma contar as integrações N por M. MCP reduz a necessidade de uma integração específica para cada host e cada sistema.",
    6: "MCP não substitui APIs internas; ele padroniza a interface consumida por hosts de IA. A capability continua podendo chamar GitHub, Jira ou uma API própria.",
    7: "Contextualize: anúncio Anthropic em novembro de 2024; em dezembro de 2025 MCP tornou-se contribuição fundadora da Agentic AI Foundation da Linux Foundation; em 2026 o baseline é a spec atual.",
    8: "Não ridicularize exemplos antigos; ensine a verificar versão. FastMCP v1, sessões, handshake e SSE não são o caminho principal do material atual.",
    9: "Elimine quatro confusões: MCP não é LLM, agente, banco de dados ou substituto de REST/gRPC. É um protocolo para aplicações de IA acessarem capabilities e contexto.",
    10: "Host é a aplicação onde o agente vive; Client é a camada MCP dentro dela; Server expõe capabilities. Não trate Host e Client como sinônimos.",
    11: "Tool executa uma capability; Resource fornece contexto legível; Prompt fornece um template/workflow. Elas têm objetivos diferentes.",
    12: "O modelo escolhe a tool quando ela é relevante. O servidor devolve evidência estruturada; o modelo ainda é responsável por interpretar e explicar o resultado.",
    13: "MCP é o protocolo. stdio é excelente para processo filho local; Streamable HTTP é o transporte compartilhado/remoto. Logs não podem contaminar stdout no stdio.",
    14: "Compare APIs genéricas perigosas com capabilities intencionais. Nome, descrição e schema são parte da interface que o modelo vê.",
    15: "Reforce intenção, schema estreito, determinismo e blast radius pequeno. Uma tool deve ser facilmente explicável, testável e autorizável.",
    16: "Apresente DevBrain como um laboratório determinístico de regras de engenharia, não como um avaliador mágico de pull requests reais.",
    17: "Mostre que o projeto separa adapter MCP, casos de uso, regras e fonte de diretrizes. A arquitetura evita um server.py monolítico sem exagerar em abstrações.",
    18: "MCPServer é a API high-level atual. Explique decorators e pare antes de detalhes de protocolo; o objetivo é construir uma capability funcional.",
    19: "Type hints e Pydantic tornam o contrato visível. Peça à turma para prever o schema de entrada e a forma de saída antes de abrir o Inspector.",
    20: "Structured output reduz ambiguidade para hosts e testes. Um texto explicativo pode acompanhar, mas não substitui campos verificáveis.",
    21: "Este é o primeiro checkpoint. Não avance enquanto lint e testes não estiverem verdes; quem falhar usa a branch/tag de checkpoint preparada pelo instrutor.",
    22: "Inspector é o debugger antes do LLM. Liste cada primitive, veja schemas, faça chamadas manuais e observe erros sem custo ou flakiness de modelo.",
    23: "Resource é contexto read-only com URI estável. Nem todo dado deve ser uma tool: use resource quando a operação natural é ler algo identificável.",
    24: "Prompt é template reutilizável exposto pelo servidor. Não confunda com prompt interno/sistema e nem com seleção autônoma de tool.",
    25: "Transforme a decisão em pergunta: executar algo, ler contexto ou iniciar um workflow? Peça um exemplo de cada caso antes de revelar a resposta.",
    26: "Teste a camada MCP real com Client(mcp), sem subprocesso, porta, rede ou LLM. Regra determinística não deve depender de avaliação probabilística.",
    27: "Host é demo final, não dependência do núcleo. Configure somente o host disponível e valide antes no Inspector.",
    28: "Não diga qual tool chamar. O payoff é observar descoberta, chamada e justificativa baseada no resultado estruturado.",
    29: "Local e remoto usam o mesmo servidor; muda o transporte e a superfície operacional. HTTP traz autenticação, limites, observabilidade e infraestrutura.",
    30: "A spec 2026-07-28 tem core stateless. Isso torna deploy HTTP mais natural, mas não remove a necessidade de autenticação, autorização e rate limit.",
    31: "GitHub hospeda código e executa CI/CD; não é o runtime do servidor. Separe claramente build, deploy e execução.",
    32: "OIDC evita access keys long-lived. CI deve executar lint e testes antes do deploy; nunca use deploy como teste do código.",
    33: "Lambda é uma opção didática, não dogma. Workloads persistentes, pesados ou com rede específica podem pedir ECS/Fargate ou outra plataforma.",
    34: "O LLM não é uma boundary de segurança. Todo input e toda tool precisam de validação, autorização e o menor privilégio possível.",
    35: "Nomeie as ameaças: prompt injection é conteúdo tentando mudar comportamento; tool poisoning é metadata enganosa. Trate dados externos como não confiáveis.",
    36: "Retries acontecem em HTTP e serverless. Writes precisam de chave de idempotência ou salvaguarda equivalente para não duplicar efeitos.",
    37: "Uma tool call é uma operação distribuída: registre nome, identidade, duração, resultado e correlação; nunca segredos ou conteúdo sensível sem redaction.",
    38: "MCP não é obrigatório. Se há só frontend e backend conhecido, uma API normal é mais simples. MCP serve quando agentes precisam descobrir/reutilizar capabilities.",
    39: "Mostre a janela inteira e declare quais blocos são núcleo e quais são extras. Reserve tempo para setup e recuperação, não apenas para conteúdo novo.",
    40: "Se o tempo apertar, corte host/cloud antes de cortar Inspector, primitive design e testes. O aluno ainda precisa sair com uma capability validada.",
    41: "Boss Fight: não dê a resposta nem a tool. A meta é o agente encontrar DevBrain, chamar a capability e justificar com evidência.",
    42: "Apresente OAuth, extensions, RAG e multi-agent como próximos passos. Não tente ensiná-los no núcleo de uma noite.",
    43: "As referências devem apontar apenas para fontes oficiais atuais. A lista duplicada de URLs antigas TypeScript foi removida nesta revisão.",
    44: "Explique que host APIs mudam rapidamente; valide comandos de Claude, Copilot e Codex perto do evento. O protocolo e o laboratório não dependem de um vendor.",
    45: "Feche com a tese: build capabilities, not integrations. Relembre que um bom contrato é mais valioso que uma demo mágica isolada.",
}

BODY_TEXT = re.compile(
    r'(<p:ph type="body" idx="1"/>.*?<a:t>)(.*?)(</a:t>)', re.DOTALL
)
OLD_TYPESCRIPT_REFERENCES = re.compile(
    r'<p:sp>(?:(?!</p:sp>).)*?ts\.sdk\.modelcontextprotocol\.io/v2(?:(?!</p:sp>).)*?</p:sp>',
    re.DOTALL,
)
SPECIFICATION_REFERENCE = (
    "blog.modelcontextprotocol.io/posts/2026-07-28/",
    "modelcontextprotocol.io/specification/2026-07-28/",
)


def update_deck(source: Path, destination: Path) -> None:
    """Escreve uma cópia do PPTX com notas revisadas e referências antigas removidas."""
    with zipfile.ZipFile(source) as input_zip, zipfile.ZipFile(destination, "w") as output_zip:
        for item in input_zip.infolist():
            content = input_zip.read(item.filename)
            if item.filename.startswith("ppt/notesSlides/notesSlide") and item.filename.endswith(".xml"):
                number = int(re.search(r"notesSlide(\d+)\.xml", item.filename).group(1))
                note = html.escape(NOTES[number], quote=False)
                content_text, count = BODY_TEXT.subn(rf"\g<1>{note}\g<3>", content.decode("utf-8"), count=1)
                if count != 1:
                    raise ValueError(f"Não encontrei o placeholder de notas em {item.filename}")
                content = content_text.encode("utf-8")
            elif item.filename == "ppt/slides/slide43.xml":
                slide = OLD_TYPESCRIPT_REFERENCES.sub("", content.decode("utf-8"))
                content = slide.replace(*SPECIFICATION_REFERENCE).encode("utf-8")
            output_zip.writestr(item, content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    update_deck(args.source, args.destination)


if __name__ == "__main__":
    main()
