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

## 5.1 Qualidade com julgamentos humanos (qrels)

A qualidade da função objetivo TF-IDF (valor quantizado e razão de aproximação) não deve ser confundida com relevância humana. Para esta última, a Parte D reutiliza o gabarito da AV1 em `data/qrels.csv`: **146** pares consulta–chunk com relevância **1**, julgados pela Helena **antes** dos rankings da recuperação. O gabarito contém apenas julgamentos positivos; a ausência de um chunk no arquivo **não** significa que ele seja irrelevante.

Para cada seleção agregada por consulta, `n` e `W`, foram contados os itens escolhidos presentes no gabarito (`itens_julgados`) e os demais (`itens_nao_julgados`). A cobertura observada nos 270 cenários foi:

| Estratégia | Ocorrências julgadas / selecionadas | Cobertura |
|---|---:|---:|
| S1 — Prefixo do ranking | 81 / 756 | 10,71% |
| S2 — Guloso por valor | 143 / 964 | 14,83% |
| S3 — Guloso por densidade | 269 / 1.575 | 17,08% |
| S4 — Guloso modificado | 269 / 1.575 | 17,08% |
| S5 — Programação dinâmica | 266 / 1.587 | 16,76% |

Quando havia pelo menos um item julgado na seleção, a métrica `precisao_entre_julgados` resultou sempre em **1,0**. Esse valor é **tautológico** no desenho atual do gabarito: todos os pares em `qrels.csv` têm relevância 1, de modo que a razão não observa falsos positivos e **não** equivale à Precision@k da AV1 nem a uma precisão do conjunto escolhido sobre o universo completo de chunks.

A comparação descritiva entre as estratégias principais mostra diferença pequena: S3 acumulou três ocorrências julgadas a mais que S5 (269 versus 266), com coberturas próximas (17,08% e 16,76%). Essa magnitude, somada à baixa fração de itens com julgamento, **não** sustenta as hipóteses H1/H2 da proposta experimental D1 em `docs/CONTRATOS_AV2.md` nem um ranking semântico entre seletores.

Métricas do Contrato 08 já medidas e distintas da relevância humana:

- **Utilização do orçamento** (média sobre os 270 cenários): S3 88,00%; S5 96,40%. No cenário `n = 50`, `W = 1024`: S3 94,92%; S5 99,44%.
- **Redundância lexical** (Jaccard ≥ 0,8 entre conjuntos de palavras): zero pares redundantes em todas as estratégias (por exemplo, S3 0/5.140 e S5 0/5.216). Zero pares nesse limiar **não** implica ausência de redundância semântica.

**Conclusão desta subseção:** a Parte D demonstra o compromisso entre otimalidade da função objetivo quantizada e custo computacional. A evidência de qualidade semântica via `qrels` é parcial e descritiva; não autoriza afirmar superioridade semântica da programação dinâmica sobre o guloso por densidade, nem o contrário.

## 6. Limitações

A programação dinâmica garante otimalidade para a função objetivo quantizada, não necessariamente maior relevância semântica.

A cobertura dos julgamentos disponíveis foi limitada: 269 de 1.575 ocorrências selecionadas por S3 (17,08%) e 266 de 1.587 por S5 (16,76%) possuíam julgamento. A seção 5.1 detalha o método, a tabela completa por estratégia e a interpretação correta de `precisao_entre_julgados`.

Consequentemente, não é possível afirmar superioridade semântica geral das estratégias com base nessa cobertura.

As métricas adicionais da proposta D1 (fração de tokens relevantes, cobertura/recall sobre \(R(q)\), cobertura máxima alcançável do top-\(n\), amostra cega de pares fora do gabarito e cenários com \(n \in \{100,200\}\)) **não** foram executadas nesta entrega e permanecem fora do escopo do Contrato 08 cumprido pela grade `n ∈ {10,30,50}` × `W ∈ {256,512,1024}`.

O custo `n_tokens` corresponde a unidades lexicais/palavras do corpus da AV1, não à tokenização de um LLM específico.

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
## Avaliação complementar — Contrato 08

### Diferença absoluta de valor (ΔV)

A diferença de valor quantizado foi calculada por:

\[
\Delta V = V_{\mathrm{DP}} - V_{\mathrm{estratégia}}
\]

