from paa_context.contador import Contador
from paa_context.insertion_sort import insertion_sort
from paa_context.linear_search import CHUNKS_PYTHON, linear_search
from paa_context.merge_sort import merge_sort
from paa_context.pipeline import retrieve, top_k


def test_top_k_zero():
    ordenados = insertion_sort(linear_search("lista python", CHUNKS_PYTHON))

    assert top_k(ordenados, 0) == []


def test_top_k_negativo():
    ordenados = insertion_sort(linear_search("lista python", CHUNKS_PYTHON))

    assert top_k(ordenados, -1) == []
    assert top_k(ordenados, -5) == []


def test_top_k_dois():
    ordenados = insertion_sort(linear_search("lista python", CHUNKS_PYTHON))
    resultado = top_k(ordenados, 2)

    assert len(resultado) == 2
    assert [score for _, score in resultado] == [1.0, 0.5]
    assert resultado[0][0] == CHUNKS_PYTHON[0]
    assert resultado[1][0] == CHUNKS_PYTHON[1]


def test_top_k_maior_que_candidatos():
    ordenados = insertion_sort(linear_search("lista python", CHUNKS_PYTHON))
    resultado = top_k(ordenados, 100)

    assert len(resultado) == 3
    assert all(score > 0 for _, score in resultado)
    assert [score for _, score in resultado] == [1.0, 0.5, 0.5]


def test_top_k_exclui_score_zero():
    ordenados = insertion_sort(linear_search("lista python", CHUNKS_PYTHON))
    resultado = top_k(ordenados, 10)

    assert all(score > 0 for _, score in resultado)
    assert CHUNKS_PYTHON[2] not in [chunk for chunk, _ in resultado]
    assert CHUNKS_PYTHON[4] not in [chunk for chunk, _ in resultado]


def test_top_k_sem_candidatos():
    ordenados = insertion_sort(linear_search("recursao grafo", CHUNKS_PYTHON))

    assert top_k(ordenados, 5) == []


def test_retrieve_insertion():
    resultado = retrieve("lista python", CHUNKS_PYTHON, k=2, algoritmo="insertion")

    assert len(resultado) == 2
    assert resultado[0] == (CHUNKS_PYTHON[0], 1.0)
    assert resultado[1] == (CHUNKS_PYTHON[1], 0.5)


def test_retrieve_merge():
    resultado = retrieve("lista python", CHUNKS_PYTHON, k=2, algoritmo="merge")

    assert len(resultado) == 2
    assert resultado[0] == (CHUNKS_PYTHON[0], 1.0)
    assert resultado[1] == (CHUNKS_PYTHON[1], 0.5)


def test_retrieve_insertion_igual_merge():
    for k in (0, 1, 2, 3, 10, -1):
        a = retrieve("lista python", CHUNKS_PYTHON, k=k, algoritmo="insertion")
        b = retrieve("lista python", CHUNKS_PYTHON, k=k, algoritmo="merge")
        assert a == b


def test_retrieve_com_contador():
    contador = Contador()
    resultado = retrieve(
        "lista python",
        CHUNKS_PYTHON,
        k=2,
        algoritmo="insertion",
        contador=contador,
    )

    assert len(resultado) == 2
    assert contador.comparacoes > 0


def test_retrieve_consulta_vazia():
    assert retrieve("", CHUNKS_PYTHON, k=5) == []
