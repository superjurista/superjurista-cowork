---
name: preparar-autos
description: Converte autos judiciais em PDF para texto (processo.txt) via OCR — etapa local obrigatória antes de qualquer pipeline do SuperJurista quando a entrada é PDF. Use quando o usuário fornecer um processo em PDF ou pedir para preparar/converter os autos. SEMPRE OCR — a extração digital perde páginas escaneadas de processos judiciais.
compatibility: Requer Python 3.8+, poppler-utils e tesseract-ocr com idioma português (instaláveis no ambiente de execução); acesso de leitura ao PDF dos autos.
metadata:
  author: superjurista
  version: "1.0.0"
---

# Preparar Autos (PDF → processo.txt via OCR)

Processos judiciais misturam páginas nativas e digitalizadas. A extração
digital "rápida" já perdeu 41% das páginas num caso real — por isso o padrão
desta skill é OCR SEMPRE, sem fallback silencioso.

## Execução

1. Instale as dependências se necessário (ambiente Linux do Cowork):
   ```bash
   sudo apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-por 2>/dev/null || apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-por
   pip install pdf2image pytesseract pillow
   ```
2. Rode o conversor:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/skills/preparar-autos/scripts/pdf_para_txt_ocr.py \
     --input <caminho/do/processo.pdf> --output <pasta-do-caso>/processo.txt
   ```
3. Confira o resultado impresso (`[FIM] N páginas -> processo.txt`). Falha de
   dependência interrompe com instrução de instalação — não caia para
   extração digital por conta própria.

## Regras

- Saída canônica: `processo.txt` na pasta do caso (workspace dos pipelines).
- Nunca resuma nem "limpe" o texto: os gates de citação verificam VERBATIM
  contra este arquivo — ele é a fonte da verdade dos autos.
- PDFs grandes: o script processa página a página; deixe terminar.
