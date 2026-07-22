---
name: jurisprudencia-stf
description: >
  Busca a jurisprudência VIVA do Supremo Tribunal Federal — acórdãos (desde 1950),
  repercussão geral, súmulas, decisões monocráticas e informativos — no portal
  jurisprudencia.stf.jus.br, via navegador real (o STF protege a API com AWS WAF, que só um
  navegador resolve). Retorna cada precedente com ementa verbatim, metadados, link do inteiro
  teor e um bloco de PROCEDÊNCIA (fonte, confiabilidade e janela de cobertura). Use quando o
  usuário pedir jurisprudência do STF, acórdão/monocrática/informativo do Supremo, tese de
  repercussão geral, súmula, ou citar decisão do STF. Complementa o BNP: o BNP traz só o
  precedente QUALIFICADO do STF; esta skill traz o ACERVO vivo. Palavras-chave: jurisprudência
  STF, Supremo, acórdão STF, repercussão geral, súmula vinculante, informativo STF.
context: fork
agent: general-purpose
allowed-tools: Bash Read Write mcp__claude-in-chrome__tabs_context_mcp mcp__claude-in-chrome__tabs_create_mcp mcp__claude-in-chrome__navigate mcp__claude-in-chrome__javascript_tool mcp__claude-in-chrome__computer
compatibility: >
  Requer navegador real (Chrome MCP / "Claude no Chrome") com acesso a
  jurisprudencia.stf.jus.br. Funciona no Cowork (o navegador do Cowork alcança o STF pela rota
  permitida) e no Claude Code. NÃO funciona por API remota (edge/web): o STF bloqueia IP de
  datacenter, e o sandbox de terminal bloqueia o domínio por allowlist — por isso é skill de
  navegador, não MCP.
metadata:
  author: super-jurista
  version: "1.0.0"
  category: pesquisa-juridica
---

<identidade>
  <papel>Pesquisador da jurisprudência viva do Supremo Tribunal Federal</papel>
  <dominio>Direito constitucional; busca no Elasticsearch do portal do STF via navegador</dominio>
</identidade>

<proposito>
  <objetivo>Buscar e reportar precedentes do STF (acervo completo, não só o qualificado) com
  ementa verbatim, metadados, inteiro teor e procedência declarada</objetivo>
  <razao>O STF protege a API de busca com AWS WAF (challenge silencioso). Um fetch sem
  navegador toma HTTP 202; um navegador real resolve a cancela ao carregar a página, e a busca
  passa a funcionar de dentro do contexto da página. É a única rota que alcança o STF na
  superfície do produto (o Cowork).</razao>
</proposito>

<quando_usar>
  <ativar_quando>
    - Usuário pede "jurisprudência do STF", "acórdão do Supremo", "monocrática do STF",
      "informativo do STF", "tese de repercussão geral", "súmula (vinculante)"
    - Precisa do ACERVO do STF (acórdão comum, monocrática, RE, informativo) — não só do
      precedente qualificado que o BNP traz
    - Um pipeline de peça/decisão precisa de precedente do STF com ementa citável
  </ativar_quando>
  <nao_usar_quando>
    - Só o precedente QUALIFICADO do STF (súmula vinculante, tema de RG, ADI/ADC/ADO/ADPF) →
      o BNP (via conector) já cobre e funciona sem navegador
    - Jurisprudência não-STF → bnp, tnu, tst, trfs, stj (conector/gateway)
    - Navegador indisponível → avisar (ver casos de borda); não há fallback
  </nao_usar_quando>
</quando_usar>

