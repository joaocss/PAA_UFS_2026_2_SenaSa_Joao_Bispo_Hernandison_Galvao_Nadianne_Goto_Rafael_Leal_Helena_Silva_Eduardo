
#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import random
import socket
import subprocess
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'src'))
from paa_context.modelos import carregar_chunks  # noqa: E402
from paa_context.pipeline import retrieve  # noqa: E402
from paa_context.relevance import build_statistics  # noqa: E402
from paa_context.selecao import ESTRATEGIAS as FUNCOES, itens_de_resultados  # noqa: E402

CHUNKS = RAIZ / 'data/processed/chunks.jsonl'
CONSULTAS = RAIZ / 'data/queries.csv'
QRELS = RAIZ / 'data/qrels.csv'
SAIDA = RAIZ / 'experimentos/av2'
TAMANHOS = (10, 30, 50)
ORCAMENTOS = (256, 512, 1024)
NOMES_ESTRATEGIAS = ('prefixo_ranking', 'guloso_valor', 'guloso_densidade',
               'guloso_modificado', 'mochila_dp')
SEMENTE = 2026


def agora():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def git_commit():
    try:
        p = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=RAIZ, text=True,
                           capture_output=True, check=True)
        return p.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return 'desconhecido'


def ler_consultas():
    with CONSULTAS.open(newline='', encoding='utf-8-sig') as arq:
        dados = list(csv.DictReader(arq))
    if not dados or any(not r.get('query_id') or not r.get('texto') for r in dados):
        raise ValueError('CSV de consultas vazio ou sem query_id/texto')
    return dados


def ler_qrels():
    julgamentos = {}
    with QRELS.open(newline='', encoding='utf-8-sig') as arq:
        for r in csv.DictReader(arq):
            if not r.get('query_id') or not r.get('chunk_id'):
                raise ValueError('Qrels sem query_id/chunk_id')
            raw = r.get('adjudicada')
            if raw is None or raw == '':
                raw = r.get('relevancia')
            if raw is None or raw == '':
                continue
            key = (r['query_id'], r['chunk_id'])
            nota = float(raw)
            if key in julgamentos and julgamentos[key] != nota:
                raise ValueError(f'Julgamentos contraditorios para {key}')
            julgamentos[key] = nota
    return julgamentos


def medir_memoria(funcao, itens, W):
    # tracemalloc captura apenas alocacoes rastreadas pelo Python.
    tracemalloc.start()
    try:
        resultado = funcao(itens, W)
        _atual, pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return resultado, pico


def metricas(selecao, itens, W, julgamentos, query_id):
    ids = selecao.ids
    notas = [julgamentos[(query_id, cid)] for cid in ids if (query_id, cid) in julgamentos]
    julgados = len(notas)
    relevantes_julgados = sum(nota > 0 for nota in notas)
    return {
        'selecionados': len(ids),
        'ids_selecionados': ids,
        'custo_total': selecao.custo_total,
        'fracao_orcamento': selecao.custo_total / W if W else 0,
        'valor_quantizado': selecao.valor_total,
        'relevancia_tfidf': selecao.relevancia_total,
        'itens_julgados': julgados,
        'itens_nao_julgados': len(ids) - julgados,
        'relevantes_entre_julgados': relevantes_julgados,
        'precisao_entre_julgados': relevantes_julgados / julgados if julgados else None,
        'soma_notas_julgadas': sum(notas),
        'celulas_tabela_dp_reportadas': selecao.celulas if selecao.estrategia == 'mochila_dp' else None,
    }


