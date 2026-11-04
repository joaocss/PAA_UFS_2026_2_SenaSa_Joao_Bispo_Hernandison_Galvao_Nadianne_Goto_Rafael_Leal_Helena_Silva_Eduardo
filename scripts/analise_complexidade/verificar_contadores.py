"""Parte C — Verificação das iterações reais da mochila 0/1.

Executa a implementação da Parte B sem alterá-la. Conta, com sys.settrace,
quantas vezes a atribuição central do laço interno da DP é executada.
Não mede tempo nem memória; a instrumentação tem custo adicional.
"""

import inspect
import sys
from pathlib import Path

# Permite executar a partir da raiz do repositório.
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from paa_context.selecao import Item, mochila_dp


def gerar_itens(n):
    """Cria n candidatos sintéticos determinísticos e válidos."""
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


def localizar_linha_atualizacao():
    """Localiza a atribuição executada uma vez por estado na DP real."""
    linhas, primeira_linha = inspect.getsourcelines(mochila_dp)
    marcador = "linha_atual[w] = linha_seguinte[w]"
    encontradas = [
        primeira_linha + indice
        for indice, linha in enumerate(linhas)
        if linha.strip().startswith(marcador)
    ]
    if len(encontradas) != 1:
        raise RuntimeError(
            "Não foi possível localizar unicamente a atualização de estado "
            "em mochila_dp(); reveja a instrumentação."
        )
    return encontradas[0]


def executar_com_contagem(itens, orcamento, linha_alvo):
    """Conta eventos reais da atribuição no frame da função mochila_dp."""
    contagem = 0

    def rastrear(frame, evento, argumento):
        nonlocal contagem
        if evento == "call":
            if frame.f_code is mochila_dp.__code__:
                return rastrear
            return None
        if evento == "line" and frame.f_lineno == linha_alvo:
            contagem += 1
        return rastrear

    rastreador_anterior = sys.gettrace()
    try:
        sys.settrace(rastrear)
        resultado = mochila_dp(itens, orcamento)
    finally:
        sys.settrace(rastreador_anterior)
    return resultado, contagem


def executar():
    candidatos = [10, 30, 50]
    orcamentos = [256, 512, 1024]
    linha_alvo = localizar_linha_atualizacao()

    print("PARTE C — CONTAGEM REAL DE ITERAÇÕES DA MATRIZ DP")
    print("-" * 79)
    print(
        f"{'n':>4} {'W':>6} {'Estados previstos':>18} "
        f"{'Iterações reais':>18} {'Células alocadas':>18} {'Status':>8}"
    )

    for n in candidatos:
        itens = gerar_itens(n)
        for W in orcamentos:
            resultado, iteracoes_reais = executar_com_contagem(itens, W, linha_alvo)
            estados_previstos = n * (W + 1)
            celulas_previstas = (n + 1) * (W + 1)

            assert iteracoes_reais == estados_previstos, (
                f"n={n}, W={W}: contadas {iteracoes_reais} iterações, "
                f"esperadas {estados_previstos}"
            )
            assert resultado.celulas == celulas_previstas
            assert resultado.custo_total <= W

            print(
                f"{n:>4} {W:>6} {estados_previstos:>18} "
                f"{iteracoes_reais:>18} {resultado.celulas:>18} {'OK':>8}"
            )

    print("-" * 79)
    print("9/9 configurações: contagens reais compatíveis com n(W + 1).")
    print("Observação: sys.settrace instrumenta a execução; não mede desempenho.")


if __name__ == "__main__":
    executar()
