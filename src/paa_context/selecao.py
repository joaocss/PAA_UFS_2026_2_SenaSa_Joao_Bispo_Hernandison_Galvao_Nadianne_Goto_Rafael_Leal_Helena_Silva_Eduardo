"""Selecao de contexto com orcamento de palavras (AV2, Trilha A).

Dos chunks que a busca da AV1 devolve, escolhe os que cabem em W palavras.
Contratos 10 a 15 de docs/CONTRATOS_AV2.md. Estrategias:
    S1 prefixo_ranking, S2 guloso_valor, S3 guloso_densidade (linha de base,
    contrato 06), S4 guloso_modificado e S5 mochila_dp (contrato 05).

n e o numero de candidatos; N, o numero de chunks do corpus.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction

ESCALA_VALOR = 1000


@dataclass(frozen=True)
class Item:
    """Chunk candidato a entrar no contexto.

    chunk_id: identificador do chunk, vindo da AV1.
    custo: palavras que o chunk ocupa. Inteiro >= 1.
    valor: escore inteiro (escore * ESCALA_VALOR). Inteiro >= 1.
    posicao: lugar no ranking da AV1 (0 e o primeiro). Inteiro >= 0 e
             distinto entre os itens; ordena S1, desempata S2 e o item
             isolado de S4 e define a ordem da saida.
    source_order: lugar do chunk no livro. Inteiro >= 0 e distinto entre
             os itens; desempata S3 e S5, como pede a Parte A.
    escore: escore tf-idf original da consulta. Numero finito > 0.
    """

    chunk_id: str
    custo: int
    valor: int
    posicao: int
    source_order: int
    escore: float


@dataclass
class Selecao:
    """Resultado de uma estrategia."""

    estrategia: str
    escolhidos: list[Item]
    celulas: int = 0  # preenchido apenas pela DP: celulas calculadas na tabela
    extras: dict = field(default_factory=dict)

    @property
    def custo_total(self):
        return sum(item.custo for item in self.escolhidos)

    @property
    def valor_total(self):
        return sum(item.valor for item in self.escolhidos)

    @property
    def relevancia_total(self):
        # V_S da Parte A: soma dos escores originais, sem arredondamento
        return sum(item.escore for item in self.escolhidos)

    @property
    def ids(self):
        return [item.chunk_id for item in self.escolhidos]


def _inteiro(numero):
    # em Python, bool e subclasse de int; True nao pode passar como 1
    return isinstance(numero, int) and not isinstance(numero, bool)


def _real_finito(numero):
    return (isinstance(numero, (int, float)) and not isinstance(numero, bool)
            and math.isfinite(numero))


def itens_de_resultados(resultados):
    """Converte [(Chunk, escore), ...] do retrieve em lista de Item (contrato 10).

    Escore zero sai da lista. chunk_id repetido, n_tokens < 1, escore
    invalido ou escore que arredonda para 0 geram ValueError.
    """
    itens = []
    ids_vistos = set()
    for posicao, (chunk, escore) in enumerate(resultados):
        if chunk.chunk_id in ids_vistos:
            raise ValueError(f"chunk_id {chunk.chunk_id!r} repetido nos resultados")
        ids_vistos.add(chunk.chunk_id)
        if not _inteiro(chunk.n_tokens) or chunk.n_tokens < 1:
            raise ValueError(f"{chunk.chunk_id}: n_tokens {chunk.n_tokens!r} precisa ser inteiro >= 1")
        if not _real_finito(escore) or escore < 0:
            raise ValueError(f"{chunk.chunk_id}: escore {escore!r} precisa ser finito e >= 0")
        if escore == 0:
            continue  # relevancia zero nao acrescenta valor (contrato 07)
        valor = round(escore * ESCALA_VALOR)
        if valor < 1:
            raise ValueError(f"{chunk.chunk_id}: escore {escore!r} arredonda para valor 0 "
                             f"com ESCALA_VALOR = {ESCALA_VALOR}")
        itens.append(Item(
            chunk_id=chunk.chunk_id,
            custo=chunk.n_tokens,
            valor=valor,
            posicao=posicao,
            source_order=chunk.source_order,
            escore=escore,
        ))
    return itens


def _validar(itens, W):
    """Regra 2 do contrato 11: entrada fora da especificacao gera ValueError."""
    if not _inteiro(W):
        raise ValueError(f"orcamento precisa ser inteiro: {W!r}")
    if W < 0:
        raise ValueError(f"orcamento negativo: {W}")
    posicoes_vistas, ordens_vistas, ids_vistos = set(), set(), set()
    for item in itens:
        if not _inteiro(item.custo) or item.custo < 1:
            raise ValueError(f"{item.chunk_id}: custo {item.custo!r} precisa ser inteiro >= 1")
        if not _inteiro(item.valor) or item.valor < 1:
            raise ValueError(f"{item.chunk_id}: valor {item.valor!r} precisa ser inteiro >= 1")
        if not _real_finito(item.escore) or item.escore <= 0:
            raise ValueError(f"{item.chunk_id}: escore {item.escore!r} precisa ser finito e > 0")
        if not _inteiro(item.posicao) or item.posicao < 0:
            raise ValueError(f"{item.chunk_id}: posicao {item.posicao!r} precisa ser inteiro >= 0")
        if not _inteiro(item.source_order) or item.source_order < 0:
            raise ValueError(f"{item.chunk_id}: source_order {item.source_order!r} precisa ser inteiro >= 0")
        if item.posicao in posicoes_vistas:
            raise ValueError(f"{item.chunk_id}: posicao {item.posicao} repetida")
        if item.source_order in ordens_vistas:
            raise ValueError(f"{item.chunk_id}: source_order {item.source_order} repetido")
        if item.chunk_id in ids_vistos:
            raise ValueError(f"chunk_id {item.chunk_id!r} repetido")
        posicoes_vistas.add(item.posicao)
        ordens_vistas.add(item.source_order)
        ids_vistos.add(item.chunk_id)


def _em_ordem_de_ranking(escolhidos):
    # o contexto segue a ordem do ranking da AV1, e nao a ordem em que a
    # estrategia encontrou os chunks
    return sorted(escolhidos, key=lambda item: item.posicao)


def prefixo_ranking(itens, W):
    """S1: desce o ranking e para no primeiro chunk que nao cabe (como a AV1)."""
    _validar(itens, W)
    escolhidos = []
    palavras_usadas = 0
    for item in sorted(itens, key=lambda item: item.posicao):
        if palavras_usadas + item.custo > W:
            break
        escolhidos.append(item)
        palavras_usadas += item.custo
    return Selecao("prefixo_ranking", escolhidos)


def _guloso(itens, W, chave, nome):
    _validar(itens, W)
    escolhidos = []
    palavras_usadas = 0
    for item in sorted(itens, key=chave):
        if palavras_usadas + item.custo <= W:  # o que nao cabe fica de fora
            escolhidos.append(item)
            palavras_usadas += item.custo
    return Selecao(nome, _em_ordem_de_ranking(escolhidos))


def guloso_valor(itens, W):
    """S2: maior valor primeiro, pulando os que nao cabem; empate pela posicao."""
    return _guloso(itens, W, lambda item: (-item.valor, item.posicao), "guloso_valor")


def guloso_densidade(itens, W):
    """S3 (contrato 06): maior valor por palavra primeiro, pulando os que nao cabem.

    Empate: maior valor, depois menor source_order. A razao e comparada como
    Fraction sobre o valor ja arredondado. O(n log n), sem garantia de otimo.
    """
    return _guloso(
        itens, W,
        lambda item: (-Fraction(item.valor, item.custo), -item.valor, item.source_order),
        "guloso_densidade",
    )


def guloso_modificado(itens, W):
    """S4: o melhor entre S3 e o item de maior valor que cabe sozinho.

    No empate, fica S3. Garante pelo menos metade do otimo. O(n log n).
    """
    _validar(itens, W)
    selecao_gulosa = guloso_densidade(itens, W)
    cabem_sozinhos = [item for item in itens if item.custo <= W]
    if not cabem_sozinhos:
        return Selecao("guloso_modificado", [])
    maior_isolado = min(cabem_sozinhos, key=lambda item: (-item.valor, item.posicao))
    if maior_isolado.valor > selecao_gulosa.valor_total:
        return Selecao("guloso_modificado", [maior_isolado])
    return Selecao("guloso_modificado", selecao_gulosa.escolhidos)


def mochila_dp(itens, W):
    """S5 (contrato 05): mochila 0/1 bottom-up, com os desempates da Parte A.

    Itens em ordem de source_order. Cada celula guarda a chave
    valor * (W + 1) - custo, que ordena por maior valor e, no empate, menor
    custo, pois o custo de uma selecao viavel fica entre 0 e W.

        E[n][w] = 0
        E[i][w] = E[i+1][w]                                    se custo_i > w
        E[i][w] = max(E[i+1][w], chave_i + E[i+1][w - custo_i])  caso contrario

    A reconstrucao vai do menor source_order ao maior e leva o item quando
    ele ainda permite alcancar E[0][W]; assim, entre as empatadas, fica a de
    menor sequencia de source_order. Tempo e memoria Theta(n * W), mais a
    ordenacao; pseudo-polinomial em W. Otimo para o valor arredondado.
    """
    _validar(itens, W)
    ordenados = sorted(itens, key=lambda item: item.source_order)
    n = len(ordenados)
    peso = W + 1  # maior que o custo de qualquer selecao viavel
    E = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        custo = ordenados[i].custo
        chave = ordenados[i].valor * peso - custo
        linha_seguinte, linha_atual = E[i + 1], E[i]
        for w in range(W + 1):
            linha_atual[w] = linha_seguinte[w]  # sem o item i
            if custo <= w and chave + linha_seguinte[w - custo] > linha_atual[w]:
                linha_atual[w] = chave + linha_seguinte[w - custo]  # com o item i
    escolhidos = []
    w = W
    for i in range(n):
        custo = ordenados[i].custo
        chave = ordenados[i].valor * peso - custo
        if custo <= w and E[i][w] == chave + E[i + 1][w - custo]:
            escolhidos.append(ordenados[i])  # leva-lo ainda alcanca a chave otima
            w -= custo
    return Selecao(
        "mochila_dp",
        _em_ordem_de_ranking(escolhidos),
        celulas=(n + 1) * (W + 1),
        extras={"valor_otimo": (E[0][W] + W) // peso},
    )


def forca_bruta(itens, W):
    """Testa os 2^n subconjuntos; so serve de juiz nos testes (n <= 20)."""
    _validar(itens, W)
    n = len(itens)
    if n > 20:
        raise ValueError("forca bruta aceita no maximo 20 itens")
    melhor_valor, melhor_subconjunto = 0, []
    for mascara in range(1 << n):
        subconjunto = [itens[j] for j in range(n) if mascara >> j & 1]
        custo = sum(item.custo for item in subconjunto)
        valor = sum(item.valor for item in subconjunto)
        if custo <= W and valor > melhor_valor:
            melhor_valor, melhor_subconjunto = valor, subconjunto
    return Selecao("forca_bruta", _em_ordem_de_ranking(melhor_subconjunto))


ESTRATEGIAS = {
    "prefixo_ranking": prefixo_ranking,
    "guloso_valor": guloso_valor,
    "guloso_densidade": guloso_densidade,
    "guloso_modificado": guloso_modificado,
    "mochila_dp": mochila_dp,
}
