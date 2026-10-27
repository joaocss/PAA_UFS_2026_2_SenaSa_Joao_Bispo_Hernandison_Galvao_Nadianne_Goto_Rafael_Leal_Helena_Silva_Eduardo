
"""Parte C — Crescimento teórico da programação dinâmica."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt

PASTA = Path(__file__).resolve().parent
SAIDA = PASTA / "resultados"
SAIDA.mkdir(exist_ok=True)

N_VALORES = [10, 20, 30, 40, 50]
W_VALORES = [256, 512, 1024]


def estados_dp(n, W):
    return n * (W + 1)


def celulas_dp(n, W):
    return (n + 1) * (W + 1)


def gerar_csv():
    caminho = SAIDA / "crescimento_dp.csv"

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["n", "W", "estados_dp", "celulas_dp"])

        for n in N_VALORES:
            for W in W_VALORES:
                escritor.writerow([
                    n, W, estados_dp(n, W), celulas_dp(n, W)
                ])

    print(f"CSV gerado: {caminho}")


def grafico_variacao_n():
    plt.figure(figsize=(8, 5))

    for W in W_VALORES:
        valores = [estados_dp(n, W) for n in N_VALORES]
        plt.plot(N_VALORES, valores, marker="o", label=f"W={W}")

    plt.xlabel("Número de candidatos (n)")
    plt.ylabel("Estados processados (teóricos)")
    plt.title("Crescimento da DP em função de n")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    caminho = SAIDA / "crescimento_por_n.png"
    plt.savefig(caminho, dpi=200)
    plt.close()
    print(f"Gráfico gerado: {caminho}")


def grafico_variacao_w():
    plt.figure(figsize=(8, 5))

    for n in [10, 30, 50]:
        valores = [estados_dp(n, W) for W in W_VALORES]
        plt.plot(W_VALORES, valores, marker="o", label=f"n={n}")

    plt.xlabel("Orçamento (W) em unidades lexicais")
    plt.ylabel("Estados processados (teóricos)")
    plt.title("Crescimento da DP em função de W")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    caminho = SAIDA / "crescimento_por_w.png"
    plt.savefig(caminho, dpi=200)
    plt.close()
    print(f"Gráfico gerado: {caminho}")


if __name__ == "__main__":
    gerar_csv()
    grafico_variacao_n()
    grafico_variacao_w()
    print("Análise teórica concluída.")
