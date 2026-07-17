#!/usr/bin/env python3
"""gerar_relatorio_sessao_html.py - Relatorio HTML da sessao (SuperJurista Cowork).

Etapa final DETERMINISTICA do pipeline analisar-sessao: le os contratos JSON
(bloco ```json ao fim de cada artefato MD), agrega por ESCADA DE CORES e
renderiza um HTML autocontido para o gabinete.

Proveniencia: a escada de cores, o mapa de acoes e a paleta vem do motor da
fabrica supercordelia (scripts/consolidar.py e _estilos.py) — "sem LLM, 100%
deterministico: a inteligencia ja foi gasta nos agentes; aqui e aritmetica de
cores". Este script e uma versao SIMPLIFICADA declarada:

  Escada:  VERMELHO(4) > AMARELO(3) > CINZA(2) > VERDE(1) > BRANCO(0)
  Acao:    VERMELHO=DECIDIR  AMARELO=DEBATER  CINZA=CORRIGIR  VERDE/BRANCO=SEGUIR
  Frentes -> cor:
    cruzada:        CONFLITO->VERMELHO   COERENTE->VERDE
    jurisprudencia: CONTRARIA->VERMELHO  CAMPO_DIVIDIDO->AMARELO
                    ALINHADA->VERDE      SEM_PARAMETRO->BRANCO
                    (sem busca: BRANCO, com nota "economico")
    sensibilidade:  SENSIVEL->VERMELHO   ATENCAO->AMARELO   ROTINA->VERDE
    incoerencia:    ACHADO->AMARELO      OK->VERDE
    erros:          ACHADO->CINZA        OK->VERDE
  Cor final da ementa = max(frentes); canal dominante = primeira frente da
  PRIORIDADE cuja cor iguala a final.

Le  <workspace>/<id>-sessao-{teses,triagem,deteccao,jurisprudencia,cruzada}.md
Grava <workspace>/<id>-sessao-relatorio.html
Exit 0 = gerado; 1 = contrato JSON ausente/invalido em artefato; 2 = erro de uso.

Uso: python gerar_relatorio_sessao_html.py <workspace> [--id IDENT]
"""
import argparse
import html
import json
import os
import re
import sys
from datetime import datetime

RE_JSON = re.compile(r"```json\s*(.*?)```", re.DOTALL)

ESCADA = {"BRANCO": 0, "VERDE": 1, "CINZA": 2, "AMARELO": 3, "VERMELHO": 4}
NOME = {v: k for k, v in ESCADA.items()}
ACAO = {"VERMELHO": "DECIDIR", "AMARELO": "DEBATER", "CINZA": "CORRIGIR",
        "VERDE": "SEGUIR", "BRANCO": "SEGUIR"}
PRIORIDADE = ["cruzada", "jurisprudencia", "incoerencia", "sensibilidade", "erros"]
FRENTE_NOME = {"cruzada": "cruzada", "jurisprudencia": "tribunal",
               "incoerencia": "incoerência", "sensibilidade": "sensibilidade",
               "erros": "redação"}

# Paleta (proveniencia: supercordelia/_estilos.py)
COR_ACAO = {"DECIDIR": "#A12B22", "DEBATER": "#B07A1E", "CORRIGIR": "#7C8794", "SEGUIR": "#3E7256"}
COR_DOT = {"VERMELHO": "#A12B22", "AMARELO": "#B07A1E", "CINZA": "#7C8794",
           "VERDE": "#3E7256", "BRANCO": "#C9D1D9"}


def extrair_contrato(caminho):
    """Ultimo bloco ```json do arquivo -> dict; (None, motivo) se falhar."""
    if not os.path.exists(caminho):
        return None, "arquivo ausente"
    with open(caminho, encoding="utf-8") as f:
        blocos = RE_JSON.findall(f.read())
    if not blocos:
        return None, "sem bloco ```json (contrato)"
    try:
        return json.loads(blocos[-1]), None
    except json.JSONDecodeError as e:
        return None, f"JSON invalido: {e}"


