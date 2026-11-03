#!/usr/bin/env python3
"""Gera graficos e resumos das metricas complementares do Contrato 08."""
import csv
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experimentos/av2'
PROCESS = BASE / 'processados'
FIG = BASE / 'figuras'


def carregar_csv(caminho):
    with caminho.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def resumir_metricas(rows):
    grupos = defaultdict(list)
    for r in rows:
        grupos[(int(r['n']), int(r['W']), r['estrategia'])].append(r)
    saida = []
    for (n, W, est), valores in sorted(grupos.items()):
        taxas = [float(r['taxa_pares_redundantes']) for r in valores
                 if r['taxa_pares_redundantes'] not in ('', None)]
        pares = sum(int(r['pares_possiveis']) for r in valores)
        redundantes = sum(int(r['pares_redundantes']) for r in valores)
        saida.append({
            'n': n, 'W': W, 'estrategia': est,
            'consultas': len(valores),
            'media_delta_quantizado': statistics.mean(float(r['delta_valor_quantizado']) for r in valores),
            'mediana_delta_quantizado': statistics.median(float(r['delta_valor_quantizado']) for r in valores),
            'pares_redundantes_total': redundantes, 'pares_possiveis_total': pares,
            'taxa_redundancia_ponderada': redundantes / pares if pares else '',
            'taxa_media_por_consulta_valida': statistics.mean(taxas) if taxas else '',
            'consultas_com_2_ou_mais_selecionados': len(taxas),
        })
    return saida


def salvar_csv(caminho, rows):
    with caminho.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def plotar(rows, fluxos):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    FIG.mkdir(parents=True, exist_ok=True)
    nomes = {'guloso_densidade': 'S3 — Guloso densidade', 'mochila_dp': 'S5 — DP'}
    for W in (256, 512, 1024):
        fig, ax = plt.subplots(figsize=(7.6, 4.6))
        for est in nomes:
            amostra = sorted((r for r in rows if int(r['W']) == W and r['estrategia'] == est), key=lambda r: int(r['n']))
            ax.plot([int(r['n']) for r in amostra], [float(r['media_delta_quantizado']) for r in amostra], marker='o', label=nomes[est])
        ax.set(xlabel='Candidatos (n)', ylabel='Delta V medio (unidades quantizadas)', title=f'Diferenca para DP — W={W}')
        ax.grid(alpha=.25); ax.legend(); fig.tight_layout()
        fig.savefig(FIG / f'delta_valor_W{W}.png', dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 5))
    for est in nomes:
        amostra = sorted((r for r in fluxos if int(r['W']) == 1024 and r['estrategia'] == est), key=lambda r: int(r['n']))
        ax.plot([int(r['n']) for r in amostra], [float(r['mediana_fluxo_consulta_ms']) for r in amostra], marker='o', label=nomes[est])
    ax.set(xlabel='Candidatos (n)', ylabel='Mediana do fluxo de consulta (ms)', title='C3 + conversao + selecao (W=1024)')
    ax.grid(alpha=.25); ax.legend(); fig.tight_layout()
    fig.savefig(FIG / 'fluxo_completo_W1024.png', dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 5))
    for est in nomes:
        amostra = sorted((r for r in rows if int(r['W']) == 512 and r['estrategia'] == est), key=lambda r: int(r['n']))
        ax.plot([int(r['n']) for r in amostra], [float(r['taxa_redundancia_ponderada']) if r['taxa_redundancia_ponderada'] != '' else float('nan') for r in amostra], marker='o', label=nomes[est])
    ax.set(xlabel='Candidatos (n)', ylabel='Proporcao de pares redundantes', title='Redundancia por Jaccard (W=512)')
    ax.grid(alpha=.25); ax.legend(); fig.tight_layout()
    fig.savefig(FIG / 'redundancia_W512.png', dpi=160); plt.close(fig)


def main():
    entrada = PROCESS / 'metricas_complementares.csv'
    fluxo = PROCESS / 'resumo_fluxo.csv'
    if not entrada.exists() or not fluxo.exists():
        raise SystemExit('Execute antes python scripts/av2/completar_contrato08.py (sem --rapido)')
    linhas = resumir_metricas(carregar_csv(entrada))
    if len(linhas) != 45:
        raise SystemExit(f'Esperados 45 agregados, encontrados {len(linhas)}')
    salvar_csv(PROCESS / 'resumo_metricas_complementares.csv', linhas)
    plotar(linhas, carregar_csv(fluxo))
    print('Gerados resumo_metricas_complementares.csv e cinco graficos em experimentos/av2/figuras')


if __name__ == '__main__':
    main()
