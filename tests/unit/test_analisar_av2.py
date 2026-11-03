"""Testes isolados para scripts/av2/analisar_av2.py."""
import csv
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts' / 'av2' / 'analisar_av2.py'
spec = importlib.util.spec_from_file_location('analisar_av2_sob_teste', SCRIPT)
analise = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analise)


def caso(qid, n, W, estrategia, repeticao, tempo, valor, otimo, julgados=0):
    return {
        'query_id': qid, 'n_solicitado': n, 'n_real': n,
        'W': W, 'estrategia': estrategia, 'repeticao': repeticao,
        'tempo_selecao_ns': tempo, 'memoria_pico_selecao_bytes': 2048,
        'valor_quantizado': valor, 'otimo_valor_quantizado_dp': otimo,
        'razao_aproximacao': valor/otimo if otimo else 1.,
        'relevancia_tfidf': .8, 'fracao_orcamento': .75,
        'itens_julgados': julgados, 'itens_nao_julgados': 1 - julgados,
        'precisao_entre_julgados': 1. if julgados else None,
    }


def configurar(tmp_path, monkeypatch, dados):
    base = tmp_path / 'experimentos' / 'av2'
    fonte = base / 'brutos' / 'execucoes.jsonl'
    fonte.parent.mkdir(parents=True)
    fonte.write_text(''.join(json.dumps(r) + '\n' for r in dados), encoding='utf-8')
    monkeypatch.setattr(analise, 'RAIZ', tmp_path)
    monkeypatch.setattr(analise, 'FONTE', fonte)
    monkeypatch.setattr(analise, 'PROCESSADOS', base / 'processados')
    monkeypatch.setattr(analise, 'FIGURAS', base / 'figuras')
    return base


def test_arquivo_ausente_gera_erro(tmp_path, monkeypatch):
    monkeypatch.setattr(analise, 'FONTE', tmp_path / 'nao_existe.jsonl')
    with pytest.raises(SystemExit, match='Nao encontrei'):
        analise.main()


def test_arquivo_vazio_gera_erro(tmp_path, monkeypatch):
    configurar(tmp_path, monkeypatch, [])
    with pytest.raises(SystemExit, match='vazio'):
        analise.main()


def test_mediana():
    assert analise.median([3, 1, 2]) == 2
    assert analise.median([1, 5]) == 3
    assert analise.median([]) is None


def test_agregacao_csv_e_mediana_reais(tmp_path, monkeypatch):
    dados = [
        caso('Q01', 10, 512, 'mochila_dp', 1, 1_000_000, 100, 100, 1),
        caso('Q01', 10, 512, 'mochila_dp', 2, 3_000_000, 100, 100, 1),
        caso('Q01', 10, 512, 'mochila_dp', 3, 2_000_000, 100, 100, 1),
        caso('Q01', 10, 512, 'guloso_densidade', 1, 100_000, 90, 100),
        caso('Q01', 10, 512, 'guloso_densidade', 2, 200_000, 90, 100),
        caso('Q01', 10, 512, 'guloso_densidade', 3, 300_000, 90, 100),
        caso('Q02', 10, 512, 'mochila_dp', 1, 4_000_000, 100, 100, 1),
        caso('Q02', 10, 512, 'guloso_densidade', 1, 200_000, 80, 100),
    ]
    base = configurar(tmp_path, monkeypatch, dados)
    analise.main()
    with (base / 'processados/resumo_por_caso.csv').open(encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 4
    dp = next(r for r in rows if r['query_id'] == 'Q01' and r['estrategia'] == 'mochila_dp')
    assert float(dp['tempo_mediano_ms']) == pytest.approx(2.0)
    assert float(dp['memoria_pico_kib']) == pytest.approx(2.0)
    assert int(dp['repeticoes']) == 3
    with (base / 'processados/resumo_por_configuracao.csv').open(encoding='utf-8') as f:
        agg = list(csv.DictReader(f))
    assert len(agg) == 2
    g = next(r for r in agg if r['estrategia'] == 'guloso_densidade')
    assert float(g['media_razao_aproximacao']) == pytest.approx(.85)
    assert int(g['consultas']) == 2
    assert g['media_precisao_entre_julgados'] == ''
    assert (base / 'figuras/razao_aproximacao_W512.png').is_file()
    assert (base / 'figuras/tempo_por_n_W512.png').is_file()
    assert (base / 'figuras/memoria_por_W_n10.png').is_file()
