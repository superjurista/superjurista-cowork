#!/usr/bin/env python3
"""pdf_para_txt_ocr.py - Autos judiciais em PDF -> processo.txt via OCR.

SEMPRE OCR: processos judiciais misturam paginas nativas e digitalizadas, e a
extracao digital perde as digitalizadas em silencio (41% das paginas num caso
real). Este script rasteriza cada pagina (poppler) e aplica Tesseract (por).

Sem fallback silencioso: dependencia ausente interrompe com a instrucao de
instalacao — quem chama decide, nunca o script decide degradar sozinho.

Uso:
  python pdf_para_txt_ocr.py --input processo.pdf --output pasta/processo.txt
      [--dpi 300] [--lang por] [--verbose]
  exit 0: convertido; 2: erro de uso/dependencia
"""
import argparse
import os
import sys


def _falha_dependencia(pacote, extra=""):
    print(f"[ERRO] dependencia ausente: {pacote}")
    print("       instale: pip install pdf2image pytesseract pillow")
    print("       sistema: apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-por")
    if extra:
        print(f"       detalhe: {extra}")
    sys.exit(2)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Autos PDF -> TXT via OCR (SuperJurista).")
    ap.add_argument("--input", required=True, help="caminho do PDF dos autos")
    ap.add_argument("--output", required=True, help="caminho do processo.txt de saida")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--lang", default="por")
    ap.add_argument("--verbose", "-v", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.input):
        print(f"[ERRO] PDF inexistente: {a.input}")
        sys.exit(2)

    try:
        from pdf2image import convert_from_path, pdfinfo_from_path
    except ImportError as e:
        _falha_dependencia("pdf2image", str(e))
    try:
        import pytesseract
    except ImportError as e:
        _falha_dependencia("pytesseract", str(e))

    try:
        info = pdfinfo_from_path(a.input)
        total = int(info.get("Pages", 0))
    except Exception as e:
        _falha_dependencia("poppler-utils (pdftoppm/pdfinfo no PATH)", str(e))

    print(f"[INICIO] {total} paginas -> {os.path.basename(a.output)}")
    os.makedirs(os.path.dirname(os.path.abspath(a.output)) or ".", exist_ok=True)

    ok, falhas = 0, 0
    with open(a.output, "w", encoding="utf-8") as saida:
        for pagina in range(1, total + 1):
            try:
                imgs = convert_from_path(a.input, dpi=a.dpi,
                                         first_page=pagina, last_page=pagina)
                texto = pytesseract.image_to_string(imgs[0], lang=a.lang)
                saida.write(f"\n--- PAGINA {pagina} ---\n{texto}\n")
                ok += 1
                if a.verbose:
                    print(f"[OK] pagina {pagina}: {len(texto)} chars")
            except Exception as e:
                falhas += 1
                saida.write(f"\n--- PAGINA {pagina} (FALHA OCR) ---\n")
                print(f"[ERRO] pagina {pagina}: {e}")

    print(f"[FIM] {ok}/{total} paginas OK, {falhas} falhas -> {a.output}")
    sys.exit(0 if ok > 0 else 2)


if __name__ == "__main__":
    main()
