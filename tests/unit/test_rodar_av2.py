"""Testes unitarios e de integracao isolada para scripts/av2/rodar_av2.py."""
import csv
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts' / 'av2' / 'rodar_av2.py'
spec = importlib.util.spec_from_file_location('rodar_av2_sob_teste', SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

from paa_context.selecao import Item, Selecao, ESTRATEGIAS  # noqa: E402


def item(nome, custo, valor, posicao):
    return Item(nome, custo, valor, posicao, posicao, valor / 1000)


def test_metricas_com_julgados_e_nao_julgados():
    itens = [item('a', 4, 800, 0), item('b', 3, 700, 1)]
    selecao = Selecao('guloso_densidade', itens)
    m = runner.metricas(selecao, itens, 10, {('Q1', 'a'): 2}, 'Q1')
    assert m['ids_selecionados'] == ['a', 'b']
    assert m['custo_total'] == 7
    assert m['fracao_orcamento'] == pytest.approx(.7)
    assert m['valor_quantizado'] == 1500
    assert m['relevancia_tfidf'] == pytest.approx(1.5)
    assert m['itens_julgados'] == 1
    assert m['itens_nao_julgados'] == 1
    assert m['precisao_entre_julgados'] == 1
    assert m['soma_notas_julgadas'] == 2


def test_metricas_sem_julgamentos_ou_orcamento_zero():
    s = Selecao('mochila_dp', [], celulas=1)
    m = runner.metricas(s, [], 0, {}, 'Q1')
    assert m['fracao_orcamento'] == 0
    assert m['precisao_entre_julgados'] is None
    assert m['celulas_tabela_dp_reportadas'] == 1
    assert m['selecionados'] == 0


@pytest.mark.parametrize('nome', list(ESTRATEGIAS))
def test_estrategias_respeitam_orcamento_e_sao_deterministicas(nome):
    itens = [item('a', 6, 700, 0), item('b', 5, 600, 1), item('c', 3, 450, 2)]
    a = ESTRATEGIAS[nome](itens, 9)
    b = ESTRATEGIAS[nome](itens, 9)
    assert a.custo_total <= 9
    assert a.ids == b.ids
    assert len(set(a.ids)) == len(a.ids)


def test_dp_e_otima_em_instancia_pequena():
    itens = [item('a', 4, 600, 0), item('b', 5, 850, 1), item('c', 6, 900, 2)]
    dp = ESTRATEGIAS['mochila_dp'](itens, 10)
    bf = ESTRATEGIAS['forca_bruta'](itens, 10) if 'forca_bruta' in ESTRATEGIAS else None
    assert dp.valor_total == 1500
    if bf is not None:
        assert dp.valor_total == bf.valor_total
    assert dp.custo_total <= 10


def test_memoria_medida_fora_do_cronometro_e_encerrada():
    itens = [item('a', 2, 500, 0)]
    s, pico = runner.medir_memoria(ESTRATEGIAS['mochila_dp'], itens, 3)
    assert s.valor_total == 500
    assert isinstance(pico, int) and pico >= 0
    assert not runner.tracemalloc.is_tracing()


def test_memoria_desliga_mesmo_se_funcao_falhar():
    def falha(_itens, _w):
        raise RuntimeError('erro simulado')
    with pytest.raises(RuntimeError, match='erro simulado'):
        runner.medir_memoria(falha, [], 1)
    assert not runner.tracemalloc.is_tracing()


def test_leitura_consultas_valida_arquivo(tmp_path, monkeypatch):
    p = tmp_path / 'queries.csv'
    p.write_text('query_id,texto,categoria\nQ01,consulta de teste,facil\n', encoding='utf-8')
    monkeypatch.setattr(runner, 'CONSULTAS', p)
    assert runner.ler_consultas()[0]['texto'] == 'consulta de teste'
    p.write_text('query_id,texto\nQ01,\n', encoding='utf-8')
    with pytest.raises(ValueError, match='CSV de consultas'):
        runner.ler_consultas()


def test_qrels_prioriza_adjudicada_e_ignora_vazio(tmp_path, monkeypatch):
    p = tmp_path / 'qrels.csv'
    p.write_text('query_id,chunk_id,relevancia,adjudicada\nQ01,a,0,2\nQ01,b,1,\nQ01,c,,\n', encoding='utf-8')
    monkeypatch.setattr(runner, 'QRELS', p)
    assert runner.ler_qrels() == {('Q01', 'a'): 2., ('Q01', 'b'): 1.}


def test_qrels_duplicado_contraditorio_falha(tmp_path, monkeypatch):
    p = tmp_path / 'qrels.csv'
    p.write_text('query_id,chunk_id,relevancia\nQ01,a,1\nQ01,a,2\n', encoding='utf-8')
    monkeypatch.setattr(runner, 'QRELS', p)
    with pytest.raises(ValueError, match='contraditorios'):
        runner.ler_qrels()


def test_execucao_integrada_sintetica_isolada(tmp_path, monkeypatch):
    """Percorre o CLI principal, usando dados sinteticos e paths temporarios.

    Nao regrava dados reais e testa contagem, chaves, restricao e metadata.
    """
    d = tmp_path / 'projeto'
    (d / 'data' / 'processed').mkdir(parents=True)
    (d / 'data' / 'processed' / 'chunks.jsonl').write_text('{}\n', encoding='utf-8')
    (d / 'data' / 'queries.csv').write_text('query_id,texto,categoria\nQ01,teste,facil\n', encoding='utf-8')
    (d / 'data' / 'qrels.csv').write_text('query_id,chunk_id,relevancia\nQ01,c0,1\n', encoding='utf-8')
    monkeypatch.setattr(runner, 'RAIZ', d)
    monkeypatch.setattr(runner, 'CHUNKS', d / 'data/processed/chunks.jsonl')
    monkeypatch.setattr(runner, 'CONSULTAS', d / 'data/queries.csv')
    monkeypatch.setattr(runner, 'QRELS', d / 'data/qrels.csv')
    monkeypatch.setattr(runner, 'SAIDA', d / 'experimentos/av2')
    monkeypatch.setattr(runner, 'TAMANHOS', (1, 2))
    monkeypatch.setattr(runner, 'ORCAMENTOS', (3, 6))
    fake_chunks = [SimpleNamespace(chunk_id='c0', n_tokens=2, source_order=0),
                   SimpleNamespace(chunk_id='c1', n_tokens=3, source_order=1)]
    monkeypatch.setattr(runner, 'carregar_chunks', lambda _: fake_chunks)
    monkeypatch.setattr(runner, 'build_statistics', lambda _: {})
    chamadas = []
    def fake_retrieve(query, chunks, stats, k, algoritmo):
        chamadas.append((query, k, algoritmo))
        return [(chunks[0], .8), (chunks[1], .7)]
    monkeypatch.setattr(runner, 'retrieve', fake_retrieve)
    monkeypatch.setattr(sys, 'argv', [str(SCRIPT), '--rapido'])
    assert runner.principal() == 0
    saida = d / 'experimentos/av2/brutos/execucoes_rapido.jsonl'
    rows = [json.loads(x) for x in saida.read_text(encoding='utf-8').splitlines()]
    assert len(chamadas) == 1
    assert chamadas[0][2] == 'merge'
    assert len(rows) == 2 * 2 * 5
    assert len({r['run_id'] for r in rows}) == len(rows)
    assert all(r['custo_total'] <= r['W'] for r in rows)
    assert all(0 <= r['razao_aproximacao'] <= 1 for r in rows)
    assert all(r['tempo_selecao_ns'] >= 0 for r in rows)
    assert all(r['memoria_pico_selecao_bytes'] >= 0 for r in rows)
    assert (d / 'experimentos/av2/logs/ambiente_rapido.json').is_file()


def test_argumentos_invalidos_sao_rejeitados(monkeypatch):
    monkeypatch.setattr(sys, 'argv', [str(SCRIPT), '--repeticoes', '0'])
    with pytest.raises(SystemExit) as err:
        runner.principal()
    assert err.value.code == 2
