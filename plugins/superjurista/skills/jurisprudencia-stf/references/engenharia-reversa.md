# Engenharia reversa — API de jurisprudência do STF

> Validada ao vivo em 21–22/07/2026 (via Chrome MCP contra o portal real). O motor
> `engine.js` é o porte fiel desta engenharia; o mesmo contrato já rodou no MCP `pesquisa-stf`.

## Endpoint

- Front (SPA): `https://jurisprudencia.stf.jus.br/pages/search`
- Busca (mesma origem): `POST https://jurisprudencia.stf.jus.br/api/search/search`
  - `Content-Type: application/json`; corpo = Elasticsearch Query DSL.
- Inteiro teor (host diferente): campo `inteiro_teor_url` →
  `https://portal.stf.jus.br/jurisprudencia/obterInteiroTeor.asp?idDocumento=NNN` (redireciona
  para o PDF). Disponível para acórdãos de ~2012 em diante.

## AWS WAF

- Cabeçalho da resposta sem cookie: `x-amzn-waf-action: challenge` → **HTTP 202**.
- É proof-of-work de JavaScript **silencioso** (não CAPTCHA). Um navegador real, ao carregar a
  página, resolve e deposita o cookie `aws-waf-token`. Fetch de mesma origem com o cookie → 200.
- Rejeita navegador **headless-shell** (HTTP 403). Exige Chrome **real** (o do Cowork/Chrome MCP).
- Bloqueia **IP de datacenter** (Cloudflare edge → 526/connection reset). Por isso a rota é o
  navegador do usuário (IP residencial), não um Worker.

## Corpo da busca (resumo)

```
{
  query: { function_score: {
    functions: [
      { exp: { julgamento_data: { origin:"now", scale:"47450d", offset:"1095d", decay:0.1 } } },
      { filter:{term:{"orgao_julgador.keyword":"Tribunal Pleno"}}, weight:1.15 },
      { filter:{term:{is_repercussao_geral:true}}, weight:1.1 }
    ],
    query: { bool: { filter:[{ query_string:{
      default_operator:"AND", fields:[...campos .plural...], query:"<busca>",
      type:"cross_fields", fuzziness:"AUTO:4,7",
      analyzer:"legal_search_analyzer", quote_analyzer:"legal_index_analyzer"
    }}], must:[<ministro/data>], should:[] } }
  }},
  _source: [...campos de retorno...],
  size, from,
  post_filter: { bool:{ must:[{term:{base:"<esBase>"}}, <RG>], should:[] } },
  sort:[{_score:"desc"}], track_total_hits:true
}
```

- `base` pública → campo `base` do índice: acordaos→`acordaos`, repercussao-geral→`acordaos`
  (+ `is_repercussao_geral`), sumulas→`sumulas`, decisoes→`decisoes`,
  informativos→`novo_informativo`.

## Campos de retorno usados (`_source` → item)

`processo_codigo_completo` (numero) · `processo_classe_processual_unificada_classe_sigla` (tipo)
· `orgao_julgador` · `ministro_facet`/`relator_processo_nome` (relator) · `julgamento_data` ·
`publicacao_data` · `procedencia_geografica_uf_sigla` (uf) · `is_repercussao_geral` ·
`sumula_numero`/`is_vinculante` · `documental_tese_tema_texto` (tema) · `documental_tese_texto`
(tese) · `ementa_texto`/`sumula_texto`/`decisao_texto`/`resumo_noticia` (conteúdo) ·
`inteiro_teor_url` · `acompanhamento_processual_url`.

## Provas de acesso (22/07/2026)

- Do navegador (residencial/Cowork): `total` p/ "liberdade" = 11.200 acórdãos; RE 979742
  (Barroso, RG Tema 952) renderizado. `window.__stfSearch("liberdade de expressao")` → 606,
  RE 795467 RG (Teori), AP 1403 (Alexandre de Moraes).
- Do sandbox de terminal do Cowork: `curl` → 403 `blocked-by-allowlist` (proxy). Por isso é
  skill de navegador, não fetch de terminal.
