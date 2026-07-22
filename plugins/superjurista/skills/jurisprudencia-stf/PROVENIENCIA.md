# Proveniência

Skill de busca da jurisprudência viva do STF, criada em 22/07/2026 para o plugin
`superjurista-cowork`. Irmã da `jurisprudencia-eleitoral` (supereleitoral) — **consumir o
padrão, não copiar**: mesma arquitetura (skill de navegador + motor in-page + procedência),
adaptada ao STF.

## Por que skill de navegador (e não MCP)

O STF é inalcançável por toda rota remota do produto:
- **edge Cloudflare** → HTTP 526 / connection reset (STF bloqueia IP de datacenter);
- **web Anthropic** → IP de datacenter + sem navegador;
- **sandbox de terminal do Cowork** → `curl` bloqueado por allowlist de proxy (403).

MAS o **navegador do Cowork alcança o STF** (rota permitida, IP residencial, navegador real que
resolve o AWS WAF). Provado em 22/07: 11.200 acórdãos renderizados; `window.__stfSearch` →
resultados reais. Um MCP local (host Python) NÃO chega à VM do Cowork. Logo, a casa de produto
do STF é esta skill.

## Reaproveitamento

O `engine.js` (query Elasticsearch, extração, dialeto de sintaxe) é porte fiel do MCP
`pesquisa-stf` (branch `feat/stf-mcp-local` do superjurista-produto), que fica como **ferramenta
de dev** (funciona no Claude Code). A versão de **produto** é esta skill.

## Relação com o BNP

Complementar: o BNP (conector) cobre o precedente QUALIFICADO do STF (súmula/vinculante/RG/
ADI/ADC/ADO/ADPF) sem navegador; esta skill cobre o ACERVO vivo (acórdão comum, monocrática,
RE, informativo).
