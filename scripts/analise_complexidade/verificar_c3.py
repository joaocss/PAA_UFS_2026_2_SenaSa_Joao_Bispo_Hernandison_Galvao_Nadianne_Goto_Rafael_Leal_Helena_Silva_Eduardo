
"""
Parte C — Verificação estrutural do Merge Sort da C3.

Utiliza a implementação real da AV1.
Não realiza benchmark de tempo.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from paa_context.merge_sort import merge_sort
from paa_context.contador import Contador
from paa_context.modelos import Chunk


def gerar_resultados(p):
    resultados = []

    for i in range(p):
        chunk = Chunk(
            chunk_id=f"teste_{i}",
            source_order=i,
            texto="chunk sintético",
            tipo="markdown",
            arquivo="teste.ipynb",
            capitulo="Teste",
            secao="",
            celula_idx=i,
            token_inicio=0,
            token_fim=2,
            n_tokens=2,
        )

        # Valores determinísticos em ordem não ordenada.
        score = float((i * 37) % (p + 1) + 1)
        resultados.append((chunk, score))

    return resultados


def executar():
    print("PARTE C — VERIFICAÇÃO DO MERGE SORT")
    print("-" * 65)

    for p in [10, 30, 50, 100, 200]:
        resultados = gerar_resultados(p)
        contador = Contador()

        ordenados = merge_sort(resultados, contador=contador)

        assert len(ordenados) == p
        assert all(
            ordenados[i][1] >= ordenados[i + 1][1]
            for i in range(p - 1)
        )

        print(
            f"P={p:>3} | "
            f"Comparações={contador.comparacoes:>5} | "
            f"Ordenação=OK"
        )


if __name__ == "__main__":
    executar()

