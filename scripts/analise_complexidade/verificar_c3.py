"""Parte C — Verificação estrutural do Merge Sort C3 da AV1.

Executa o algoritmo original com entradas sintéticas determinísticas, verifica
ordenacao e desempate pelo critério original e exporta as comparações para CSV.
Não mede tempo de execução.
"""

import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from paa_context.merge_sort import merge_sort
from paa_context.contador import Contador
from paa_context.modelos import Chunk
from paa_context.sort_key import sort_key


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
        score = float((i * 37) % (p + 1) + 1)
        resultados.append((chunk, score))
    return resultados


def executar():
    tamanhos = (10, 30, 50, 100, 200)
    registros = []

    print("PARTE C — VERIFICAÇÃO DO MERGE SORT")
    print("-" * 76)

    for p in tamanhos:
        resultados = gerar_resultados(p)
        contador = Contador()
        ordenados = merge_sort(resultados, contador=contador)

        # Verifica a ordem TOTAL da C3, incluindo desempate por source_order.
        esperado = sorted(resultados, key=sort_key)
        assert len(ordenados) == p, f"Tamanho incorreto para P={p}"
        assert ordenados == esperado, (
            f"Ordenação ou desempate por source_order incorreto para P={p}"
        )
        assert contador.comparacoes >= 0

        registros.append({"P": p, "comparacoes": contador.comparacoes})
        print(
            f"P={p:>3} | Comparações={contador.comparacoes:>5} "
            "| Ordem e desempate=OK"
        )

    destino = Path(__file__).resolve().parent / "resultados"
    destino.mkdir(parents=True, exist_ok=True)
    arquivo = destino / "comparacoes_merge_sort.csv"

    # Só grava se todas as verificações tiverem passado.
    with arquivo.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=("P", "comparacoes"))
        escritor.writeheader()
        escritor.writerows(registros)

    print("-" * 76)
    print(f"{len(tamanhos)}/{len(tamanhos)} configurações verificadas.")
    print(f"CSV gerado: {arquivo}")


if __name__ == "__main__":
    executar()
