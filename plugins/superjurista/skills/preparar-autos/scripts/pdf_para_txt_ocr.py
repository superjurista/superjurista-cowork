#!/usr/bin/env python3
"""pdf_para_txt_ocr.py - Autos judiciais em PDF -> processo.txt (SuperJurista).

Processos judiciais misturam paginas nativas e digitalizadas; a extracao
digital "rapida" perde as digitalizadas EM SILENCIO (41% das paginas num caso
real). Este script nunca degrada em silencio — ele escolhe entre DUAS rotas
declaradas:

ROTA OCR (preferida): rasteriza cada pagina (poppler) e aplica Tesseract em
portugues. O idioma "por" vem do sistema OU do tessdata EMBARCADO no plugin
(skills/preparar-autos/tessdata/por.traineddata) — funciona sem rede desde que
o binario tesseract exista.

ROTA HIBRIDA (contingencia sem tesseract): extrai o texto NATIVO pagina a
pagina, detecta as paginas digitalizadas (sem camada de texto), renderiza cada
uma como PNG em scans/ e grava um marcador explicito no processo.txt:
    --- PAGINA N (DIGITALIZADA - TRANSCREVER de scans/pNNNN.png) ---
Quem chama (a skill preparar-autos) DEVE transcrever cada PNG por leitura
visual e substituir o marcador por "(DIGITALIZADA - TRANSCRICAO)" + o texto.
Nenhuma pagina fica sem texto; nenhuma pendencia fica invisivel.

Uso:
  python pdf_para_txt_ocr.py --input processo.pdf --output pasta/processo.txt
      [--modo auto|ocr|hibrido] [--dpi 300] [--verbose]
  python pdf_para_txt_ocr.py --check          # diagnostico de capacidades
  exit 0: convertido (hibrido pode ter [PENDENTE]); 2: erro de uso/dependencia

Saida (padrao minimo): [INICIO] ... [ROTA] ... [PENDENTE]* ... [FIM] ...
"""
import argparse
import glob
import io
import os
import re
import shutil
import subprocess
import sys

# Pagina digitalizada no PJe NAO tem camada de texto vazia: o sistema carimba
# numeracao, assinatura eletronica e URL de verificacao (~250 chars) sobre a
# imagem. Medir o texto BRUTO classifica errado (perda silenciosa da pagina
# escaneada — armadilha encontrada em caso real). Por isso: remove-se o
# boilerplate do PJe e mede-se o que sobra.
RE_BOILERPLATE_PJE = re.compile(
    r"^\s*(Num\.\s*\d+\s*-\s*P\S{0,3}g\.\s*\d+.*|Assinado eletronicamente por:.*|"
    r"N\S{0,3}mero do documento:.*|https?://\S+.*)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
LIMIAR_NATIVO = 100  # chars UTEIS (pos-boilerplate) para considerar a pagina nativa


def texto_util(texto):
    return RE_BOILERPLATE_PJE.sub("", texto or "").strip()


def _achar_poppler():
    """Dir bin do poppler quando fora do PATH; None se pdftoppm ja esta no PATH."""
    if shutil.which("pdftoppm"):
        return None
    padroes = (
        os.path.expanduser("~/poppler/*/Library/bin"),
        os.path.expanduser("~/poppler/*/bin"),
        r"C:\Program Files\poppler*\Library\bin",
        r"C:\Program Files\poppler*\bin",
    )
    for padrao in padroes:
        achados = sorted(glob.glob(padrao))
        if achados:
            return achados[-1]
    return None


POPPLER = _achar_poppler()


def _bin_poppler(nome):
    """Caminho executavel de uma ferramenta poppler, ou None se indisponivel."""
    if shutil.which(nome):
        return nome
    if POPPLER:
        cand = os.path.join(POPPLER, nome + (".exe" if os.name == "nt" else ""))
        if os.path.exists(cand):
            return cand
    return None


def _dir_tessdata_embarcado():
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tessdata")
    d = os.path.abspath(d)
    return d if os.path.exists(os.path.join(d, "por.traineddata")) else None


def _achar_tesseract():
    """Binario tesseract: PATH primeiro, depois locais padrao (Windows/Linux/mac)."""
    if shutil.which("tesseract"):
        return "tesseract"
    candidatos = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
    )
    for cand in candidatos:
        if os.path.exists(cand):
            return cand
    return None


def resolver_ocr():
    """(config_tesseract, origem_do_idioma) se OCR em portugues for possivel; senao None."""
    try:
        import pytesseract
    except ImportError:
        return None
    binario = _achar_tesseract()
    if not binario:
        return None
    pytesseract.pytesseract.tesseract_cmd = binario
    try:
        langs = pytesseract.get_languages(config="")
    except Exception:
        langs = []
    if "por" in langs:
        return ("", "sistema")
    td = _dir_tessdata_embarcado()
    if td:
        return (f'--tessdata-dir "{td}"', "embarcado no plugin")
    return None