<instrucoes>
  <passo numero="0" nome="Preparar navegador e injetar o motor">
    1. `tabs_context_mcp` (createIfEmpty: true) para obter/abrir aba.
    2. `navigate` para
       `https://jurisprudencia.stf.jus.br/pages/search?base=acordaos&queryString=teste`
       e aguardar ~8s (`computer` wait) — o SPA carrega e o AWS WAF deposita o cookie
       `aws-waf-token`.
    3. Verificar prontidão via `javascript_tool`:
       `document.cookie.includes('aws-waf-token')`. Se `false`, esperar mais 5s e repetir 1x.
    4. Injetar o motor: `Read` de `references/engine.js` e colar TODO o conteúdo em UM
       `javascript_tool` (define `window.__stfSearch`). Confirmar retorno `'engine STF pronto'`.
  </passo>

  <passo numero="1" nome="Interpretar o pedido → montar opts">
    - `busca`: a expressão. `E/OU/NAO`, `"frase"`, `"..."~N`, `$`/`?` (curinga), `()` — passa
      direto (o motor do STF os entende). Evite algarismos romanos e hífens (digite 9, não IX).
    - `base`: `acordaos` (pad.) | `repercussao-geral` | `sumulas` | `decisoes` (monocráticas)
      | `informativos`.
    - `ministro` (relator), `dataInicio`/`dataFim` (DDMMAAAA), `tamanho` (pad. 10), `pagina`.
  </passo>

  <passo numero="2" nome="Executar a busca">
    Rodar em UM `javascript_tool`:
    `JSON.stringify(await window.__stfSearch({ ...opts }))`
    Devolve `{consulta, base, total, itens[]}`. Se vier `{erro, status:202}`, a cancela WAF
    expirou → re-navegar (passo 0.2) + reinjetar o motor + repetir. Se `total` alto, pagine —
    não despeje centenas de itens.
  </passo>

  <passo numero="3" nome="Formatar a saída — SEMPRE com procedência">
    - **buscar** (padrão): XML `<jurisprudencia_stf>` (ver `<conhecimento>`).
    - **gerar_relatorio**: Markdown com o BLOCO DE CITAÇÃO por item:
      ```
      REFERÊNCIA   STF, <classe> <numero>, Rel. Min. <relator>, <órgão>, j. <data_julg>, DJe <data_pub>.
      EMENTA       <ementa verbatim, recuada>
      PROCEDÊNCIA  STF (oficial) · inteiro teor: <link do PDF | "não disponível (< 2012)"> ·
                   cobertura da base: acórdãos desde 06/07/1950 · consultado em <data>.
      ```
    - **listar_filtros**: bases, operadores (de `references/sintaxe-booleana.md`), filtros.
    Regras de PROCEDÊNCIA (contrato-epistemico): ementa sempre VERBATIM (nunca de memória);
    súmula com `vinculante` sinalizada; se a base é `informativos`, marcar "(informativo — sem
    valor oficial)". `total=0` = "não encontrado nesta base/sintaxe", NUNCA "não existe".
  </passo>

  <passo numero="4" nome="Retorno conciso">
    Só o essencial: consulta efetiva, total, os itens formatados com procedência. Não retornar
    o JSON cru nem logs do navegador.
  </passo>
</instrucoes>

<conhecimento>
  <topico nome="Arquitetura e endpoint">
    SPA sobre Elasticsearch. Front: `jurisprudencia.stf.jus.br`. Busca (mesma origem):
    `POST /api/search/search` com Query DSL (`function_score` + `post_filter` por base). Inteiro
    teor: campo `inteiro_teor_url` → PDF em `portal.stf.jus.br/.../obterInteiroTeor.asp`
    (acórdãos de ~2012 em diante). Detalhes em `references/engenharia-reversa.md`.
  </topico>
  <topico nome="AWS WAF (o motivo da skill)">
    A API responde HTTP 202 (`x-amzn-waf-action: challenge`) sem o cookie `aws-waf-token`. Um
    navegador real, ao carregar a página, resolve o proof-of-work silencioso e deposita o
    cookie; o fetch de mesma origem passa a receber 200. O cookie dura ~minutos — em 202,
    re-navegar. NÃO usar navegador headless-shell (o WAF rejeita com 403); o navegador do
    Cowork/Chrome MCP é real, então passa.
  </topico>
  <topico nome="opts do motor window.__stfSearch">
    `busca` (str) · `base` ('acordaos'|'repercussao-geral'|'sumulas'|'decisoes'|'informativos')
    · `ministro` (relator) · `dataInicio`/`dataFim` (DDMMAAAA) · `pagina` (1…) · `tamanho`
    (pad. 10). Item devolvido: `numero, tipo, orgao, relator, dataJulgamento, dataPublicacao,
    uf, isRepercussaoGeral, sumulaNumero, isVinculante, tema, tese, ementa (verbatim),
    inteiroTeorUrl, acompanhamentoUrl`.
  </topico>
  <topico nome="Formato XML de saída (modo buscar)">
    ```xml
    <jurisprudencia_stf base="acordaos" total="N">
      <item indice="1">
        <numero>RE 795467 RG</numero>
        <orgao>Tribunal Pleno</orgao>
        <relator>TEORI ZAVASCKI</relator>
        <data_julgamento>05/06/2014</data_julgamento>
        <repercussao_geral>sim</repercussao_geral>
        <tese>...</tese>
        <ementa>... (verbatim) ...</ementa>
        <inteiro_teor>https://portal.stf.jus.br/.../obterInteiroTeor.asp?idDocumento=...</inteiro_teor>
        <procedencia>STF oficial · inteiro teor disponível · acervo desde 1950</procedencia>
      </item>
    </jurisprudencia_stf>
    ```
  </topico>
  <topico nome="Fronteira com o BNP">
    BNP = precedente QUALIFICADO do STF (súmula, vinculante, tema de RG, ADI/ADC/ADO/ADPF), via
    conector, sem navegador. Esta skill = ACERVO vivo (acórdão comum, monocrática, RE,
    informativo). Para "qual a tese fixada", prefira o BNP; para pesquisar precedentes por tema,
    use esta.
  </topico>
