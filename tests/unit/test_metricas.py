import math

from paa_context.metricas import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank

RELEVANCIA = {"a": 2, "b": 0, "c": 1, "d": 1}


def test_precision_conta_so_grau_positivo():
    assert precision_at_k(["a", "b", "c"], RELEVANCIA, 3) == 2 / 3


def test_precision_divide_por_k_mesmo_com_menos_resultados():
    assert precision_at_k(["a"], RELEVANCIA, 5) == 1 / 5


def test_precision_k_zero():
    assert precision_at_k(["a"], RELEVANCIA, 0) == 0.0


def test_recall_sobre_os_relevantes_julgados():
    assert recall_at_k(["a", "x"], RELEVANCIA, 2) == 1 / 3


def test_recall_sem_relevante_e_none():
    assert recall_at_k(["a"], {"a": 0}, 5) is None


def test_ndcg_ordem_ideal_vale_um():
    assert ndcg_at_k(["a", "c", "d"], RELEVANCIA, 3) == 1.0


def test_ndcg_ordem_invertida_menor_que_um():
    esperado = (1 / 1 + 1 / math.log2(3) + 2 / 2) / (2 / 1 + 1 / math.log2(3) + 1 / 2)
    assert math.isclose(ndcg_at_k(["d", "c", "a"], RELEVANCIA, 3), esperado)


def test_reciprocal_rank_primeiro_relevante_na_terceira():
    assert reciprocal_rank(["x", "b", "c"], RELEVANCIA) == 1 / 3


def test_reciprocal_rank_nenhum_relevante():
    assert reciprocal_rank(["x", "b"], RELEVANCIA) == 0.0
