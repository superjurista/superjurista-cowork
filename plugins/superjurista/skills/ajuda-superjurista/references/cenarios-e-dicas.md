# Cenários por perfil e dicas de máximo potencial

> Material de apoio do concierge. Os exemplos de fluxo citados aqui refletem o
> catálogo no momento da escrita — a lista válida do dia vem SEMPRE de
> `carregar_pipeline()` e `listar_prontos()`. Se um exemplo daqui não constar
> do catálogo vivo, não prometê-lo; se o catálogo trouxer fluxos novos,
> apresentá-los com a mesma lógica destes.

## Cenários por perfil

### Juiz(a) / assessor(a) de gabinete

| Necessidade | Rota | O que sai |
|---|---|---|
| Minutar sentença de um processo | Fluxo de minuta de sentença | Linha do tempo, relatório, análise do caso (com pesquisa de precedentes ao vivo), fundamentação com dispositivo e sentença montada — cada peça num arquivo da pasta do caso |
| Avaliar se a prova sustenta condenação/procedência | Tribunal probatório adversarial | Tese pró-autor e tese pró-réu construídas em paralelo, réplicas cruzadas e síntese final por fato controvertido (provado / não provado / non liquet) |
| Revisar a pauta antes da sessão colegiada | Fluxo de análise de sessão | Alertas em ordem de gravidade: mesma questão decidida de dois jeitos na mesma pauta, contrariedade a jurisprudência, incoerência interna, erro material — com relatório HTML navegável |
| Conferir a redação de uma decisão antes de publicar | Pronto de análise de vícios (o mesmo mapeamento que subsidia embargos serve como revisão preventiva da própria decisão) | Mapa de omissões, contradições, obscuridades e erros materiais |

### Advogado(a)

| Necessidade | Rota | O que sai |
|---|---|---|
| "Cabem embargos de declaração desta decisão?" | Fluxo de embargos (perspectiva do advogado) | Síntese das peças + análise de vícios com veredito honesto (RECOMENDADO / POSSÍVEL MAS ARRISCADO / NÃO RECOMENDADO) e alerta de prequestionamento; se recomendado, a minuta da petição sai pronta |
| Preparar recurso contra sentença | Fluxo de apelação, se constar do catálogo vivo | Mapa recursal da sentença (capítulos, interesse recursal, pontos atacáveis), pesquisa de precedentes e razões redigidas |
| Saber o terreno antes de firmar uma tese | Radar de precedentes | Mapa do tema em toda a Justiça Federal de 2º grau, com convergências, divergências e trechos citáveis copiados verbatim das buscas |
| Peça ou parecer pontual | Pronto do catálogo | O modelo curado da tarefa, aplicado aos documentos fornecidos |

### Qualquer perfil

- **Pesquisa de jurisprudência avulsa** — sem fluxo: usar as buscas do serviço
  diretamente. Regra de ouro: o que aparecer entre aspas é cópia exata do que
  o tribunal publicou, com processo, relator e data.
- **Processo em PDF** — sempre começar por `preparar-autos` (conversão local
  com OCR). Páginas escaneadas são marcadas e transcritas; nada é enviado para
  fora da máquina.

## Como extrair o máximo (as dicas que mudam o resultado)

1. **Dê o contexto estratégico já no pedido.** "Minute a sentença" funciona;
   "minute a sentença — atenção especial à prescrição, que a contestação
   levantou" funciona MELHOR. Tudo o que o usuário disser de ênfase, tese
   preferida ou matéria a prequestionar é injetado nas etapas certas.

2. **Responda às perguntas intermediárias.** Quando o fluxo prevê escolhas do
   usuário, ele para e pergunta antes da etapa (ex.: "pesquisa focada ou
   ampla?", "qual decisão embargar?" — cada fluxo declara as suas). São os
   momentos de maior alavancagem do usuário sobre o resultado — quem responde
   dirige; quem não responde recebe o padrão (que é declarado, nunca oculto).

3. **Revise os artefatos intermediários, não só o final.** A pasta do caso
   guarda cada etapa (linha do tempo, análise, mapa de vícios...). O usuário
   pode pedir "me mostre a análise antes de redigir a peça" — e deve, nos
   casos importantes: corrigir a análise custa minutos; corrigir a peça
   pronta custa a confiança.

4. **Radar antes da tese.** Antes de firmar posição num tema controvertido,
   rodar o radar de precedentes: saber ONDE cada TRF está evita construir
   sobre terreno movediço — e os trechos verbatim já saem prontos para citar.

5. **Interrompeu? Retome sem medo.** Os fluxos reconhecem o que já está pronto
   na pasta do caso e NÃO refazem etapa válida. Fechar o computador no meio
   não perde trabalho.

6. **Peça o selo de verificação.** Em minutas, as citações dos AUTOS são
   conferidas automaticamente, caractere a caractere, contra o texto do
   processo (conferência local); as de JURISPRUDÊNCIA só podem entrar se
   vieram de busca real feita na sessão, com referência completa que permite
   reconferir (regime verbatim). Se o usuário quiser, o veredito da
   conferência pode ser mostrado — é a diferença entre "parece certo" e
   "foi conferido".

7. **Tarefa pequena não precisa de fluxo.** Para um despacho simples, um
   parecer curto, uma revisão de texto: `listar_prontos()` tem dezenas de
   modelos curados que resolvem em uma passada. Fluxo completo é para trabalho
   de fôlego.

8. **O sistema diz "não" — e isso é recurso, não defeito.** O fluxo de
   embargos se recusa a redigir quando a análise conclui que embargar é
   inviável; a minuta se recusa a citar julgado que a busca não confirmou.
   Explicar ao usuário: essas recusas são a proteção dele.
