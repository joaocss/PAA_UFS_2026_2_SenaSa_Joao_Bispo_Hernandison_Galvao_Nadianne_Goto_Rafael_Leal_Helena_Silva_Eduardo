
"""
Parte C — Verificação dos contadores da programação dinâmica.

Utiliza a implementação da Parte B sem modificá-la.
Os candidatos são sintéticos e determinísticos.
"""

import sys
from pathlib import Path

# Permite executar diretamente a partir da raiz do projeto.
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from paa_context.selecao import Item, mochila_dp


def gerar_itens(n):
    """Cria n candidatos sintéticos com custos e valores positivos."""
    return [
        Item(
            chunk_id=f"chunk_{i:03d}",
            custo=10 + (i % 20),
            valor=1000 + i * 100,
            posicao=i,
            source_order=i,
            escore=1.0 + i / 10,
        )
        for i in range(n)
    ]


def executar():
    candidatos = [10, 30, 50]
    orcamentos = [256, 512, 1024]

    print("PARTE C — VERIFICAÇÃO DA MATRIZ DP")
    print("-" * 77)
    print(
        f"{'n':>4} {'W':>6} "
        f"{'Estados':>12} {'Previstas':>12} "
        f"{'Registradas':>13} {'Status':>10}"
    )

    for n in candidatos:
        itens = gerar_itens(n)

        for W in orcamentos:
            resultado = mochila_dp(itens, W)

            estados = n * (W + 1)
            previstas = (n + 1) * (W + 1)
            registradas = resultado.celulas

            assert registradas == previstas
            assert resultado.custo_total <= W

            print(
                f"{n:>4} {W:>6} "
                f"{estados:>12} {previstas:>12} "
                f"{registradas:>13} {'OK':>10}"
            )

    print("-" * 77)
    print("Todas as configurações foram verificadas.")


if __name__ == "__main__":
    executar()