def extrator_nativo():
    """Funcao (pdf, pagina)->texto usando pypdf/PyPDF2 ou pdftotext; None se nada existir."""
    try:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader
        leitores = {}

        def por_pypdf(pdf, pagina):
            if pdf not in leitores:
                leitores[pdf] = PdfReader(pdf)
            return leitores[pdf].pages[pagina - 1].extract_text() or ""
        return por_pypdf
    except ImportError:
        pass
    pdftotext = _bin_poppler("pdftotext")
    if pdftotext:
        def por_pdftotext(pdf, pagina):
            r = subprocess.run([pdftotext, "-f", str(pagina), "-l", str(pagina),
                                "-layout", pdf, "-"], capture_output=True)
            return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else ""
        return por_pdftotext
    return None


def renderizador():
    """Funcao (pdf, pagina, destino_png, dpi)->bool; None se nada existir."""
    try:
        from pdf2image import convert_from_path

        def por_pdf2image(pdf, pagina, destino, dpi):
            imgs = convert_from_path(pdf, dpi=dpi, poppler_path=POPPLER, first_page=pagina, last_page=pagina)
            imgs[0].save(destino, "PNG")
            return True
        return por_pdf2image
    except ImportError:
        pass
    pdftoppm = _bin_poppler("pdftoppm")
    if pdftoppm:
        def por_pdftoppm(pdf, pagina, destino, dpi):
            base = destino[:-4] if destino.lower().endswith(".png") else destino
            r = subprocess.run([pdftoppm, "-png", "-r", str(dpi), "-f", str(pagina),
                                "-l", str(pagina), "-singlefile", pdf, base],
                               capture_output=True)
            return r.returncode == 0 and os.path.exists(base + ".png")
        return por_pdftoppm
    try:
        import fitz  # PyMuPDF

        def por_fitz(pdf, pagina, destino, dpi):
            doc = fitz.open(pdf)
            pix = doc[pagina - 1].get_pixmap(dpi=dpi)
            pix.save(destino)
            doc.close()
            return True
        return por_fitz
    except ImportError:
        return None


def contar_paginas(pdf):
    try:
        from pdf2image import pdfinfo_from_path
        return int(pdfinfo_from_path(pdf, poppler_path=POPPLER).get("Pages", 0))
    except Exception:
        pass
    try:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader
        return len(PdfReader(pdf).pages)
    except Exception:
        pass
    pdfinfo = _bin_poppler("pdfinfo")
    if pdfinfo:
        r = subprocess.run([pdfinfo, pdf], capture_output=True)
        for linha in r.stdout.decode("utf-8", errors="replace").splitlines():
            if linha.startswith("Pages:"):
                return int(linha.split()[-1])
    return 0


def diagnostico():
    ocr = resolver_ocr()
    print("[CHECK] capacidades do ambiente:")
    print(f"  OCR portugues: {'SIM (' + ocr[1] + ')' if ocr else 'NAO'}")
    print(f"  tessdata embarcado: {_dir_tessdata_embarcado() or 'ausente'}")
    print(f"  poppler: {POPPLER or ('PATH' if shutil.which('pdftoppm') else 'ausente')}")
    print(f"  extrator de texto nativo: {'SIM' if extrator_nativo() else 'NAO'}")
    print(f"  renderizador de pagina: {'SIM' if renderizador() else 'NAO'}")
    rota = "ocr" if ocr else ("hibrido" if extrator_nativo() and renderizador() else "NENHUMA")
    print(f"  rota em --modo auto: {rota}")
    sys.exit(0 if rota != "NENHUMA" else 2)


def rota_ocr(a, total, config, origem):
    import pytesseract
    from pdf2image import convert_from_path
    print(f"[ROTA] ocr (idioma por: {origem})")
    ok, falhas = 0, 0
    with open(a.output, "w", encoding="utf-8") as saida:
        for pagina in range(1, total + 1):
            try:
                imgs = convert_from_path(a.input, dpi=a.dpi, poppler_path=POPPLER,
                                         first_page=pagina, last_page=pagina)
                texto = pytesseract.image_to_string(imgs[0], lang="por", config=config)
                saida.write(f"\n--- PAGINA {pagina} ---\n{texto}\n")
                ok += 1
                if a.verbose:
                    print(f"[OK] pagina {pagina}: {len(texto)} chars")
            except Exception as e:
                falhas += 1
                saida.write(f"\n--- PAGINA {pagina} (FALHA OCR) ---\n")
                print(f"[ERRO] pagina {pagina}: {e}")
    print(f"[FIM] {ok}/{total} paginas OK, {falhas} falhas -> {a.output}")
    return 0 if ok > 0 else 2


