import random

from paa_context.contador import Contador
from paa_context.indice import buscar_indexado, construir_indice, recuperar_indexado, unir_postings
from paa_context.linear_search import CHUNKS_PYTHON, linear_search
from paa_context.pipeline import retrieve
from paa_context.preprocessing import normalize
from paa_context.relevance import build_statistics

ESTATISTICAS = build_statistics(CHUNKS_PYTHON)
INDICE = construir_indice(CHUNKS_PYTHON)

CONSULTAS = ["lista python", "lista dicionario", "python", "uma sequencia", "recursao grafo", ""]


def test_vocabulario_ordenado_e_sem_repeticao():
    assert INDICE.vocabulario == sorted(set(INDICE.vocabulario))


def test_vocabulario_tem_todos_os_termos():
    termos = set()
    for chunk in CHUNKS_PYTHON:
        termos.update(normalize(chunk.texto))

    assert set(INDICE.vocabulario) == termos


def test_postings_crescentes_e_corretos():
    for termo, postings in zip(INDICE.vocabulario, INDICE.postings):
        esperado = [i for i, chunk in enumerate(CHUNKS_PYTHON) if termo in normalize(chunk.texto)]
        assert postings == esperado


def test_postings_de_python():
    i = INDICE.vocabulario.index("python")

    assert INDICE.postings[i] == [0, 1, 3]


def test_indice_vazio():
    indice = construir_indice([])

    assert indice.vocabulario == []
    assert buscar_indexado("lista", indice, build_statistics([])) == []


def test_unir_postings():
    assert unir_postings([1, 3, 5], [2, 3, 6]) == [1, 2, 3, 5, 6]


def test_unir_postings_com_lista_vazia():
    assert unir_postings([], [2, 4]) == [2, 4]
    assert unir_postings([1], []) == [1]
    assert unir_postings([], []) == []


def test_unir_postings_listas_aleatorias():
    rng = random.Random(2026)
    for _ in range(200):
        a = sorted(rng.sample(range(50), rng.randrange(0, 20)))
        b = sorted(rng.sample(range(50), rng.randrange(0, 20)))
        assert unir_postings(a, b) == sorted(set(a) | set(b))


def test_igual_a_busca_linear():
    for consulta in CONSULTAS:
        assert buscar_indexado(consulta, INDICE, ESTATISTICAS) == linear_search(consulta, CHUNKS_PYTHON, ESTATISTICAS)


def test_termo_fora_do_vocabulario():
    assert buscar_indexado("recursao grafo", INDICE, ESTATISTICAS) == []


def test_termo_repetido_nao_duplica_candidato():
    resultado = buscar_indexado("python python", INDICE, ESTATISTICAS)

    assert [chunk for chunk, _ in resultado] == [CHUNKS_PYTHON[0], CHUNKS_PYTHON[1], CHUNKS_PYTHON[3]]


def test_contador_soma_comparacoes_da_busca_binaria():
    contador = Contador()

    buscar_indexado("lista python", INDICE, ESTATISTICAS, contador=contador)

    assert contador.comparacoes > 0


def test_recuperar_indexado_igual_c1_e_c3():
    for consulta in CONSULTAS:
        for k in (0, 1, 2, 3, 10, -1):
            c2 = recuperar_indexado(consulta, INDICE, ESTATISTICAS, k)
            assert c2 == retrieve(consulta, CHUNKS_PYTHON, ESTATISTICAS, k, algoritmo="insertion")
            assert c2 == retrieve(consulta, CHUNKS_PYTHON, ESTATISTICAS, k, algoritmo="merge")
