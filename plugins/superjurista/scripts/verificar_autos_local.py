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


def verificar(doc_texto, corpus_norm, limiar):
    problemas, conferidas = [], 0
    for m in RE_ASPAS.finditer(doc_texto):
        bruto = m.group(1) or m.group(2)
        fragmentos = RE_CORTE.split(bruto)
        relevantes = [f for f in fragmentos if len(_norm(f)) >= limiar]
        if not relevantes:
            continue
        conferidas += 1
        for frag in relevantes:
            if _norm(frag) not in corpus_norm:
                problemas.append((bruto, frag))
                break
    return problemas, conferidas


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
    problemas, conferidas = verificar(texto, corpus_norm, a.limiar)

    print(f"[INICIO] {os.path.basename(doc)} -> {conferidas} citacao(oes) no regime dos autos")
    for bruto, frag in problemas:
        resumo = re.sub(r"\s+", " ", frag).strip()[:120]
        print(f'[ERRO] citacao sem lastro nos autos: "{resumo}..."')

    veredito = {
        "veredito": "AUTOS_VERIFICADO_LOCAL" if not problemas else "AUTOS_REPROVADO_LOCAL",
        "documento": os.path.basename(doc),
        "citacoes_no_regime": conferidas,
        "citacoes_conferidas": conferidas - len(problemas),
        "citacoes_sem_lastro": len(problemas),
        "limiar": a.limiar,
        "autos": arquivos,
        "sha256_autos": sha,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    destino = a.json_out or os.path.join(a.workspace, f"{ident}-autos-veredito.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(veredito, f, ensure_ascii=False, indent=2)

    print(f"[FIM] {veredito['citacoes_conferidas']}/{conferidas} conferidas -> {os.path.basename(destino)}")
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