def rota_hibrida(a, total):
    extrair = extrator_nativo()
    render = renderizador()
    if not extrair or not render:
        faltas = []
        if not extrair:
            faltas.append("extrator de texto (pypdf/PyPDF2 ou pdftotext)")
        if not render:
            faltas.append("renderizador (pdf2image, pdftoppm ou PyMuPDF)")
        print(f"[ERRO] rota hibrida indisponivel: falta {' e '.join(faltas)}")
        sys.exit(2)
    print("[ROTA] hibrida (texto nativo + paginas digitalizadas para transcricao visual)")
    dir_scans = os.path.join(os.path.dirname(os.path.abspath(a.output)), "scans")
    os.makedirs(dir_scans, exist_ok=True)
    ok, pendentes, falhas = 0, [], 0
    with open(a.output, "w", encoding="utf-8") as saida:
        for pagina in range(1, total + 1):
            try:
                texto = extrair(a.input, pagina)
                if len(texto_util(texto)) >= LIMIAR_NATIVO:
                    saida.write(f"\n--- PAGINA {pagina} ---\n{texto}\n")
                    ok += 1
                    continue
                png = os.path.join(dir_scans, f"p{pagina:04d}.png")
                if render(a.input, pagina, png, a.dpi):
                    rel = os.path.join("scans", os.path.basename(png))
                    saida.write(f"\n--- PAGINA {pagina} (DIGITALIZADA - TRANSCREVER de {rel}) ---\n")
                    pendentes.append(pagina)
                else:
                    raise RuntimeError("renderizacao falhou")
            except Exception as e:
                falhas += 1
                saida.write(f"\n--- PAGINA {pagina} (FALHA) ---\n")
                print(f"[ERRO] pagina {pagina}: {e}")
    if pendentes:
        print(f"[PENDENTE] {len(pendentes)} paginas digitalizadas aguardam TRANSCRICAO VISUAL "
              f"(PNGs em {dir_scans}): paginas {pendentes[0]}..{pendentes[-1]}")
        print("[PENDENTE] substitua cada marcador TRANSCREVER pelo texto transcrito, "
              "marcado como (DIGITALIZADA - TRANSCRICAO)")
    print(f"[FIM] {ok} nativas + {len(pendentes)} digitalizadas, {falhas} falhas -> {a.output}")
    return 0 if (ok + len(pendentes)) > 0 else 2


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Autos PDF -> TXT (SuperJurista): OCR por, com rota hibrida declarada.")
    ap.add_argument("--input", help="caminho do PDF dos autos")
    ap.add_argument("--output", help="caminho do processo.txt de saida")
    ap.add_argument("--modo", choices=["auto", "ocr", "hibrido"], default="auto",
                    help="auto: OCR se disponivel, senao hibrida com aviso; ocr: estrito; hibrido: forca")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--check", action="store_true", help="so diagnostica capacidades e sai")
    ap.add_argument("--verbose", "-v", action="store_true")
    a = ap.parse_args()

    if a.check:
        diagnostico()
    if not a.input or not a.output:
        print("[ERRO] --input e --output sao obrigatorios (ou use --check)")
        sys.exit(2)
    if not os.path.exists(a.input):
        print(f"[ERRO] PDF inexistente: {a.input}")
        sys.exit(2)

    total = contar_paginas(a.input)
    if total <= 0:
        print("[ERRO] nao foi possivel contar as paginas (instale pypdf, pdf2image ou poppler-utils)")
        sys.exit(2)
    print(f"[INICIO] {total} paginas -> {os.path.basename(a.output)}")
    os.makedirs(os.path.dirname(os.path.abspath(a.output)) or ".", exist_ok=True)

    ocr = resolver_ocr() if a.modo in ("auto", "ocr") else None
    if a.modo == "ocr" and not ocr:
        print("[ERRO] OCR em portugues indisponivel (tesseract ausente ou sem 'por'; "
              "o plugin embarca tessdata/por.traineddata — basta o binario tesseract). "
              "Use --modo hibrido para a rota de contingencia.")
        sys.exit(2)
    if ocr:
        sys.exit(rota_ocr(a, total, ocr[0], ocr[1]))
    if a.modo == "auto":
        print("[AVISO] tesseract com portugues indisponivel — caindo para a rota HIBRIDA "
              "(nenhuma pagina se perde: digitalizadas viram pendencia explicita de transcricao)")
    sys.exit(rota_hibrida(a, total))


if __name__ == "__main__":
    main()
