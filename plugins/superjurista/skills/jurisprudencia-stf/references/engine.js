// Motor in-page da busca do STF — injetado na página jurisprudencia.stf.jus.br
// pela skill jurisprudencia-stf. Define window.__stfSearch(opts).
//
// Por que in-page: o STF protege a API com AWS WAF (challenge silencioso). Carregar
// a página de busca deposita o cookie aws-waf-token; então este fetch, de MESMA
// ORIGEM, é aceito (validado ao vivo). NÃO há mint de token por chamada (diferente
// do hCaptcha da Justiça Eleitoral) — só a garantia de que a página está carregada.
//
// A query Elasticsearch e a extração são porte fiel do MCP pesquisa-stf (validado).
(function () {
  const API_PATH = "/api/search/search";

  const BASE_ES = {
    acordaos: "acordaos",
    "repercussao-geral": "acordaos", // sub-filtro (is_repercussao_geral)
    sumulas: "sumulas",
    decisoes: "decisoes",
    informativos: "novo_informativo",
  };

  const SEARCH_FIELDS = [
    "processo_codigo_completo.plural",
    "acordao_ata.plural^3",
    "documental_tese_tema_texto.plural^3",
    "documental_tese_texto.plural^3",
    "documental_indexacao_texto.plural",
    "ementa_texto.plural^3",
    "ministro_facet.plural",
    "orgao_julgador.plural",
    "titulo.plural^6",
    "decisao_texto.plural^2",
    "sumula_texto.plural^3",
    "resumo_noticia.plural^3",
    "titulo_noticia.plural^3",
    "conteudo_noticia.plural^1",
  ];

  const SOURCE_FIELDS = [
    "base", "titulo", "ministro_facet", "relator_processo_nome",
    "procedencia_geografica_uf_sigla", "processo_codigo_completo",
    "processo_classe_processual_unificada_classe_sigla",
    "julgamento_data", "publicacao_data", "orgao_julgador",
    "ementa_texto", "decisao_texto", "documental_tese_texto",
    "documental_tese_tema_texto", "sumula_texto", "sumula_numero",
    "is_vinculante", "is_repercussao_geral",
    "inteiro_teor_url", "acompanhamento_processual_url", "resumo_noticia",
  ];

  function ddmmaaaaParaIso(v) {
    const m = /^(\d{2})(\d{2})(\d{4})$/.exec(v || "");
    return m ? m[3] + "-" + m[2] + "-" + m[1] : v;
  }

  function buildQuery(opts) {
    const base = opts.base || "acordaos";
    const esBase = BASE_ES[base] || "acordaos";
    const max = Math.max(1, Math.min(parseInt(opts.tamanho, 10) || 10, 50));
    const pagina = Math.max(1, parseInt(opts.pagina, 10) || 1);

    const boolQuery = {
      filter: [{
        query_string: {
          default_operator: "AND",
          fields: SEARCH_FIELDS,
          query: opts.busca,
          type: "cross_fields",
          fuzziness: "AUTO:4,7",
          analyzer: "legal_search_analyzer",
          quote_analyzer: "legal_index_analyzer",
        },
      }],
      must: [],
      should: [],
    };
    if (opts.ministro) boolQuery.must.push({ match: { ministro_facet: opts.ministro } });
    if (opts.dataInicio || opts.dataFim) {
      const rng = {};
      if (opts.dataInicio) rng.gte = ddmmaaaaParaIso(opts.dataInicio);
      if (opts.dataFim) rng.lte = ddmmaaaaParaIso(opts.dataFim);
      boolQuery.filter.push({ range: { julgamento_data: rng } });
    }

    const functionScore = {
      functions: [
        { exp: { julgamento_data: { origin: "now", scale: "47450d", offset: "1095d", decay: 0.1 } } },
        { filter: { term: { "orgao_julgador.keyword": "Tribunal Pleno" } }, weight: 1.15 },
        { filter: { term: { is_repercussao_geral: true } }, weight: 1.1 },
      ],
      query: { bool: boolQuery },
    };

    const postFilterMust = [{ term: { base: esBase } }];
    if (base === "repercussao-geral") postFilterMust.push({ term: { is_repercussao_geral: true } });

    return {
      query: { function_score: functionScore },
      _source: SOURCE_FIELDS,
      size: max,
      from: (pagina - 1) * max,
      post_filter: { bool: { must: postFilterMust, should: [] } },
      sort: [{ _score: "desc" }],
      track_total_hits: true,
    };
  }

  function limpar(t) {
    if (!t) return "";
    return String(t).replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
  }
  function fmtData(d) {
    if (!d) return "";
    const iso = String(d).split("T")[0];
    const p = iso.split("-");
    return p.length === 3 ? p[2] + "/" + p[1] + "/" + p[0] : d;
  }

  function extrair(data) {
    const res = (data && data.result) ? data.result : data;
    const hits = (res && res.hits) ? res.hits : {};
    const totalObj = hits.total;
    const total = (totalObj && typeof totalObj === "object")
      ? (totalObj.value || 0) : (totalObj || 0);
    const itens = (hits.hits || []).map(function (hit) {
      const s = hit._source || {};
      let ministro = s.ministro_facet || s.relator_processo_nome || "";
      if (Array.isArray(ministro)) ministro = ministro.join(", ");
      const ementa = limpar(s.ementa_texto);
      const sumula = limpar(s.sumula_texto);
      const decisao = limpar(s.decisao_texto);
      const resumoNot = limpar(s.resumo_noticia);
      const conteudo = (s.base === "novo_informativo")
        ? (resumoNot || ementa) : (ementa || sumula || decisao);
      return {
        numero: s.processo_codigo_completo || s.titulo || "",
        tipo: s.processo_classe_processual_unificada_classe_sigla || "",
        titulo: s.titulo || "",
        orgao: s.orgao_julgador || "",
        relator: String(ministro || ""),
        dataJulgamento: fmtData(s.julgamento_data),
        dataPublicacao: fmtData(s.publicacao_data),
        uf: s.procedencia_geografica_uf_sigla || "",
        isRepercussaoGeral: !!s.is_repercussao_geral,
        sumulaNumero: (s.sumula_numero != null) ? String(s.sumula_numero) : "",
        isVinculante: !!s.is_vinculante,
        tema: limpar(s.documental_tese_tema_texto),
        tese: limpar(s.documental_tese_texto),
        ementa: conteudo,
        inteiroTeorUrl: s.inteiro_teor_url || "",
        acompanhamentoUrl: s.acompanhamento_processual_url || "",
      };
    });
    return { total: total, itens: itens };
  }

  window.__stfSearch = async function (opts) {
    opts = opts || {};
    if (!opts.busca || String(opts.busca).trim().length < 2) {
      return { erro: "opts.busca obrigatório (>= 2 caracteres)" };
    }
    const base = opts.base || "acordaos";
    const body = buildQuery(opts);
    let status = 0, data = null;
    for (let i = 0; i < 2; i++) {
      const r = await fetch(API_PATH, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json, text/plain, */*" },
        body: JSON.stringify(body),
      });
      status = r.status;
      if (status === 200) { data = await r.json(); break; }
      // 202 = cancela WAF expirou; a skill deve re-navegar e reinjetar o motor
      await new Promise(function (res) { setTimeout(res, 1500); });
    }
    if (status !== 200) {
      return { erro: "STF respondeu HTTP " + status + " (cancela WAF) — recarregue o portal e reinjete o motor", status: status };
    }
    const ex = extrair(data);
    return { consulta: opts.busca, base: base, total: ex.total, itens: ex.itens };
  };

  return "engine STF pronto";
})();
