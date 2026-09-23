"""Reproduz o trabalho de ponta a ponta, na ordem, parando no primeiro erro.

Uso:
    python scripts/reproduzir_tudo.py
    python scripts/reproduzir_tudo.py --rapido    # experimento reduzido, so para conferir o fluxo

Etapas: baixar o corpus, preparar os chunks, rodar a suite de testes, rodar
os experimentos, gerar tabelas e figuras e medir a ingestao com a
sensibilidade ao tamanho do chunk. O julgamento de relevancia
(data/qrels.csv) e humano e nao e refeito aqui; se o arquivo existir, as
metricas de qualidade entram nas tabelas.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def principal() -> int:
    opcoes = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    opcoes.add_argument("--rapido", action="store_true")
    args = opcoes.parse_args()

    python = sys.executable
    etapas = [
        [python, "scripts/baixar_corpus.py"],
        [python, "scripts/preparar_corpus.py"],
        [python, "-m", "pytest"],
        [python, "scripts/rodar_experimentos.py"] + (["--rapido"] if args.rapido else []),
        [python, "scripts/gerar_figuras.py"],
        [python, "scripts/medir_ingestao.py"] + (["--rapido"] if args.rapido else []),
    ]
    for etapa in etapas:
        print(f"\n>>> {' '.join(etapa[1:])}", flush=True)
        if subprocess.run(etapa, cwd=RAIZ).returncode != 0:
            print(f"parou em: {' '.join(etapa[1:])}", file=sys.stderr)
            return 1
    print("\nfeito: dados brutos em experimentos/brutos, tabelas em experimentos/processados, figuras em experimentos/figuras")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
