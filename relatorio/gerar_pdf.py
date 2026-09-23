"""Gera relatorio_av1.pdf a partir de relatorio_av1.html.

Passos:
  1. (Re)gera as figuras teoricas (relatorio/figuras/gerar_figuras.py).
  2. Renderiza o HTML em PDF usando um navegador Chromium (Edge ou Chrome) em
     modo headless.
  3. Pos-processa com PyMuPDF: cobre a faixa de cabecalho/rodape que o navegador
     insere na margem (data, URL, numero de pagina proprios) e carimba um rodape
     limpo com numeracao "Pagina X de N".

O navegador headless embute cabecalho/rodape proprios que as flags de linha de
comando ja nao suprimem de forma confiavel; essas faixas caem dentro da margem,
fora do conteudo, entao sao cobertas em branco sem tocar o texto.

Uso:
    python relatorio/gerar_pdf.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz  # PyMuPDF

AQUI = Path(__file__).resolve().parent
HTML = AQUI / "relatorio_av1.html"
SAIDA = AQUI / "relatorio_av1.pdf"

RODAPE = "Projeto e Análise de Algoritmos — AV1 · PROCC/UFS 2026.2"

CANDIDATOS_NAVEGADOR = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def achar_navegador() -> str:
    for nome in ("msedge", "chrome", "chromium", "google-chrome"):
        caminho = shutil.which(nome)
        if caminho:
            return caminho
    for caminho in CANDIDATOS_NAVEGADOR:
        if Path(caminho).exists():
            return caminho
    print("Navegador Chromium (Edge/Chrome) nao encontrado.", file=sys.stderr)
    raise SystemExit(1)


def gerar_figuras() -> None:
    script = AQUI / "figuras" / "gerar_figuras.py"
    if script.exists():
        subprocess.run([sys.executable, str(script)], check=True)


def renderizar_pdf_bruto(navegador: str, destino: Path) -> None:
    url = HTML.resolve().as_uri()
    comando = [
        navegador,
        "--headless",
        "--disable-gpu",
        "--no-margins",
        f"--print-to-pdf={destino}",
        url,
    ]
    resultado = subprocess.run(comando, capture_output=True, text=True)
    if not destino.exists():
        print(resultado.stderr, file=sys.stderr)
        raise SystemExit("Falha ao gerar o PDF bruto.")


def limpar_e_numerar(bruto: Path, final: Path) -> int:
    doc = fitz.open(bruto)
    branco = (1, 1, 1)
    cinza = (0.42, 0.42, 0.42)
    n = doc.page_count
    for pagina in doc:
        larg = pagina.rect.width
        alt = pagina.rect.height
        # REMOVE de fato o cabecalho/rodape que o navegador imprime na margem
        # (data, URL e numero de pagina proprios). Redaction apaga o texto
        # subjacente, evitando que ele "vaze" sob a faixa branca em alguns
        # leitores. As faixas ficam na margem (topo 18 mm, base 20 mm), fora do
        # corpo do texto, que comeca a ~51 pt do topo e termina a ~57 pt da base.
        pagina.add_redact_annot(fitz.Rect(0, 0, larg, 44), fill=branco)
        pagina.add_redact_annot(fitz.Rect(0, alt - 44, larg, alt), fill=branco)
        pagina.apply_redactions()
    for i, pagina in enumerate(doc):
        # Rodape proprio (a capa fica limpa).
        if i == 0:
            continue
        larg = pagina.rect.width
        alt = pagina.rect.height
        y = alt - 30
        pagina.draw_line((40, y), (larg - 40, y), color=cinza, width=0.6)
        pagina.insert_text((40, y + 12), RODAPE, fontname="helv", fontsize=7.5, color=cinza)
        pagina.insert_textbox(
            fitz.Rect(larg - 200, y + 2, larg - 40, y + 16),
            f"Página {i + 1} de {n}",
            fontname="helv", fontsize=7.5, color=cinza, align=fitz.TEXT_ALIGN_RIGHT,
        )
    doc.save(final, deflate=True, garbage=4)
    doc.close()
    return n


def main() -> int:
    if not HTML.exists():
        print(f"Nao encontrei {HTML}", file=sys.stderr)
        return 1
    gerar_figuras()
    navegador = achar_navegador()
    print(f"Navegador: {navegador}")
    with tempfile.TemporaryDirectory(prefix="relatorio-") as tmp:
        bruto = Path(tmp) / "bruto.pdf"
        renderizar_pdf_bruto(navegador, bruto)
        paginas = limpar_e_numerar(bruto, SAIDA)
    print(f"PDF gerado: {SAIDA} ({paginas} páginas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