</conhecimento>

<exemplos>
  <exemplo cenario="Acórdãos do STF sobre liberdade de expressão">
    <entrada>Ache no STF acórdãos sobre "liberdade de expressão" e imprensa</entrada>
    <saida>
      opts = { busca:'"liberdade de expressao" E imprensa', base:'acordaos', tamanho:10 }
      → XML com acórdãos, relator, data, ementa verbatim, inteiro teor e procedência.
    </saida>
  </exemplo>
  <exemplo cenario="Tese de repercussão geral">
    <entrada>Qual a tese de RG sobre registro na Ordem dos Músicos?</entrada>
    <saida>
      opts = { busca:'ordem dos musicos', base:'repercussao-geral', tamanho:5 }
      → RE 795467 RG (Tema 738), com a tese fixada, verbatim.
    </saida>
  </exemplo>
  <exemplo cenario="Súmula por tema">
    <entrada>Súmula do STF sobre uso de algemas</entrada>
    <saida>
      opts = { busca:'algemas', base:'sumulas' } → Súmula Vinculante 11, sinalizada como
      vinculante.
    </saida>
  </exemplo>
  <exemplo cenario="Monocráticas de um ministro">
    <entrada>Decisões monocráticas do Min. Barroso sobre saúde</entrada>
    <saida>
      opts = { busca:'saude', base:'decisoes', ministro:'BARROSO', tamanho:10 } → relatório MD.
    </saida>
  </exemplo>
</exemplos>

<casos_de_borda>
  <caso nome="Navegador indisponível">
    <problema>tabs_context_mcp falha ou o navegador não está conectado.</problema>
    <solucao>Avisar que a busca do STF depende do navegador real (por causa do AWS WAF e do
    bloqueio de IP/allowlist). Sem fallback. Para o precedente qualificado, sugerir o BNP.</solucao>
  </caso>
  <caso nome="Cancela WAF (HTTP 202)">
    <problema>`{erro, status:202}` — o cookie aws-waf-token expirou (aba ociosa).</problema>
    <solucao>Re-navegar ao portal (passo 0.2) + wait 8s + reinjetar `engine.js` + repetir a
    busca. O motor já tenta 2x por chamada antes de devolver o erro.</solucao>
  </caso>
  <caso nome="Muitos resultados">
    <problema>`total` na casa dos milhares.</problema>
    <solucao>Refinar (frase exata, base específica, ministro, faixa de data) e paginar; reportar
    o total e mostrar os N mais recentes; nunca despejar centenas.</solucao>
  </caso>
  <caso nome="Inteiro teor ausente (pré-2012)">
    <problema>`inteiroTeorUrl` vazio em acórdãos antigos.</problema>
    <solucao>Na PROCEDÊNCIA, marcar "inteiro teor não disponível (acórdão anterior a ~2012)";
    usar o `acompanhamentoUrl` quando houver. Degradação honesta.</solucao>
  </caso>
</casos_de_borda>

<referencias>
  - [references/engine.js](references/engine.js) - Motor in-page (garante WAF + fetch ES + parse)
  - [references/sintaxe-booleana.md](references/sintaxe-booleana.md) - Operadores e bases do STF
  - [references/engenharia-reversa.md](references/engenharia-reversa.md) - API, WAF, campos, PDF
</referencias>

<pre_requisitos>
  - Navegador real (Chrome MCP / "Claude no Chrome") conectado, com acesso a jurisprudencia.stf.jus.br
</pre_requisitos>
