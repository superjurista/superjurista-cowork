---
name: tribunal-probatico
description: Tribunal probatório adversarial do SuperJurista — debate real sobre a prova de um processo (penal ou cível): advogado da pretensão e advogado da resistência constroem teses em paralelo, trocam réplicas e um juiz-mediador consolida o estado da prova POR PROBANDA. Use quando o usuário pedir análise probatória, avaliação das provas, "quem tem razão nas provas", tribunal probatório ou análise adversarial de um caso.
metadata:
  author: superjurista
  version: "1.0.0"
---

# Tribunal Probatório Adversarial

Atalho de disparo do pipeline `tribunal-probatico` da fábrica SuperJurista.

## Execução

1. Confirme o insumo: autos em texto (`processo.txt`) na pasta do caso.
   Entrada em PDF → rode antes a skill `preparar-autos` (OCR).
2. Invoque a skill `executar-pipeline` com o pipeline `tribunal-probatico`.
   O manifesto do gateway rege tudo: teses pró-autor e pró-réu em PARALELO
   (fan-out real de subagentes), réplicas cruzadas em paralelo, síntese final
   do juiz-mediador.
3. O produto final é `{N}-probatica-consolidado.md` — estado da prova por
   probanda (PROVADA / NÃO PROVADA / NON LIQUET), convergências, divergências
   decididas e lacunas com consequência de ônus.

## O que este tribunal NÃO faz

- Não decide o mérito da causa — decide o estado da PROVA.
- Não inventa provas nem julgados: tudo ancorado nos autos com fonte, e
  jurisprudência só via buscas do conector, verbatim.
