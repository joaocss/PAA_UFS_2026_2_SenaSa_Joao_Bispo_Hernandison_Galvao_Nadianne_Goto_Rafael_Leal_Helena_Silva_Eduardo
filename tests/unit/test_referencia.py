import pytest

pytest.importorskip("sklearn")

from paa_context.linear_search import CHUNKS_PYTHON  # noqa: E402
from paa_context.referencia import construir_referencia, recuperar_referencia  # noqa: E402


def test_devolve_no_maximo_k_com_escore_positivo():
    referencia = construir_referencia(CHUNKS_PYTHON)
    resultados, candidatos = recuperar_referencia("lista python", referencia, 2)
    assert len(resultados) <= 2
    assert candidatos >= len(resultados)
    assert all(escore > 0 for _, escore in resultados)


def test_escores_decrescentes():
    referencia = construir_referencia(CHUNKS_PYTHON)
    resultados, _ = recuperar_referencia("lista python", referencia, 10)
    escores = [escore for _, escore in resultados]
    assert escores == sorted(escores, reverse=True)


def test_termo_inexistente_devolve_vazio():
    referencia = construir_referencia(CHUNKS_PYTHON)
    assert recuperar_referencia("zzzz", referencia, 5) == ([], 0)


def test_k_zero():
    referencia = construir_referencia(CHUNKS_PYTHON)
    assert recuperar_referencia("lista", referencia, 0) == ([], 0)
