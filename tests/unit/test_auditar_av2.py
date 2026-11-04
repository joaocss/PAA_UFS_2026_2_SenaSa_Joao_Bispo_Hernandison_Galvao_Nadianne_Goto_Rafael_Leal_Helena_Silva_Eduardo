"""Auditoria do arquivo de medicao: rejeita corrupcao e duplicidade."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts/av2/auditar_av2.py'
spec = importlib.util.spec_from_file_location('auditar_av2_sob_teste', SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def gerar(caminho):
    lines = []
    for estrategia in sorted(audit.ESTRATEGIAS):
        for rep in sorted(audit.REPETICOES):
            valor = 10 if estrategia == 'mochila_dp' else 9
            lines.append(dict(
                run_id=f'Q01-n10-w256-{estrategia}-r{rep}',
                query_id='Q01', n_solicitado=10, n_real=1, W=256,
                estrategia=estrategia, repeticao=rep,
                ids_selecionados=['c1'], selecionados=1, custo_total=1,
                fracao_orcamento=1/256, valor_quantizado=valor,
                otimo_valor_quantizado_dp=10, razao_aproximacao=valor/10,
                itens_julgados=0, itens_nao_julgados=1,
                tempo_selecao_ns=100, memoria_pico_selecao_bytes=1024,
            ))
    # grade reduzida configurada apenas para os testes
    caminho.write_text(''.join(json.dumps(row) + '\n' for row in lines), encoding='utf-8')
    return lines


def test_auditoria_aprova_grade_sintetica(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'NS', {10})
    monkeypatch.setattr(audit, 'WS', {256})
    f = tmp_path / 'execucoes.jsonl'
    gerar(f)
    r = audit.auditar(f, consultas_esperadas=1)
    assert r['medicoes'] == 25
    assert r['cenarios'] == 1
    assert r['empates']['mochila_dp'] == 1


@pytest.mark.parametrize('alterar', ['duplicado', 'orcamento', 'razao', 'dp', 'repeticoes'])
def test_auditoria_rejeita_problemas(tmp_path, monkeypatch, alterar):
    monkeypatch.setattr(audit, 'NS', {10})
    monkeypatch.setattr(audit, 'WS', {256})
    f = tmp_path / 'execucoes.jsonl'
    linhas = gerar(f)
    if alterar == 'duplicado':
        linhas[1]['run_id'] = linhas[0]['run_id']
    elif alterar == 'orcamento':
        linhas[0]['custo_total'] = 999
    elif alterar == 'razao':
        linhas[0]['razao_aproximacao'] = 1.1
    elif alterar == 'dp':
        dp = next(r for r in linhas if r['estrategia'] == 'mochila_dp')
        dp['valor_quantizado'] = 9
    elif alterar == 'repeticoes':
        linhas.pop()
    f.write_text(''.join(json.dumps(row) + '\n' for row in linhas), encoding='utf-8')
    with pytest.raises(ValueError):
        audit.auditar(f, consultas_esperadas=1)
