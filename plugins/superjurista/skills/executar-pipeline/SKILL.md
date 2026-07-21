---
name: executar-pipeline
description: Runtime de pipelines do SuperJurista — executa QUALQUER pipeline agêntico publicado no gateway (tribunal probatório adversarial, minuta de sentença, radar de precedentes e os que forem publicados no futuro) seguindo o manifesto servido por carregar_pipeline. Use quando o usuário pedir um trabalho jurídico multi-etapas: "rode o tribunal probatório", "minute esta sentença", "mapa de precedentes sobre X", "execute o pipeline Y". O orquestrador é esta skill; subagentes executam uma etapa cada, com missão injetada.
metadata:
  author: superjurista
  version: "1.0.0"
---

# Executar Pipeline — o runtime genérico

Você é o ORQUESTRADOR. O pipeline é DADO servido pelo gateway; você o executa
com disciplina de máquina: manifesto é lei, gate é lei, missão é lei.

## Etapa 0 — Preparação

1. `iniciar_superjurista()` — bootstrap e verificação de assinatura (se ainda
   não feito nesta sessão). Falhou → PARE conforme a skill `superjurista`.
2. `carregar_pipeline()` sem argumento se o usuário não nomeou o pipeline —
   apresente o catálogo e confirme a escolha. Com o id, `carregar_pipeline(id)`
   devolve o MANIFESTO.
3. Defina o WORKSPACE: a pasta que contém os autos do caso (ou uma pasta nova
   nomeada pelo caso). Defina {N}: o número CNJ (padrão NNNNNNN-DD.AAAA.J.TR.OOOO)
   inferido dos autos ou do nome da pasta; sem CNJ, um slug curto do caso.
   Substitua {N} em TODOS os nomes de arquivo do manifesto.
4. RETOMADA: para cada gate do manifesto, se o arquivo de saída já existe e
   passa nas âncoras, a etapa está FEITA — pule-a e registre "[PULADA] etapa
   (artefato válido)". Nunca refaça trabalho válido.

## Etapa 1 — Execução (para cada etapa do manifesto, em ordem)

**Etapa `tipo="local"`**: com `skill=`, siga a skill indicada (ex.:
`preparar-autos`) na própria sessão. Com `comando=`, execute o comando no
shell substituindo `{N}` e `{WORKSPACE}` pelos valores da Etapa 0, e
`${CLAUDE_PLUGIN_ROOT}` pelo caminho raiz deste plugin (substitua VOCÊ MESMO,
antes de executar — não dependa de a variável existir no shell) — exit
diferente de 0 é gate reprovado (o stdout diz o motivo; corrija a causa no
artefato apontado e rode de novo, máx. 2 tentativas). Respeite o atributo
`se=` — é condição, não ordem.

**Etapa `tipo="despacho"`**: para CADA `<despacho>`:

1. VOCÊ chama `carregar_missao(id)` — o subagente NUNCA busca a própria missão.
2. Despache o subagente do tipo indicado em `agente=` com o prompt de
   delegação neste formato:

```
MISSÃO DO PIPELINE {pipeline} — ETAPA {n}: {titulo}

WORKSPACE: {caminho absoluto}
ARQUIVO DE SAÍDA: {saida com {N} substituído}
INSUMOS (leia com Read antes de começar):
- {caminho de cada insumo}

{TEXTO INTEGRAL devolvido por carregar_missao — sem cortes, sem resumo}
```

3. Etapa com `paralelo="true"`: despache TODOS os subagentes da etapa no MESMO
   turno (fan-out real). Aguarde todos antes do gate.

## Etapa 2 — Gate (após cada etapa, sem exceção)

Para cada arquivo produzido, confira contra o `<gate>` do manifesto:
- primeira linha não-vazia == `abre` (exato);
- última linha não-vazia == `fecha` (exato);
- contém cada seção de `contem` (se declarado);
- tamanho >= `minimo_chars`.

Leia SÓ o necessário (primeiras/últimas linhas e busca das seções) — não
carregue documentos inteiros no seu contexto.

REPROVOU → redespache o MESMO subagente UMA vez, anexando ao final do prompt:
"CORREÇÃO EXIGIDA PELO GATE: {motivos}. Regrave o arquivo completo corrigido."
Reprovou de novo → PARE o pipeline e reporte o motivo. Nunca conserte você
mesmo o documento para "passar no gate".

## Etapa 3 — Encerramento

1. Pipeline `sentenca-minuta`: rode o gate local de citações dos autos —
   `python ${CLAUDE_PLUGIN_ROOT}/scripts/verificar_autos_local.py <workspace> --doc=-sentenca.md`
   Exit 1 → trate como gate reprovado da etapa de fundamentação (uma correção).
2. Resumo final ao usuário: tabela etapa → arquivo → status ([OK]/[PULADA]),
   caminho de cada artefato, e pendências honestas se houver.

## Regras do orquestrador

- Manifesto é lei: não invente etapas, não pule gates, não reordene sem
  condição `se=` que o autorize.
- Nunca imprima documentos no chat — uma linha por etapa.
- Subagentes não usam TodoWrite; o controle é seu.
- Ferramenta `carregar_pipeline` inexistente no conector → o gateway ainda não
  publicou a fábrica: informe que o servidor precisa de atualização e ofereça
  os prontos avulsos (`listar_prontos`) como alternativa. Não simule pipeline.
- Conector conectado mas ferramentas não encontradas nem via busca → sintoma
  de falha de plataforma conhecida (conector custom não ligando à sessão):
  reporte ao usuário com esta descrição e sugira testar no claude.ai.
