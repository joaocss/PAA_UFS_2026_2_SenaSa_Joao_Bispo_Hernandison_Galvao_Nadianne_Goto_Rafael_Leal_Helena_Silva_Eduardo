"""Gera as figuras teoricas usadas no relatorio da AV1.

Estas figuras sao curvas de crescimento e diagramas didaticos, derivados das
funcoes de complexidade, e NAO medicoes experimentais. Os graficos empiricos
(tempo, memoria, Precision@k) serao produzidos por scripts/gerar_figuras.py a
partir dos dados de experimentos/ depois que o pipeline for executado.

Uso:
    python relatorio/figuras/gerar_figuras.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

AQUI = Path(__file__).resolve().parent

AZUL = "#1f4e79"
LARANJA = "#c55a11"
VERDE = "#2e7d32"
CINZA = "#666666"


def crescimento_teorico() -> None:
    """Contagem de operacoes elementares em funcao de N (escala log em y)."""
    ns = list(range(2, 2001))
    n2 = [n * n for n in ns]
    nlogn = [n * math.log2(n) for n in ns]
    linear = [n for n in ns]
    logn = [math.log2(n) for n in ns]

    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    ax.plot(ns, n2, color=LARANJA, lw=2.2, label=r"Insertion Sort (pior/medio): $\Theta(N^2)$")
    ax.plot(ns, nlogn, color=AZUL, lw=2.2, label=r"Merge Sort (todos os casos): $\Theta(N\log N)$")
    ax.plot(ns, linear, color=VERDE, lw=2.0, ls="--", label=r"Busca linear: $\Theta(N)$")
    ax.plot(ns, logn, color=CINZA, lw=2.0, ls=":", label=r"Busca binaria: $\Theta(\log N)$")

    ax.set_yscale("log")
    ax.set_xlabel("N (numero de chunks)")
    ax.set_ylabel("Operacoes elementares (escala log)")
    ax.set_title("Crescimento teorico do custo por estrategia")
    ax.grid(True, which="both", ls=":", alpha=0.4)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.95)
    ax.axvline(330, color="#999999", lw=1.0, alpha=0.7)
    ax.annotate("N ≈ 330\n(config. principal)", xy=(330, 5), xytext=(430, 3),
                fontsize=7.5, color="#444444")

    fig.tight_layout()
    fig.savefig(AQUI / "crescimento_teorico.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def arvore_recorrencia() -> None:
    """Arvore de recorrencia do Merge Sort: T(N)=2T(N/2)+Theta(N)."""
    fig, ax = plt.subplots(figsize=(6.6, 4.1))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10.6)
    ax.axis("off")

    niveis = [
        (9.0, 1, "N"),
        (7.0, 2, "N/2"),
        (5.0, 4, "N/4"),
        (3.0, 8, "N/8"),
    ]
    largura_total = 8.0
    x0 = 1.0
    for y, blocos, rotulo in niveis:
        larg = largura_total / blocos
        for i in range(blocos):
            cx = x0 + i * larg
            caixa = FancyBboxPatch((cx + 0.06, y), larg - 0.12, 0.9,
                                   boxstyle="round,pad=0.02,rounding_size=0.08",
                                   linewidth=1.1, edgecolor=AZUL, facecolor="#dce6f1")
            ax.add_patch(caixa)
            if blocos <= 4:
                ax.text(cx + larg / 2, y + 0.45, rotulo, ha="center", va="center", fontsize=8.5)

    ax.text(9.9, 10.15, "trabalho no nivel", ha="right", fontsize=8, style="italic", color="#333")
    trabalhos = [(9.0, "cN"), (7.0, "cN"), (5.0, "cN"), (3.0, "cN")]
    for y, t in trabalhos:
        ax.text(9.7, y + 0.45, t, ha="right", va="center", fontsize=9, color=LARANJA, weight="bold")

    ax.annotate("", xy=(0.55, 3.0), xytext=(0.55, 9.4),
                arrowprops=dict(arrowstyle="<->", color=CINZA, lw=1.2))
    ax.text(0.32, 6.2, r"log$_2$N + 1 niveis", rotation=90, ha="center", va="center",
            fontsize=8.5, color=CINZA)

    ax.text(5.0, 1.7, "...  (folhas: subproblemas de tamanho 1)", ha="center", fontsize=8, color="#555")
    ax.text(5.0, 0.7, r"Custo total = (trabalho por nivel) × (nº de niveis) = $cN\cdot(\log_2 N + 1) = \Theta(N\log N)$",
            ha="center", fontsize=9.5, color=AZUL, weight="bold")
    ax.set_title("Arvore de recorrencia do Merge Sort:  T(N) = 2·T(N/2) + Θ(N)", fontsize=10)

    fig.tight_layout()
    fig.savefig(AQUI / "arvore_recorrencia.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    crescimento_teorico()
    arvore_recorrencia()
    print("Figuras geradas em", AQUI)


if __name__ == "__main__":
    main()