Nas 270 configurações de consulta, candidatos e orçamento, foram produzidos 1.350 registros complementares para as cinco estratégias.

Os maiores valores médios de ΔV por configuração foram:

| Estratégia | Configuração | Maior ΔV médio |
|---|---|---:|
| S3 — Guloso por densidade | n=30, W=1024 | 13.785,47 |
| S4 — Guloso modificado | n=30, W=1024 | 13.785,47 |
| S2 — Guloso por valor | n=50, W=1024 | 166.923,90 |
| S1 — Prefixo do ranking | n=50, W=1024 | 205.809,07 |
| S5 — Programação dinâmica | — | 0 |

As diferenças foram calculadas sobre os valores quantizados utilizados pelos algoritmos. Não devem ser confundidas com diferenças diretas entre os escores TF-IDF originais.

### Redundância textual

Foi adotado o critério de similaridade de Jaccard entre conjuntos de palavras, classificando como redundante um par de chunks com similaridade igual ou superior a 0,8.

| Estratégia | Pares redundantes / possíveis | Taxa |
|---|---:|---:|
| S1 | 0 / 1.137 | 0% |
| S2 | 0 / 1.763 | 0% |
| S3 | 0 / 5.140 | 0% |
| S4 | 0 / 5.140 | 0% |
| S5 | 0 / 5.216 | 0% |

Não foram identificados pares acima desse limiar nas configurações avaliadas. Esse resultado não implica ausência de redundância semântica.

### Tempo completo do fluxo de consulta

Além da seleção isolada, foi realizada uma segunda série experimental que mede recuperação C3, conversão dos candidatos e seleção.

Foram obtidas 1.620 medições, correspondentes a 270 cenários, duas estratégias principais (S3 e S5) e três repetições.

No cenário n=10, W=256, foram observadas as seguintes medianas agregadas:

| Estratégia | Tempo do fluxo |
|---|---:|
| S3 — Guloso por densidade | 138,4361 ms |
| S5 — Programação dinâmica | 138,1148 ms |

Nesse cenário, a recuperação C3 apresentou participação dominante no tempo do fluxo. A diferença entre as medianas não deve ser interpretada isoladamente como superioridade de desempenho da DP, devido à variabilidade entre execuções.

O carregamento do corpus e a construção das estatísticas não integram essa medida do fluxo de consulta e devem ser documentados como etapas de preparação.

### Rastreabilidade do corpus

Os arquivos `data/chunks.jsonl` e `data/processed/chunks.jsonl` apresentaram o mesmo SHA-256:

`2af8c533a2a872a6381307ae8e5b02eadd20c9b110a84e892d4b18bb12863cc4`

Assim, foi confirmada sua equivalência byte a byte no ambiente utilizado.

### Validação complementar

Foram aprovados 14 testes específicos adicionais, elevando para 39 os testes desenvolvidos especificamente para a Parte D.

A suíte completa do projeto retornou código de saída 0.

A auditoria das 6.750 medições originais permaneceu aprovada. A auditoria complementar verificou 1.620 registros do fluxo, 540 grupos de medição e 1.350 registros de métricas, sem inconsistências nas regras examinadas.

Os resultados complementares encontram-se em `experimentos/av2/`, separados dos resultados da AV1.

### Limitações

A redundância foi avaliada apenas por similaridade lexical de Jaccard com limiar 0,8.

As medições do fluxo completo foram realizadas para S3 e S5, enquanto os demais seletores participaram da avaliação de seleção isolada.

A recuperação foi medida novamente na série complementar, mas o pré-processamento permanece separado. A baixa cobertura do gabarito de relevância limita conclusões sobre qualidade semântica.


## 8. Conclusão

A programação dinâmica apresentou o maior valor quantizado, conforme sua garantia teórica. As estratégias gulosas por densidade e modificada ofereceram aproximações elevadas com menor tempo de execução e menor pico de alocações rastreadas.

Os resultados evidenciam o compromisso entre qualidade da otimização e custo computacional na seleção de contexto sob orçamento de palavras. A avaliação de relevância semântica permanece limitada pela cobertura dos julgamentos disponíveis, conforme a discussão metodológica da seção 5.1.
