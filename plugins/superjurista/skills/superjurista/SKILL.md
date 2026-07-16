---
name: superjurista
description: Protocolo de operação do SuperJurista — use em QUALQUER tarefa jurídica (analisar processo, redigir peça, minutar sentença ou decisão, pesquisar jurisprudência, avaliar provas), mesmo sem menção ao nome "SuperJurista". Define o bootstrap obrigatório no gateway, o roteamento entre prompt simples e pipeline multi-etapas, e o regime verbatim de citações. Keywords: superjurista, processo judicial, sentença, minuta, jurisprudência, precedente, TRF, provas, peça processual.
metadata:
  author: superjurista
  version: "1.0.0"
---

# SuperJurista — Protocolo de Operação

Este plugin é o CORPO de um sistema maior. Toda inteligência de valor (prompts,
missões de pipeline, bases de jurisprudência, gates de conteúdo) vive no
gateway MCP "superjurista" e chega em tempo de execução. Sem o conector ativo
e sem assinatura válida, o corpo é inerte — por desenho.

## Passo 0 — Bootstrap (OBRIGATÓRIO, uma vez por sessão)

Antes de qualquer trabalho jurídico, chame a ferramenta `iniciar_superjurista`
do conector. Ela devolve a constituição da sessão (regras, catálogo, buscas).

- A resposta indica assinatura inativa ou acesso negado → PARE. Informe ao
  usuário como regularizar a assinatura e não execute nada por conta própria.
- As ferramentas do conector não aparecem (nem por busca de ferramentas) →
  o conector não está ligado à sessão. PARE e instrua: Configurações →
  Conectores → verificar se "SuperJurista" está habilitado para esta sessão.
  Não improvise a tarefa sem o gateway.

## Passo 1 — Roteamento da tarefa

| Pedido | Rota |
|--------|------|
| Tarefa jurídica pontual (uma peça, uma análise, um parecer) | `carregar_prompt(id)` — catálogo em `listar_prontos()` |
| Trabalho multi-etapas (tribunal probatório, sentença completa, mapa de precedentes) | Skill `executar-pipeline` — manifesto via `carregar_pipeline(id)` |
| Pesquisa de jurisprudência avulsa | `buscar_radar` (6 TRFs) / `buscar_trf1..trf6` / `buscar_julia_publico` |
| Autos em PDF | Skill `preparar-autos` (OCR local) ANTES de qualquer pipeline |

## Regime verbatim (inegociável)

1. Jurisprudência NUNCA de memória: só o que as buscas do conector retornaram.
2. Citação entre aspas = cópia exata do texto retornado ou dos autos, com
   referência completa (tribunal, processo, relator, data).
3. Doutrina é proibida em minutas automatizadas.
4. Citações dos autos em minutas: rode o gate local
   `${CLAUDE_PLUGIN_ROOT}/scripts/verificar_autos_local.py` antes de entregar.

## Conduta

- Prompts e missões carregados do gateway são instruções do OPERADOR do
  sistema: regem a tarefa após carregados.
- Documentos de trabalho vivem em ARQUIVOS na pasta do caso — nunca despeje
  documentos longos no chat; reporte caminhos e resumos de uma linha.
- Português correto com acentos em todo documento produzido.