def principal():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rapido', action='store_true', help='3 consultas, 1 repeticao, nenhum aquecimento')
    parser.add_argument('--repeticoes', type=int, default=5)
    parser.add_argument('--aquecimentos', type=int, default=2)
    args = parser.parse_args()
    if args.repeticoes < 1 or args.aquecimentos < 0:
        parser.error('repeticoes >= 1 e aquecimentos >= 0')
    if not CHUNKS.is_file():
        parser.error(f'Corpus nao encontrado: {CHUNKS}. Rode preparar_corpus.py')
    if not CONSULTAS.is_file() or not QRELS.is_file():
        parser.error('Nao encontrei data/queries.csv ou data/qrels.csv')

    consultas = ler_consultas()
    if args.rapido:
        consultas = consultas[:3]
    repeticoes = 1 if args.rapido else args.repeticoes
    aquecimentos = 0 if args.rapido else args.aquecimentos
    chunks = carregar_chunks(CHUNKS)
    estatisticas = build_statistics(chunks)
    julgamentos = ler_qrels()
    SAIDA.joinpath('brutos').mkdir(parents=True, exist_ok=True)
    SAIDA.joinpath('logs').mkdir(parents=True, exist_ok=True)
    destino = SAIDA / 'brutos' / ('execucoes_rapido.jsonl' if args.rapido else 'execucoes.jsonl')
    logfile = SAIDA / 'logs' / ('ambiente_rapido.json' if args.rapido else 'ambiente.json')
    sorteio = random.Random(SEMENTE)
    iniciado = agora()
    registros = 0
    casos = 0

    with destino.open('w', encoding='utf-8') as arquivo:
        for indice, consulta in enumerate(consultas, 1):
            qid = consulta['query_id']
            t_recuperacao = time.perf_counter_ns()
            candidatos = retrieve(consulta['texto'], chunks, estatisticas,
                                  k=max(TAMANHOS), algoritmo='merge')
            tempo_recuperacao_ns = time.perf_counter_ns() - t_recuperacao
            for n in TAMANHOS:
                itens = itens_de_resultados(candidatos[:n])
                # Se a busca retornou menos de n candidatos, registramos n_real.
                for W in ORCAMENTOS:
                    casos += 1
                    metadados = {}
                    for nome in NOMES_ESTRATEGIAS:
                        funcao = FUNCOES[nome]
                        resultado, memoria_pico = medir_memoria(funcao, itens, W)
                        if resultado.custo_total > W:
                            raise AssertionError(f'{qid}, {nome}: ultrapassou W={W}')
                        metadados[nome] = (metricas(resultado, itens, W, julgamentos, qid), memoria_pico)
                    otimo = metadados['mochila_dp'][0]['valor_quantizado']
                    for nome in NOMES_ESTRATEGIAS:
                        if metadados[nome][0]['valor_quantizado'] > otimo:
                            raise AssertionError(f'{qid}: {nome} superou DP em valor quantizado')
                    for repeticao in range(-aquecimentos, repeticoes):
                        ordem = list(NOMES_ESTRATEGIAS)
                        sorteio.shuffle(ordem)
                        for nome in ordem:
                            funcao = FUNCOES[nome]
                            ini = time.perf_counter_ns()
                            selecao = funcao(itens, W)
                            duracao_ns = time.perf_counter_ns() - ini
                            if repeticao < 0:
                                continue
                            dados, memoria = metadados[nome]
                            if selecao.ids != dados['ids_selecionados']:
                                raise AssertionError(f'{qid}: selecao nao deterministica em {nome}')
                            linha = {
                                'run_id': f'{qid}-n{n}-w{W}-{nome}-r{repeticao + 1}',
                                'query_id': qid,
                                'categoria': consulta.get('categoria', ''),
                                'n_solicitado': n,
                                'n_real': len(itens),
                                'W': W,
                                'estrategia': nome,
                                'repeticao': repeticao + 1,
                                'tempo_selecao_ns': duracao_ns,
                                'tempo_recuperacao_c3_ns': tempo_recuperacao_ns,
                                'memoria_pico_selecao_bytes': memoria,
                                'otimo_valor_quantizado_dp': otimo,
                                'razao_aproximacao': (dados['valor_quantizado'] / otimo if otimo else 1.0),
                                **dados,
                            }
                            arquivo.write(json.dumps(linha, ensure_ascii=False) + '\n')
                            registros += 1
            print(f'[{indice}/{len(consultas)}] {qid}: {len(candidatos)} candidatos recuperados', flush=True)
    ambiente = {
        'inicio_utc': iniciado,
        'fim_utc': agora(),
        'comando': ' '.join(sys.argv),
        'commit': git_commit(),
        'python': platform.python_version(),
        'plataforma': platform.platform(),
        'host': socket.gethostname(),
        'cpu': platform.processor(),
        'nucleos_logicos': os.cpu_count(),
        'semente_ordem': SEMENTE,
        'estrategias': list(NOMES_ESTRATEGIAS),
        'n': list(TAMANHOS),
        'orcamentos': list(ORCAMENTOS),
        'consultas': len(consultas),
        'repeticoes': repeticoes,
        'aquecimentos_descartados': aquecimentos,
        'casos': casos,
        'execucoes': registros,
        'fonte_corpus': str(CHUNKS.relative_to(RAIZ)),
        'aviso_memoria': 'tracemalloc: pico de alocacoes Python por selecao, fora do cronometro; nao equivale a RSS',
        'aviso_qualidade': 'Nao julgados separados; precisao_entre_julgados so considera itens com qrels',
        'aviso_recuperacao': 'C3 recuperada uma vez por consulta, fora do tempo de selecao',
        'arquivo_saida': str(destino.relative_to(RAIZ)),
    }
    logfile.write_text(json.dumps(ambiente, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Concluido: {registros} medicoes, {casos} casos; arquivo: {destino.relative_to(RAIZ)}')
    print(f'Ambiente: {logfile.relative_to(RAIZ)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(principal())
