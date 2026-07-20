#!/usr/bin/env python3
"""verificar_autos_local.py - Gate LOCAL de citacoes dos autos (SuperJurista Cowork).

Fecha o buraco do regime verbatim na superficie remota: os AUTOS nao sobem ao
servidor, entao a citacao dos autos e verificada AQUI, na maquina do cliente.
Extrai cada trecho ENTRE ASPAS do documento e confere, por correspondencia
normalizada (acentos/caixa/espacos), se e copia exata dos autos
(processo.txt e/ou <numero>.txt no workspace).

Motor identico ao gate da fabrica local (verificar_citacoes.py do repo
superjurista), reduzido ao corpus dos autos e acrescido do VEREDITO em JSON
com sha256 do corpus — so o veredito (nunca os autos) pode subir ao dossie.

Trechos com corte interno ("(...)", "[...]", "...") sao divididos: cada
fragmento com >= LIMIAR chars normalizados deve constar do corpus. Aspas
curtas (expressoes idiomaticas, dispositivos legais breves) ficam fora do
regime.

ESCOPO POR REGIME (v1.2): este gate cobre SOMENTE as citacoes dos AUTOS.
Citacao que nao casa com o corpus mas tem REFERENCIA DE JURISPRUDENCIA
adjacente (tribunal, relator, numero CNJ de outro processo, data de
julgamento) pertence ao regime do CONECTOR — e verificada contra as buscas,
nao contra os autos — e sai do denominador, contada a parte no veredito
(citacoes_jurisprudencia). Citacao que nao casa e NAO tem referencia nenhuma
continua reprovando: aspas longas sem lastro declarado nao existem.

Uso:
  python verificar_autos_local.py <workspace> [--doc=-sentenca.md | --doc caminho]
      [--limiar 60] [--json saida.json]
  exit 0: todas conferem; 1: alguma citacao sem lastro; 2: erro de uso

ATENCAO: sufixo de --doc comeca com hifen — use a forma --doc=-sentenca.md.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone

LIMIAR_DEFAULT = 60
RE_CNJ = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
RE_ASPAS = re.compile(r'"([^"]+)"|“([^”]+)”', re.DOTALL)
RE_CORTE = re.compile(r"\(\s*\.\.\.\s*\)|\[\s*\.\.\.\s*\]|\(\s*…\s*\)|\[\s*…\s*\]|…|\.\.\.")
# Marcadores de referencia de jurisprudencia no ENTORNO da citacao (so sao
# consultados quando a citacao ja NAO casou com o corpus dos autos).
RE_JURIS = re.compile(
    r"TRF\s?-?\s?\d|STJ|STF|\bTNU\b|\bTRU\b|Turma\s+Recursal|S[úu]mula|"
    r"Tribunal\s+Regional\s+Federal|Superior\s+Tribunal\s+de\s+Justi|"
    r"Supremo\s+Tribunal\s+Federal|Turma\s+Nacional\s+de\s+Uniformiza|"
    r"Tema\s+\d|REsp|AgRg|AgInt|EDcl|EREsp|ApCiv|Agravo\s+de\s+Instrumento|"
    r"Rel\.|Relator|Min\.|Des\.|Desembargador|julgad[oa]\s+em|j\.\s*(?:em\s*)?\d{2}/\d{2}/\d{4}",
    re.IGNORECASE,
)
JANELA_ANTES = 300
JANELA_DEPOIS = 200
# Aspas separadas por ate GAP_GRUPO chars formam um BLOCO DE TRANSCRICAO
# (varias teses/paragrafos citados em sequencia compartilham a mesma
# referencia introdutoria — ex.: "...consignou, verbatim:" seguido de N aspas).
GAP_GRUPO = 200


def _norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").casefold()
    return re.sub(r"\s+", " ", s).strip()


def carregar_autos(workspace, ident):
    partes, arquivos = [], []
    for nome in ("processo.txt", ident + ".txt"):
        p = os.path.join(workspace, nome)
        if os.path.exists(p):
            with open(p, encoding="utf-8", errors="replace") as f:
                partes.append(f.read())
            arquivos.append(nome)
    return partes, arquivos


def _tem_referencia_jurisprudencia(doc_texto, inicio, fim, ident):
    janela = doc_texto[max(0, inicio - JANELA_ANTES):fim + JANELA_DEPOIS]
    if RE_JURIS.search(janela):
        return True
    # Numero CNJ de OUTRO processo na janela tambem e referencia (o numero do
    # proprio caso aparece perto de citacoes dos autos e nao conta).
    return any(n != ident for n in RE_CNJ.findall(janela))


def verificar(doc_texto, corpus_norm, limiar, ident):
    # Coleta as citacoes do regime com posicao e resultado no corpus.
    itens = []
    for m in RE_ASPAS.finditer(doc_texto):
        bruto = m.group(1) or m.group(2)
        relevantes = [f for f in RE_CORTE.split(bruto) if len(_norm(f)) >= limiar]
        if not relevantes:
            continue
        sem_lastro = [f for f in relevantes if _norm(f) not in corpus_norm]
        itens.append((m.start(), m.end(), bruto, sem_lastro))

    # Agrupa aspas consecutivas num bloco de transcricao: a referencia
    # introdutoria de um bloco vale para todas as aspas do bloco.
    grupos = []
    for item in itens:
        if grupos and item[0] - grupos[-1][-1][1] <= GAP_GRUPO:
            grupos[-1].append(item)
        else:
            grupos.append([item])

    problemas, conferidas, jurisprudencia = [], 0, 0
    for grupo in grupos:
        ref_juris = _tem_referencia_jurisprudencia(
            doc_texto, grupo[0][0], grupo[-1][1], ident)
        for _ini, _fim, bruto, sem_lastro in grupo:
            # 1) O corpus decide primeiro: casou, e citacao dos autos conferida.
            if not sem_lastro:
                conferidas += 1
            # 2) Nao casou, mas o bloco tem referencia de jurisprudencia ->
            #    regime do conector (verificada contra as buscas, nao os autos).
            elif ref_juris:
                jurisprudencia += 1
            # 3) Nem corpus, nem referencia: aspas sem lastro declarado.
            else:
                problemas.append((bruto, sem_lastro[0]))
    return problemas, conferidas, jurisprudencia


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Gate local de citacoes dos autos (SuperJurista).")
    ap.add_argument("workspace")
    ap.add_argument("--doc", default="-sentenca.md",
                    help="sufixo do documento (default -sentenca.md) ou caminho completo")
    ap.add_argument("--limiar", type=int, default=LIMIAR_DEFAULT)
    ap.add_argument("--json", dest="json_out",
                    help="grava o veredito em JSON neste caminho (default: <workspace>/<id>-autos-veredito.json)")
    a = ap.parse_args()

    if not os.path.isdir(a.workspace):
        print(f"[ERRO] workspace inexistente: {a.workspace}")
        sys.exit(2)
    base = os.path.basename(os.path.abspath(a.workspace))
    m = RE_CNJ.search(base)
    ident = m.group(0) if m else base

    doc = a.doc if (os.path.sep in a.doc or os.path.exists(a.doc)) \
        else os.path.join(a.workspace, ident + a.doc)
    if not os.path.exists(doc):
        print(f"[ERRO] documento inexistente: {doc}")
        sys.exit(2)

    autos_brutos, arquivos = carregar_autos(a.workspace, ident)
    if not autos_brutos:
        print("[ERRO] autos ausentes (nem processo.txt nem <numero>.txt no workspace)")
        sys.exit(2)

    corpus_norm = "  ".join(_norm(t) for t in autos_brutos)
    sha = hashlib.sha256("\n".join(autos_brutos).encode("utf-8")).hexdigest()

    with open(doc, encoding="utf-8") as f:
        texto = f.read()
    problemas, conferidas, jurisprudencia = verificar(texto, corpus_norm, a.limiar, ident)

    no_regime = conferidas + len(problemas)
    print(f"[INICIO] {os.path.basename(doc)} -> {no_regime} citacao(oes) no regime dos autos, "
          f"{jurisprudencia} no regime do conector (jurisprudencia)")
    for bruto, frag in problemas:
        resumo = re.sub(r"\s+", " ", frag).strip()[:120]
        print(f'[ERRO] citacao sem lastro nos autos nem referencia declarada: "{resumo}..."')

    veredito = {
        "veredito": "AUTOS_VERIFICADO_LOCAL" if not problemas else "AUTOS_REPROVADO_LOCAL",
        "documento": os.path.basename(doc),
        "citacoes_no_regime": no_regime,
        "citacoes_conferidas": conferidas,
        "citacoes_sem_lastro": len(problemas),
        "citacoes_jurisprudencia": jurisprudencia,
        "nota_jurisprudencia": "citacoes com referencia de jurisprudencia adjacente pertencem ao regime do conector (verificacao contra as buscas, nao contra os autos)",
        "limiar": a.limiar,
        "autos": arquivos,
        "sha256_autos": sha,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    destino = a.json_out or os.path.join(a.workspace, f"{ident}-autos-veredito.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(veredito, f, ensure_ascii=False, indent=2)

    print(f"[FIM] {veredito['citacoes_conferidas']}/{no_regime} conferidas nos autos, "
          f"{jurisprudencia} jurisprudencia (regime do conector) -> {os.path.basename(destino)}")
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
