# Resultados experimentais e escalabilidade

Texto-base para as seções de resultados, discussão e escalabilidade do relatório. Todos os números vêm de `experimentos/brutos/execucoes.jsonl` e das tabelas de `experimentos/processados/`, gerados por `scripts/rodar_experimentos.py` e `scripts/gerar_figuras.py` no commit `081c407`.

## Ambiente e desenho

Execução única em 22/09/2026, das 20h28 às 20h36 (horário de Brasília), num Apple M5 com 24 GB de memória, macOS, Python 3.14.7, scikit-learn 1.6.1 e numpy 2.2.2 (registro completo em `experimentos/logs/ambiente.json`).

Quatro configurações (C1, C2, C3 e a referência C4), três tamanhos de corpus (25, 50 e 100 % dos chunks, sorteados por capítulo com semente 2026: 684, 1.368 e 2.737 chunks), as 30 consultas de `data/queries.csv`, k igual a 5 e 10, cinco repetições medidas após dois aquecimentos descartados, com a ordem das configurações sorteada em cada bloco. São 3.600 execuções registradas, uma linha por execução. O mínimo do enunciado é 12.

Cada execução é medida de ponta a ponta: estatísticas do corpus (N e df), construção do índice quando existe, busca e pontuação, ordenação e corte top-k. A memória de pico vem de uma execução extra com `tracemalloc`, fora do cronômetro. As tabelas trazem mediana e intervalo interquartil, porque um pico do coletor de lixo distorce a média e não a mediana.

## Equivalência (H1)

C1, C2 e C3 devolveram a mesma lista, na mesma ordem, em todas as 180 combinações de tamanho, consulta e k. O script confere isso a cada bloco e registrou zero divergências. A diferença entre as três configurações é só de custo.

## Custo por configuração, corpus inteiro

Medianas sobre 300 execuções por linha (30 consultas, 2 valores de k, 5 repetições).

| Configuração | Total (ms) | Ingestão | Índice | Busca e pontuação | Ordenação | Consulta | Comparações | Memória de pico |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 varredura + Insertion Sort | 167,0 | 39,4 | 0 | 63,2 | 63,2 | 127,9 | 461.702 | 451 KiB |
| C2 índice + busca binária + Merge Sort | 128,6 | 39,4 | 40,8 | 45,2 | 2,3 | 47,7 | 13.039 | 1.659 KiB |
| C3 varredura + Merge Sort | 105,7 | 39,4 | 0 | 63,0 | 2,4 | 65,8 | 12.746 | 452 KiB |
| C4 scikit-learn (referência) | 87,1 | 39,4 | 47,2 | 0,4 | (junto com a busca) | 0,4 | não se aplica | 2.581 KiB |

Os tempos estão em milissegundos. "Consulta" soma busca, ordenação e corte, sem a ingestão e sem o índice. Nas 3.600 execuções nenhuma consulta devolveu lista vazia; a mediana de candidatos com escore maior que zero (P) foi 1.403 no corpus inteiro, cerca de metade dos chunks, porque palavras frequentes da consulta como "que", "como" e "uma" aparecem em quase todo trecho.

Figura sugerida: `experimentos/figuras/decomposicao_do_tempo.png`.

## Comparações contra a previsão assintótica (H2)

| Chunks (N) | Candidatos (P) | Comparações C1 | Razão | Comparações C3 | Razão |
| --- | --- | --- | --- | --- | --- |
| 684 | 352 | 29.349 | | 2.512 | |
| 1.368 | 710 | 115.210 | 3,93 | 5.752 | 2,29 |
| 2.737 | 1.403 | 461.702 | 4,01 | 12.746 | 2,22 |

Quando P dobra, as comparações do Insertion Sort multiplicam por cerca de 4, o comportamento de Θ(P²), e as do Merge Sort por pouco mais de 2, o de Θ(P log P). No corpus inteiro, o C1 faz 36 vezes mais comparações que o C3 para devolver a mesma lista.

As medições ficam próximas das curvas teóricas. Por consulta, no corpus inteiro e nos menores, o Insertion Sort fez de 85 % a 100 % de P²/4 (mediana 93 %), um pouco abaixo porque a varredura entrega os candidatos na ordem do livro, que não é uma permutação aleatória dos escores. O Merge Sort fez de 81 % a 88 % de P log₂ P (mediana 85 %), o esperado, já que cada intercalação para de comparar quando uma das metades se esgota e o pior caso é P log₂ P − P + 1. A C2 soma às comparações do Merge Sort as da busca binária no vocabulário, cerca de 2 por rodada e poucas dezenas por consulta, e por isso fica ligeiramente acima da C3.

Figuras sugeridas: `experimentos/figuras/comparacoes_por_candidatos.png` (pontos medidos sobre as curvas P²/4 e P log₂ P) e `experimentos/figuras/comparacoes_por_tamanho.png`.

## Tempo e escalabilidade (H3)

| Chunks (N) | Total C1 (ms) | Total C2 | Total C3 | Total C4 | Consulta C2 | Consulta C3 |
| --- | --- | --- | --- | --- | --- | --- |
| 684 | 29,0 | 31,3 | 25,6 | 22,0 | 11,5 | 16,0 |
| 1.368 | 68,1 | 65,6 | 53,4 | 45,6 | 24,0 | 32,9 |
| 2.737 | 167,0 | 128,6 | 105,7 | 87,1 | 47,7 | 65,8 |

