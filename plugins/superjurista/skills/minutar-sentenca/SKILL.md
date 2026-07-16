---
name: minutar-sentenca
description: Minuta de sentença completa do SuperJurista — dos autos à sentença integral em cinco etapas encadeadas (linha do tempo, relatório, análise, fundamentação com dispositivo, montagem), com regime verbatim de citações e gate local de citações dos autos. Use quando o usuário pedir para minutar, redigir ou preparar uma sentença ou decisão a partir de um processo.
metadata:
  author: superjurista
  version: "1.0.0"
---

# Minutar Sentença

Atalho de disparo do pipeline `sentenca-minuta` da fábrica SuperJurista.

## Execução

1. Confirme o insumo: autos em texto (`processo.txt`). PDF → skill
   `preparar-autos` primeiro (OCR obrigatório — extração digital perde páginas
   escaneadas).
2. Invoque a skill `executar-pipeline` com o pipeline `sentenca-minuta`.
   Etapas do manifesto: linha do tempo → relatório → análise → fundamentação
   (com dispositivo) → montagem da sentença integral. Cada etapa tem gate de
   âncoras; a retomada pula etapas com artefato válido.
3. Encerramento obrigatório: gate local de citações dos autos —
   `python ${CLAUDE_PLUGIN_ROOT}/scripts/verificar_autos_local.py <workspace> --doc=-sentenca.md`
   Toda citação entre aspas na minuta precisa de lastro verbatim nos autos ou
   nas buscas do conector. Exit 1 = corrigir antes de entregar.

## Limites honestos (v1)

- Trilho linear: a triagem cognitiva com trilhos condicionais e a válvula
  ESCALAR da fábrica local ainda não estão nesta versão do pipeline remoto.
- A minuta é SUBSÍDIO ao magistrado — inteligência aumentada, nunca
  substituição. O selo de qualidade depende dos gates terem passado.
