# SuperJurista para Claude Cowork

> **O corpo é público. O cérebro é assinatura.**

Este repositório é o **marketplace do plugin SuperJurista** — o sistema
agêntico jurídico que roda dentro do **Claude Cowork** (e do Claude Code):
tribunal probatório adversarial, minuta de sentença com regime verbatim de
citações e radar de precedentes ao vivo nos 6 TRFs.

## Arquitetura: corpo e cérebro

| Camada | Onde vive | O que contém |
|--------|-----------|--------------|
| **Corpo** (este repo, público) | Plugin instalado no Cowork | Skills orquestradoras finas, agentes de capacidade, scripts locais (OCR dos autos, gate de citações) |
| **Cérebro** (gateway MCP, assinatura) | `mcp.superjurista.com` | Prompts curados, missões de pipeline, manifestos, radar de jurisprudência dos 6 TRFs |

Nenhum prompt de valor vive neste repositório — **por desenho**. O plugin é um
*runtime*: cada etapa de pipeline pede sua missão ao gateway em tempo de
execução (`carregar_pipeline` / `carregar_missao`). Sem assinatura ativa, o
corpo é inerte. Com assinatura, **pipelines novos aparecem sem reinstalar
nada** — eles são conteúdo do servidor, não código do plugin.

**Instalar → Conectar → Escolher:** ao instalar o plugin, o Claude abre o
login do SuperJurista com dois caminhos: o botão **Experimentar sem convite**
(visitante com 1 resposta completa gratuita por dia) ou, para assinante, o
campo de **convite** (`sj-...`) + e-mail seguido de **Autorizar acesso**. Seu
convite também pode ser digitado na conversa para elevar a conta de visitante
a assinante sem reconectar. Para assinatura:
<https://mcp.superjurista.com/assinar>.

## Instalação

**No Claude Cowork (desktop):**
1. Cowork → **Customize** → **Plugins** → adicionar marketplace a partir deste
   repositório (GitHub/Git URL).
2. Instalar o plugin **superjurista**. O Claude abre automaticamente o login do
   SuperJurista: clique em **Experimentar sem convite** (visitante com 1 resposta/dia)
   ou preencha o **convite** (`sj-...`) + e-mail e clique em **Autorizar acesso**
   (assinante com acesso ilimitado).
3. Após login, o conector fica ativo: assinantes começam com `iniciar_superjurista`;
   visitantes usam `ativar_superjurista` e têm direito a uma tarefa completa gratuita
   por dia. Para elevar para assinante, digite seu convite (`sj-...`) na conversa.

**No Claude Code:**
```
/plugin marketplace add <url-deste-repo>
/plugin install superjurista@superjurista
```

**Assinante com a página de boas-vindas:** o caminho mais curto nem precisa
deste repositório — basta o gesto único da página `/acesso/<convite>` (colar a
URL pessoal em Configurações → Conectores). Este plugin acrescenta os recursos
locais do Cowork: OCR dos autos sem rede, agentes paralelos e gate de citações.

## O que ele faz

O catálogo é **vivo** — a lista completa e atual vem de `carregar_pipeline()`
no próprio conector; pipelines novos aparecem sem atualizar este pacote.
Exemplos publicados:

| Pipeline | Produto final |
|----------|---------------|
| `tribunal-probatico` | Debate adversarial real sobre a prova (teses paralelas, réplicas cruzadas, síntese por probanda do juiz-mediador) |
| `sentenca-minuta` | Sentença integral: linha do tempo → relatório → análise → fundamentação → montagem, com gates de âncora e gate local de citações dos autos |
| `radar-precedentes` | Mapa de um tema em toda a Justiça Federal de 2º grau, com trechos verbatim citáveis |
| `analisar-sessao` | Revisão econômica de pauta de sessão colegiada: teses por ementa, detecção de incoerências/erros/sensibilidade, confronto jurisprudencial só onde há mérito e relatório de alertas |
| `embargos-advogado` | Embargos de declaração na perspectiva do advogado: síntese das peças + linha do tempo, análise de vícios da decisão (com veredito de viabilidade e alerta de prequestionamento) e minuta da petição — se a análise disser "não embargue", o pipeline para e explica |

Perdido? Diga **"me ajuda a usar o SuperJurista"** — o assistente de ajuda
(skill `ajuda-superjurista`) explica o sistema em linguagem de gabinete,
diagnostica o que você precisa e conduz à rota certa, sem jargão técnico.

Regra de ouro do sistema: **nenhuma citação sem verificação**. Jurisprudência
só via buscas ao vivo do conector; citações dos autos conferidas localmente
(`verificar_autos_local.py`) — os autos **nunca saem da sua máquina**, só o
veredito (com hash) é registrado.

## Requisitos

- Claude Cowork (plano pago) ou Claude Code.
- Assinatura SuperJurista ativa (o gateway responde ao bootstrap).
- Para autos em PDF: Python 3.8+, poppler e tesseract-por no ambiente de
  execução (a skill `preparar-autos` instrui a instalação).

## Estado (julho/2026) — honestidade radical

- O runtime (`executar-pipeline`) segue o manifesto servido pelo gateway;
  a fábrica de pipelines do servidor está em implantação — se
  `carregar_pipeline` ainda não existir no conector, o plugin oferece os
  prompts avulsos (`listar_prontos`) e avisa.
- Bugs de plataforma conhecidos e monitorados: conectores custom podem não
  ligar a sessões do Cowork (anthropics/claude-ai-mcp#584) e pedidos de
  permissão por tool call em contas Team (#491).
- Este plugin é **inteligência aumentada** para profissionais do direito —
  subsídio de trabalho, nunca substituição do julgamento humano.

## Licença

O código deste pacote (o "corpo") é MIT. Os prompts, missões, manifestos e
bases servidos pelo gateway (o "cérebro") **não estão neste repositório** e
são licenciados apenas via assinatura.
