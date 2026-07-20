---
name: preparar-autos
description: Converte autos judiciais em PDF para texto (processo.txt) — etapa local obrigatória antes de qualquer pipeline do SuperJurista quando a entrada é PDF. Use quando o usuário fornecer um processo em PDF ou pedir para preparar/converter os autos. Rota preferida é OCR em português (tessdata embarcado no plugin, funciona sem rede); sem tesseract, rota híbrida declarada (texto nativo + transcrição visual das páginas digitalizadas). NUNCA extração digital pura — ela perde páginas escaneadas em silêncio.
compatibility: Requer Python 3.8+. Rota OCR usa poppler + tesseract (o idioma português já vem EMBARCADO no plugin — basta o binário tesseract, sem rede). Sem tesseract, a rota híbrida usa qualquer extrator (pypdf/PyPDF2/pdftotext) + renderizador (pdf2image/pdftoppm/PyMuPDF) e delega as páginas digitalizadas à transcrição visual.
metadata:
  author: superjurista
  version: "1.1.0"
---

# Preparar Autos (PDF → processo.txt)

Processos judiciais misturam páginas nativas e digitalizadas. A extração
digital "rápida" já perdeu 41% das páginas num caso real — e no PJe a página
digitalizada NÃO tem camada de texto vazia (o sistema carimba numeração e
assinatura sobre a imagem), o que engana qualquer verificação ingênua. Por
isso o conversor decide por rotas DECLARADAS, nunca degrada em silêncio.

## Passo 0 — Diagnóstico

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/preparar-autos/scripts/pdf_para_txt_ocr.py --check
```

Mostra o que o ambiente tem (tesseract? português? poppler? extrator?
renderizador?) e qual rota o `--modo auto` vai usar. Se faltar tudo E houver
rede, instale (`apt-get install -y poppler-utils tesseract-ocr` + `pip install
pdf2image pytesseract pypdf pillow`) — o idioma português NÃO precisa ser
instalado: `tessdata/por.traineddata` já vem no plugin.

## Passo 1 — Conversão

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/preparar-autos/scripts/pdf_para_txt_ocr.py \
  --input <caminho/do/processo.pdf> --output <pasta-do-caso>/processo.txt
```

- **Rota OCR** (`[ROTA] ocr`): melhor caso — todas as páginas OCR-izadas em
  português. Nada mais a fazer.
- **Rota híbrida** (`[ROTA] hibrida`, quando não há tesseract): páginas
  nativas entram direto; páginas digitalizadas viram PNG em `scans/` e um
  marcador explícito no processo.txt:
  `--- PAGINA N (DIGITALIZADA - TRANSCREVER de scans/pNNNN.png) ---`

## Passo 2 — Transcrição visual (só na rota híbrida, obrigatório)

Para CADA página `[PENDENTE]`: leia o PNG (Read tool) e transcreva o conteúdo
LITERALMENTE — íntegra, sem resumir, sem interpretar. Substitua o marcador por:

```
--- PAGINA N (DIGITALIZADA - TRANSCRICAO) ---
<texto transcrito integral da página>
```

Muitas páginas? Despache subagentes em lotes (ex.: 15 páginas por subagente),
cada um transcrevendo e editando seu trecho do processo.txt.

## Passo 3 — Verificação final (gate manual)

```bash
grep -c "TRANSCREVER" <pasta-do-caso>/processo.txt   # DEVE ser 0
```

Restou marcador TRANSCREVER → o preparo NÃO terminou. Nenhuma página pode
ficar sem texto: os gates de citação verificam VERBATIM contra este arquivo —
ele é a fonte da verdade dos autos.

## Regras

- Saída canônica: `processo.txt` na pasta do caso (workspace dos pipelines).
- Nunca resuma nem "limpe" o texto; transcrição visual é LITERAL.
- Registre no relato ao usuário qual rota foi usada e quantas páginas foram
  transcritas visualmente (transparência de proveniência).
- PDFs grandes: o script processa página a página; deixe terminar.