def cor_frentes(n, deteccao, juris, triagem, cruzada):
    """Frentes da ementa n -> {frente: (COR, resumo)}."""
    f = {}
    d = next((e for e in deteccao.get("ementas", []) if e.get("n") == n), {})
    inc = (d.get("incoerencia") or {})
    err = (d.get("erros") or {})
    sen = (d.get("sensibilidade") or {})
    f["incoerencia"] = ("AMARELO" if inc.get("status") == "ACHADO" else "VERDE",
                        inc.get("resumo") or "")
    f["erros"] = ("CINZA" if err.get("status") == "ACHADO" else "VERDE",
                  err.get("resumo") or "")
    sens_cor = {"SENSIVEL": "VERMELHO", "ATENCAO": "AMARELO"}.get(sen.get("status"), "VERDE")
    f["sensibilidade"] = (sens_cor, sen.get("razao") or "")

    sem_busca = {x.get("n"): x.get("razao", "") for x in triagem.get("sem_busca", [])
                 if isinstance(x, dict)}
    if n in sem_busca:
        f["jurisprudencia"] = ("BRANCO", f"sem busca (econômico): {sem_busca[n]}")
    else:
        j = next((e for e in juris.get("ementas", []) if e.get("n") == n), None)
        mapa = {"CONTRARIA": "VERMELHO", "CAMPO_DIVIDIDO": "AMARELO",
                "ALINHADA": "VERDE", "SEM_PARAMETRO": "BRANCO"}
        if j:
            f["jurisprudencia"] = (mapa.get(j.get("situacao"), "BRANCO"),
                                   (j.get("resumo") or "") +
                                   (f" — {j['acordao_chave']}" if j.get("acordao_chave") else ""))
        else:
            f["jurisprudencia"] = ("BRANCO", "sem dado")

    grupo = next((g for g in cruzada.get("grupos", [])
                  if g.get("conflito") and n in (g.get("ementas") or [])), None)
    f["cruzada"] = (("VERMELHO", grupo.get("resumo", "")) if grupo else ("VERDE", ""))
    return f


def consolidar_ementa(tese, frentes):
    val = max(ESCADA[c] for c, _ in frentes.values())
    cor = NOME[val]
    canal = next((fr for fr in PRIORIDADE if ESCADA[frentes[fr][0]] == val), "erros")
    return {"n": tese.get("n"), "processo": tese.get("processo", ""),
            "recurso": tese.get("recurso", ""), "resultado": tese.get("resultado", ""),
            "tese": tese.get("tese_central", ""), "cor": cor, "acao": ACAO[cor],
            "canal": canal, "frentes": frentes}


def render(ident, ementas, triagem, cruzada):
    e_ = html.escape
    ordenadas = sorted(ementas, key=lambda x: (-ESCADA[x["cor"]], x["n"] or 0))
    cont = {}
    for em in ementas:
        cont[em["acao"]] = cont.get(em["acao"], 0) + 1
    tiles = "".join(
        f'<div class="tile" style="border-top:4px solid {COR_ACAO[a]}">'
        f'<div class="tnum">{cont.get(a, 0)}</div><div class="tlab">{a}</div></div>'
        for a in ("DECIDIR", "DEBATER", "CORRIGIR", "SEGUIR"))

    cards = []
    for em in ordenadas:
        linhas = []
        for fr in PRIORIDADE:
            cor, resumo = em["frentes"][fr]
            if cor in ("VERDE",) and not resumo:
                continue
            dom = " ◀ dominante" if fr == em["canal"] and em["cor"] != "VERDE" else ""
            linhas.append(
                f'<li><span class="dot" style="background:{COR_DOT[cor]}"></span>'
                f'<b>{FRENTE_NOME[fr]}</b>: {e_(resumo) or "sem achados"}{dom}</li>')
        corpo = "".join(linhas) or '<li><span class="dot" style="background:#3E7256"></span>sem achados — segue na rotina</li>'
        cards.append(f'''<div class="card" style="border-left:6px solid {COR_DOT[em["cor"]]}">
<div class="chead"><span class="enum">Ementa {em["n"]:02d}</span>
<span class="badge" style="background:{COR_ACAO[em["acao"]]}">{em["acao"]}</span></div>
<div class="cmeta">{e_(em["processo"])} · {e_(em["recurso"])} · {e_(em["resultado"])}</div>
<div class="ctese">{e_(em["tese"])}</div>
<ul class="frentes">{corpo}</ul>
</div>''')

    economia = "".join(
        f'<li>Ementa {x.get("n"):02d} — {e_(x.get("razao", ""))}</li>'
        for x in triagem.get("sem_busca", []) if isinstance(x, dict))
    conflitos = sum(1 for g in cruzada.get("grupos", []) if g.get("conflito"))
    gerado = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sessão {e_(ident)} — SuperJurista</title>
