# Slides da palestra

Os slides de "MCP: MegaBrain Context Protocol", do DevFest 2026. São 56 slides feitos
em [reveal.js](https://revealjs.com/) sobre o template do DevFest, com os diagramas e
o código que aparecem na aula.

## Como abrir

O GitHub mostra o `index.html` como código, então para ver os slides você precisa do
arquivo na sua máquina. Clone o repositório e abra `apresentacao/index.html` no
navegador. Duplo clique funciona.

Não precisa de servidor. O reveal.js vem junto, em `vendor/`, e roda sem internet. A
única coisa baixada é a fonte Google Sans; offline, o navegador usa uma parecida e o
layout continua de pé.

## Atalhos

| Tecla | O que faz |
|---|---|
| → ou espaço | próximo passo (os elementos aparecem um por vez) |
| ← | volta |
| F | tela cheia |
| S | janela do apresentador, com o próximo slide e um relógio |
| Esc | visão geral dos slides |
| G e o número | pula para um slide |

O endereço acompanha o slide: `index.html#/13` abre o 13.

## Revisar ou imprimir

`index.html?tudo` mostra cada slide já completo, sem ir revelando item por item. É o
jeito mais rápido de reler a palestra.

Para PDF, abra `index.html?print-pdf` no Chrome e imprima como PDF.

## O que tem na pasta

```text
apresentacao/
├── index.html       os slides, o estilo e a configuração do reveal.js
├── assets/          fundos do template, fotos, QR codes e o mascote
└── vendor/reveal/   reveal.js 5.1.0 com os plugins de código e de notas
```
