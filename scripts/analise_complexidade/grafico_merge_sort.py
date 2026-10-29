"""Parte C — Gráfico das comparações observadas do Merge Sort C3.

Lê o CSV produzido por verificar_c3.py; nunca usa valores digitados à mão.
Para atualizar o gráfico, execute primeiro verificar_c3.py.
"""

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt

RESULTADOS = Path(__file__).resolve().parent / "resultados"
ENTRADA = RESULTADOS / "comparacoes_merge_sort.csv"
SAIDA = RESULTADOS / "comparacoes_merge_sort.png"


def executar():
    if not ENTRADA.is_file():
        raise SystemExit(
            f"CSV não encontrado: {ENTRADA}\n"
            "Execute primeiro: python scripts/analise_complexidade/verificar_c3.py"
        )

    with ENTRADA.open(newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        if not {"P", "comparacoes"}.issubset(leitor.fieldnames or []):
            raise ValueError("O CSV precisa das colunas P e comparacoes.")
        registros = [(int(linha["P"]), int(linha["comparacoes"])) for linha in leitor]

    if not registros:
        raise ValueError("O CSV não contém medições.")
    if any(p < 1 or comparacoes < 0 for p, comparacoes in registros):
        raise ValueError("O CSV contém valores inválidos.")

    registros.sort(key=lambda par: par[0])
    p = [par[0] for par in registros]
    comparacoes = [par[1] for par in registros]
    if len(set(p)) != len(p):
        raise ValueError("O CSV contém valores de P duplicados.")

    referencia = [x * math.log2(x) for x in p]
    figura, eixo = plt.subplots(figsize=(8, 5))
    eixo.plot(p, comparacoes, marker="o", label="Comparações observadas")
    eixo.plot(
        p, referencia, marker="s", linestyle="--",
        label=r"Referência $P\log_2 P$",
    )
    eixo.set_xlabel("Quantidade de candidatos (P)")
    eixo.set_ylabel("Número de comparações")
    eixo.set_title("Crescimento das comparações do Merge Sort — C3")
    eixo.legend()
    eixo.grid(True, alpha=0.3)
    figura.tight_layout()
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    figura.savefig(SAIDA, dpi=200)
    plt.close(figura)
    print(f"Gráfico gerado com {len(registros)} linhas do CSV: {SAIDA}")


if __name__ == "__main__":
    executar()