<style>
body{{font-family:Georgia,'Times New Roman',serif;background:#F6F4EF;color:#2B2B2B;margin:0;padding:2rem;max-width:960px;margin-inline:auto}}
h1{{font-size:1.5rem;border-bottom:3px double #A12B22;padding-bottom:.5rem}}
.sub{{color:#5E6B78;margin-bottom:1.5rem}}
.tiles{{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:2rem}}
.tile{{background:#fff;padding:.8rem 1.4rem;border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,.08);text-align:center;min-width:90px}}
.tnum{{font-size:1.8rem;font-weight:bold}}.tlab{{font-size:.75rem;letter-spacing:.08em;color:#5E6B78}}
.card{{background:#fff;border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,.08);padding:1rem 1.2rem;margin-bottom:1rem}}
.chead{{display:flex;justify-content:space-between;align-items:center}}
.enum{{font-weight:bold;font-size:1.05rem}}
.badge{{color:#fff;font-size:.72rem;letter-spacing:.1em;padding:.25rem .6rem;border-radius:3px}}
.cmeta{{color:#5E6B78;font-size:.85rem;margin:.25rem 0}}
.ctese{{font-style:italic;margin:.4rem 0 .6rem}}
.frentes{{list-style:none;padding:0;margin:0;font-size:.9rem}}
.frentes li{{margin:.25rem 0}}
.dot{{display:inline-block;width:.7em;height:.7em;border-radius:50%;margin-right:.5em}}
.economia{{background:#EAEEF1;border-radius:6px;padding:1rem 1.2rem;font-size:.9rem}}
footer{{margin-top:2rem;color:#9AA6B2;font-size:.75rem;border-top:1px solid #C9D1D9;padding-top:.8rem}}
</style>
</head>
<body>
<h1>Relatório da Sessão de Julgamento — {e_(ident)}</h1>
<div class="sub">{len(ementas)} ementas · {conflitos} conflito(s) de coerência cruzada · gerado em {gerado}</div>
<div class="tiles">{tiles}</div>
{"".join(cards)}
<div class="economia"><b>Economia registrada</b> (ED de rejeição sem busca externa — "na dúvida, busca"):
<ul>{economia or "<li>nenhuma — todas as ementas receberam busca</li>"}</ul>
Triagem por regra instruída com decisão auditável por ementa (a fábrica local usa script determinístico).</div>
<footer>Gerado deterministicamente por gerar_relatorio_sessao_html.py — escada de cores e paleta com proveniência do motor supercordelia (consolidar.py / _estilos.py). Detalhes completos nos artefatos .md da sessão.</footer>
</body>
</html>'''


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Relatorio HTML da sessao (deterministico).")
    ap.add_argument("workspace")
    ap.add_argument("--id", dest="ident", help="identificador (inferido do nome da pasta)")
    a = ap.parse_args()
    if not os.path.isdir(a.workspace):
        print(f"[ERRO] workspace inexistente: {a.workspace}")
        sys.exit(2)
    ident = a.ident or os.path.basename(os.path.abspath(a.workspace))

    artefatos, falhas = {}, []
    for nome in ("teses", "triagem", "deteccao", "jurisprudencia", "cruzada"):
        dados, erro = extrair_contrato(os.path.join(a.workspace, f"{ident}-sessao-{nome}.md"))
        if erro:
            falhas.append(f"{nome}: {erro}")
        artefatos[nome] = dados or {}
    print(f"[INICIO] sessao {ident} -> agregacao deterministica de {5 - len(falhas)}/5 contratos")
    for f in falhas:
        print(f"[ERRO] contrato {f}")
    if falhas:
        sys.exit(1)

    ementas = [consolidar_ementa(t, cor_frentes(t.get("n"), artefatos["deteccao"],
                                                artefatos["jurisprudencia"],
                                                artefatos["triagem"], artefatos["cruzada"]))
               for t in artefatos["teses"].get("ementas", [])]
    if not ementas:
        print("[ERRO] contrato de teses sem ementas")
        sys.exit(1)

    destino = os.path.join(a.workspace, f"{ident}-sessao-relatorio.html")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(render(ident, ementas, artefatos["triagem"], artefatos["cruzada"]))
    print(f"[FIM] {len(ementas)} ementas -> {os.path.basename(destino)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
