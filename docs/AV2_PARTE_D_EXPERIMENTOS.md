# AV2 — Parte D: Experimentos e Comparação

## 1. Objetivo

Avaliar experimentalmente algoritmos de seleção de chunks textuais sob orçamento de palavras, comparando qualidade da função objetivo, tempo de execução e uso de memória.

A programação dinâmica (S5) é utilizada como referência ótima para a função objetivo quantizada. As demais estratégias são avaliadas em relação a esse valor.

## 2. Ambiente e dados

- Corpus: conjunto de chunks do livro *Pense Python*, preparado na AV1.
- Consultas: 30 consultas previamente definidas.
- Recuperação: configuração C3, com busca linear e Merge Sort.
- Linguagem: Python 3.12.16, executado em ambiente virtual no Fedora Linux.
- Registro do ambiente: `experimentos/av2/logs/ambiente.json`.

## 3. Configuração experimental

Foram avaliadas cinco estratégias:

- S1 — Prefixo do ranking.
- S2 — Guloso por valor.
- S3 — Guloso por densidade.
- S4 — Guloso modificado.
- S5 — Mochila 0/1 por programação dinâmica.

O protocolo utilizou:

- Quantidade de candidatos: n ∈ {10, 30, 50}.
- Orçamento de palavras: W ∈ {256, 512, 1024}.
- Cinco repetições cronometradas por combinação.
- Dois aquecimentos descartados.
- Semente 2026 para a ordem de execução.

Foram considerados 270 cenários de consulta, quantidade de candidatos e orçamento, totalizando 6.750 medições cronometradas.

A recuperação C3 foi realizada separadamente, fora da medição de seleção. A memória foi medida com `tracemalloc`, também fora do cronômetro.

## 4. Métricas

As métricas registradas incluem tempo de seleção, pico de alocações Python rastreadas, valor quantizado, relevância TF-IDF original, custo em palavras, utilização do orçamento e razão de aproximação em relação à DP.

A razão de aproximação é calculada por:

\[
R = \frac{V_{\text{estratégia}}}{V_{\text{DP}}}
\]

Para casos em que ambas as soluções têm valor zero, o protocolo define a razão como 1.

As avaliações baseadas em julgamentos humanos são tratadas separadamente da função objetivo TF-IDF.

## 5. Resultados principais

No cenário n = 50 e W = 1024, as medianas de tempo foram:

| Estratégia | Tempo (ms) | Memória (KiB) | Aproximação média |
|---|---:|---:|---:|
| DP | 7,2771 | 854,07 | 100,00% |
| Guloso por densidade | 0,3030 | 7,34 | 97,78% |
| Guloso modificado | 0,3477 | 7,34 | 97,78% |
| Guloso por valor | 0,0675 | 7,34 | 67,71% |
| Prefixo do ranking | 0,0607 | 7,18 | 59,81% |

Em 270 cenários, foram observados os seguintes empates no valor quantizado com a DP:

| Estratégia | Empates | Menor razão observada |
|---|---:|---:|
| S3 | 79 | 73,54% |
| S4 | 85 | 78,44% |
| S2 | 43 | 30,04% |
| S1 | 14 | 20,54% |

Os resultados mostram que S3 e S4 obtiveram boas aproximações ao objetivo quantizado, com custos computacionais inferiores aos da DP.

## 6. Limitações

A programação dinâmica garante otimalidade para a função objetivo quantizada, não necessariamente maior relevância semântica.

A cobertura dos julgamentos disponíveis foi limitada: 269 de 1.575 ocorrências selecionadas por S3 (17,08%) e 266 de 1.587 por S5 (16,76%) possuíam julgamento.

Consequentemente, não é possível afirmar superioridade semântica geral das estratégias com base nessa cobertura.

As medições com `tracemalloc` representam alocações Python rastreadas, não a memória residente total do processo.

As repetições utilizam os mesmos dados e devem ser interpretadas como repetições de desempenho, não como observações independentes de relevância.

## 7. Reprodutibilidade

Na raiz do repositório, com as dependências instaladas:

```bash
python scripts/av2/rodar_av2.py
python scripts/av2/analisar_av2.py
python -m pytest -q --disable-warnings
```

Resultados disponíveis em:

- `experimentos/av2/brutos/execucoes.jsonl`
- `experimentos/av2/processados/resumo_por_caso.csv`
- `experimentos/av2/processados/resumo_por_configuracao.csv`
- `experimentos/av2/figuras/`
- `experimentos/av2/logs/ambiente.json`

## Validação e auditoria dos resultados

A implementação experimental foi submetida a verificações automatizadas para avaliar sua consistência e reprodutibilidade.

**Validação dos scripts:** foram executados 25 testes específicos, distribuídos entre os módulos `test_rodar_av2.py`, `test_analisar_av2.py` e `test_auditar_av2.py`. Todos passaram no ambiente Fedora Linux com Python 3.12.16 e pytest 8.3.4.

**Auditoria dos resultados:** o script `scripts/av2/auditar_av2.py` foi executado sobre o conjunto completo de medições, retornando `AUDITORIA AV2: APROVADA`. Foram confirmadas 30 consultas, 270 cenários, 1.350 combinações de cenário e estratégia e 6.750 medições.

A auditoria também confirmou a consistência dos valores armazenados, das razões de aproximação e dos resultados agregados relativos à programação dinâmica.

**Testes de regressão:** a suíte completa do repositório foi executada com `python -m pytest -q --disable-warnings`, terminando com código de saída `0`.

Essas verificações fornecem evidências de consistência experimental, mas não eliminam todas as possíveis ameaças à validade, incluindo limitações da cobertura de julgamentos e dependência do ambiente de execução.

### Comandos de validação

```bash
python scripts/av2/auditar_av2.py
python -m pytest -v tests/unit/test_rodar_av2.py tests/unit/test_analisar_av2.py tests/unit/test_auditar_av2.py
python -m pytest -q --disable-warnings
```


## 8. Conclusão

A programação dinâmica apresentou o maior valor quantizado, conforme sua garantia teórica. As estratégias gulosas por densidade e modificada ofereceram aproximações elevadas com menor tempo de execução e menor pico de alocações rastreadas.

Os resultados evidenciam o compromisso entre qualidade da otimização e custo computacional na seleção de contexto sob orçamento de palavras. A avaliação de relevância semântica permanece limitada pela cobertura dos julgamentos disponíveis.
