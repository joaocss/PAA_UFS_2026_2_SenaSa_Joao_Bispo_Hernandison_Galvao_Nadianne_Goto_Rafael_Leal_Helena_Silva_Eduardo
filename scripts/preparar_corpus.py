"""Corta o corpus em chunks e grava data/processed/chunks.jsonl.

Le os notebooks de data/raw/capitulos na ordem do livro (introducao ao
Jupyter, prefacio, capitulos 1 a 19), extrai as celulas, fragmenta e grava
um objeto JSON por linha no formato do contrato 01. Ao final registra o
SHA-256 do arquivo gerado no manifesto do corpus.

Uso:
    python scripts/preparar_corpus.py                  # todos os 21 notebooks
    python scripts/preparar_corpus.py --notebooks 8    # os 8 primeiros (checkpoint)
    python scripts/preparar_corpus.py --tamanho 128 --sobreposicao 16
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from paa_context.fragmentacao import extrair_celulas, fragmentar  # noqa: E402
from paa_context.modelos import salvar_chunks  # noqa: E402

PASTA_BRUTA = RAIZ / "data" / "raw"
SAIDA_PADRAO = RAIZ / "data" / "processed" / "chunks.jsonl"
MANIFESTO = RAIZ / "data" / "corpus_manifest.csv"

ORDEM = ["jupyter_intro", "chap00"] + [f"chap{i:02d}" for i in range(1, 20)]


def notebooks_na_ordem(quantos: int | None) -> list[Path]:
    caminhos = []
    for nome in ORDEM:
        arquivo = PASTA_BRUTA / "capitulos" / f"{nome}.ipynb"
        if not arquivo.exists():
            print(f"nao encontrei {arquivo}. Rode antes: python scripts/baixar_corpus.py", file=sys.stderr)
            raise SystemExit(1)
        caminhos.append(arquivo)
    return caminhos[:quantos] if quantos else caminhos


def registrar_no_manifesto(saida: Path, tamanho: int, sobreposicao: int) -> None:
    """Acrescenta (ou substitui) a linha da extracao no manifesto."""
    if not MANIFESTO.exists():
        return
    with MANIFESTO.open(encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        colunas = leitor.fieldnames or []
        linhas = [l for l in leitor if l["tipo"] != "extracao"]
    linhas.append({
        "tipo": "extracao",
        "caminho": str(saida.relative_to(RAIZ)),
        "bytes": saida.stat().st_size,
        "sha256": hashlib.sha256(saida.read_bytes()).hexdigest(),
        "commit": f"tamanho={tamanho};sobreposicao={sobreposicao}",
        "url": "",
        "acessado_em": date.today().isoformat(),
    })
    with MANIFESTO.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)


def principal() -> int:
    opcoes = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    opcoes.add_argument("--notebooks", type=int, default=None, help="usa so os N primeiros notebooks")
    opcoes.add_argument("--tamanho", type=int, default=256, help="tokens por chunk")
    opcoes.add_argument("--sobreposicao", type=int, default=32, help="tokens repetidos entre chunks vizinhos")
    opcoes.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = opcoes.parse_args()

    celulas = []
    for caminho in notebooks_na_ordem(args.notebooks):
        celulas.extend(extrair_celulas(caminho, raiz=PASTA_BRUTA))

    chunks = fragmentar(celulas, tamanho=args.tamanho, sobreposicao=args.sobreposicao)
    salvar_chunks(chunks, args.saida)

    por_tipo = Counter(c.tipo for c in chunks)
    por_arquivo = Counter(c.arquivo for c in chunks)
    print(f"{len(celulas)} celulas de {len(por_arquivo)} notebooks")
    print(f"{len(chunks)} chunks ({por_tipo['markdown']} de texto, {por_tipo['codigo']} de codigo), "
          f"tamanho {args.tamanho}, sobreposicao {args.sobreposicao}")
    for arquivo, n in sorted(por_arquivo.items(), key=lambda par: ORDEM.index(Path(par[0]).stem)):
        print(f"  {arquivo:32} {n:4d}")
    print(f"gravado em {args.saida}")

    if args.saida == SAIDA_PADRAO and args.notebooks is None:
        registrar_no_manifesto(args.saida, args.tamanho, args.sobreposicao)
        print("hash da extracao registrado no manifesto")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
