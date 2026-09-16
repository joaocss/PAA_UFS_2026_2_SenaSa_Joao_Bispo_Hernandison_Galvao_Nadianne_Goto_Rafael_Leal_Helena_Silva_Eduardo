import csv
import json
import random
from pathlib import Path

from paa_context.contador import Contador
from paa_context.insertion_sort import insertion_sort
from paa_context.linear_search import linear_search
from paa_context.merge_sort import merge_sort
from paa_context.modelos import carregar_chunks
from paa_context.pipeline import retrieve
from paa_context.relevance import build_statistics

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

CHUNKS = carregar_chunks(FIXTURES / "chunks_sinteticos.jsonl")
ESTATISTICAS = build_statistics(CHUNKS)

with (FIXTURES / "consultas_sinteticas.csv").open(encoding="utf-8") as arquivo:
    CONSULTAS = list(csv.DictReader(arquivo))


def carregar_esperado(query_id):
    caminho = FIXTURES / f"esperado_{query_id}.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def test_bate_com_gabarito():
    for consulta in CONSULTAS:
        esperado = carregar_esperado(consulta["query_id"])
        ids_esperados = [linha["chunk_id"] for linha in esperado["resultados"]]

        for algoritmo in ("insertion", "merge"):
            resultado = retrieve(consulta["texto"], CHUNKS, ESTATISTICAS, k=esperado["k"], algoritmo=algoritmo)

            assert [chunk.chunk_id for chunk, _ in resultado] == ids_esperados
            for (_, score), linha in zip(resultado, esperado["resultados"]):
                assert abs(score - linha["escore"]) < 1e-6


def test_insertion_igual_merge():
    for consulta in CONSULTAS:
        for k in (0, 1, 5, 100):
            a = retrieve(consulta["texto"], CHUNKS, ESTATISTICAS, k=k, algoritmo="insertion")
            b = retrieve(consulta["texto"], CHUNKS, ESTATISTICAS, k=k, algoritmo="merge")
            assert a == b


def test_ordem_de_entrada_nao_muda_resultado():
    # Simula a C2, em que os candidatos saem do indice fora da ordem do corpus.
    gerador = random.Random(2026)
    for consulta in CONSULTAS:
        candidatos = linear_search(consulta["texto"], CHUNKS, ESTATISTICAS)
        referencia = insertion_sort(candidatos)

        for _ in range(20):
            embaralhados = list(candidatos)
            gerador.shuffle(embaralhados)
            assert insertion_sort(embaralhados) == referencia
            assert merge_sort(embaralhados) == referencia


def test_insertion_no_maximo_p_ao_quadrado():
    for consulta in CONSULTAS:
        candidatos = linear_search(consulta["texto"], CHUNKS, ESTATISTICAS)
        contador = Contador()

        insertion_sort(candidatos, contador=contador)

        p = len(candidatos)
        assert contador.comparacoes <= p * (p - 1) // 2