C3, C2 e C4 crescem de forma aproximadamente linear em N: dobrar o corpus dobra o tempo. O C1 cresce mais que isso (2,35 e 2,45 vezes a cada dobra), porque a fatia da ordenação quadrática aumenta com o corpus: 13 % do total com 684 chunks e 38 % com 2.737. Extrapolando a razão de 4 por dobra, com um livro quatro vezes maior a ordenação do C1 passaria de 1 s por consulta, enquanto a do C3 ficaria perto de 10 ms.

A C2 tem a consulta mais rápida entre as configurações da equipe (47,7 ms contra 65,8 ms da C3), porque pontua só os chunks que contêm algum termo da consulta, encontrados pela busca binária no vocabulário ordenado. Mas construir o índice custa 40,8 ms, e no experimento ele é reconstruído a cada execução; por isso o total da C2 fica acima do da C3. Com o índice construído uma vez e reaproveitado, a C2 passa a sair mais barata que a C3 no acumulado a partir da terceira consulta (40,8 + 47,7n contra 65,8n). O preço é memória: o índice ocupa cerca de 3,7 vezes o pico da C3.

A ingestão (contagem de N e df, 39 ms no corpus inteiro) é igual em todas as configurações e é a maior parcela isolada do custo da C3. Numa aplicação real ela seria feita uma vez, junto com o índice.

## Qualidade da recuperação

Enquanto os julgamentos de relevância (`data/qrels.csv`) não estão concluídos, a tabela `experimentos/processados/qualidade_por_configuracao.md` traz um indicador auxiliar: a fração do top-k que cai na seção do livro indicada para cada consulta em `data/queries.csv`. Não substitui Precision@k, porque um trecho de outra seção pode responder a pergunta, mas mostra a tendência.

| Configuração | Top-5 na seção esperada | Fáceis | Médias | Difíceis |
| --- | --- | --- | --- | --- |
| C1, C2, C3 | 8,7 % | 8 % | 8 % | 10 % |
| C4 scikit-learn | 29,3 % | 30 % | 36 % | 22 % |

A lista da equipe e a da referência têm em comum só 10,7 % do top-5. A causa aparece em `experimentos/processados/secoes_mais_devolvidas_C1.md`: das 300 posições de top-10 da equipe, 110 (36,7 %) são do Glossário, 33 de "Pergunte a um assistente virtual" e 21 de "Exercício". Esses trechos reúnem muitos termos técnicos, e a fórmula do contrato 02 soma a contribuição de cada termo sem normalizar pelo tamanho do trecho, o que favorece quem acumula termos. A C4 usa a mesma família de tf-idf, mas normaliza os vetores (norma L2), e o escore vira um cosseno; o Glossário deixa de dominar.

A conclusão é que, neste trabalho, a escolha do algoritmo define o custo e a escolha da função de relevância define a qualidade. C1, C2 e C3 diferem em até 36 vezes nas comparações e devolvem exatamente a mesma lista; C4 muda a lista.

Quando `data/qrels.csv` existir, `python scripts/gerar_figuras.py` acrescenta Precision@k, Recall@k, nDCG@k e MRR à mesma tabela, sem refazer o experimento.

## Métricas mínimas da seção 7.3 do enunciado

| Métrica pedida | Onde está |
| --- | --- |
| Tempo de pré-processamento/ingestão | coluna `ingestao_ms` |
| Tempo de ordenação ou construção de índice | colunas `indice_ms` e `ordenacao_ms` |
| Tempo de consulta e tempo total | colunas `consulta_ms` e `total_ms` |
| Memória | coluna `memoria_pico_kib` |
| Comparações | colunas `comparacoes` e `trocas` |
| Tamanho do corpus e número de chunks | colunas `tamanho_%` e `n_chunks` |
| k | 5 e 10, uma linha por valor no log |
| Precision@k | quando houver `data/qrels.csv`; até lá, indicador auxiliar |
| Falhas, vazios, irrelevantes | `vazios_%` (zero em todas); irrelevantes pelo indicador auxiliar e depois pelo qrels |
| Custo e limitações | seções acima e a seguir |

## Custo e limitações de cada abordagem

C1 é a mais simples de implementar e de provar correta, e não usa memória extra além da lista de candidatos, mas a ordenação quadrática domina o tempo à medida que o corpus cresce.

C2 tem a consulta mais rápida e é a única que não visita todos os chunks, mas exige construir e guardar o índice, o que só compensa com várias consultas sobre o mesmo corpus, e tem a maior memória entre as configurações da equipe.

C3 mantém a varredura completa, mas troca a ordenação por Θ(P log P), e com isso a ordenação passa a ser 2 % do tempo; o gargalo vira a pontuação de todos os chunks.

C4 é a referência de mercado e, com a normalização L2, coloca mais trechos da seção esperada no topo; em compensação, a pontuação, a busca e a ordenação ficam dentro da biblioteca, sem contagem de comparações nem controle sobre o desempate além do que a equipe impôs na saída.

## Ameaças à validade

O cronômetro mede o interpretador Python tanto quanto o algoritmo; os contadores de comparações são a evidência principal, e o tempo é secundário. Três tamanhos mostram tendência, não provam ordem assintótica. Os três tamanhos são subconjuntos do mesmo livro, e P cresce junto com N, o que mistura os dois efeitos. Os chunks seguem as células dos notebooks (2.737 chunks, mediana de 13 tokens), e não janelas contínuas de 256 tokens, o que multiplica o número de trechos curtos em relação à estimativa da reserva. A dificuldade das consultas coincide com a ordem dos capítulos (fáceis nos capítulos 1 a 6, difíceis nos 13 a 18), o que confunde dificuldade lexical com assunto. Um único livro introdutório é um estudo de caso, não uma amostra de materiais educacionais abertos.
