# Testes: casos e resultados esperados

Este arquivo lista, para cada caso da suíte, a entrada, a saída esperada e a função de teste que o verifica. Os valores das colunas de entrada e de saída são os que estão nas asserções do código.

## 1. Como rodar

Na raiz do repositório, com Python 3.11 ou mais recente:

```
pip install -e ".[dev]"
python -m pytest
```

A saída esperada termina em `131 passed`. O `pyproject.toml` já configura `testpaths = ["tests"]` e `pythonpath = ["src"]`, então basta ter o `pytest` instalado para a suíte rodar.

A suíte não precisa do corpus baixado. Nenhum teste lê `data/raw/` nem `data/processed/`: os testes usam os cinco trechos curtos de `CHUNKS_PYTHON`, definidos em `src/paa_context/linear_search.py`, os dados sintéticos de `tests/fixtures/` e notebooks mínimos gravados em diretório temporário durante o próprio teste.

## 2. O que a suíte cobre

| Arquivo | Testes | O que cobre |
| --- | --- | --- |
| `tests/unit/test_preprocessing.py` | 5 | `normalize`: minúsculas, remoção de acentos e de pontuação, tokenização |
| `tests/unit/test_relevance.py` | 9 | estatísticas do corpus (N, df) e o escore do contrato 02 (`tf = 1 + ln f`, idf suavizado) |
| `tests/unit/test_linear_search.py` | 8 | varredura linear: só candidatos com escore > 0, na ordem do corpus |
| `tests/unit/test_sort_key.py` | 3 | chave de ordenação `(-escore, source_order)` |
| `tests/unit/test_insertion_sort.py` | 13 | Insertion Sort (C1): casos de borda, desempate, contador |
| `tests/unit/test_merge_sort.py` | 17 | Merge Sort (C3): casos de borda, desempate, equivalência com o Insertion Sort, contador |
| `tests/unit/test_busca_binaria.py` | 9 | busca binária no vocabulário (C2), custo e comparação com o `bisect` |
| `tests/unit/test_indice.py` | 13 | índice invertido (C2): vocabulário, postings, união de postings, igualdade com C1 e C3 |
| `tests/unit/test_pipeline.py` | 12 | corte top-k e `retrieve` com os dois algoritmos de ordenação |
| `tests/unit/test_fragmentacao.py` | 12 | leitura dos notebooks e fragmentação em chunks de 256 tokens com sobreposição de 32 |
| `tests/unit/test_modelos.py` | 12 | contrato 01: formato do chunk, validação, leitura e escrita do JSONL |
| `tests/unit/test_metricas.py` | 9 | Precision@k, Recall@k, nDCG@k e reciprocal rank, com os casos de k zero e de consulta sem relevante julgado |
| `tests/unit/test_referencia.py` | 4 | referência C4 (scikit-learn): no máximo k resultados com escore positivo, escores decrescentes, termo inexistente, k zero |
| `tests/integration/test_equivalencia.py` | 5 | C1, C2 e C3 contra o gabarito dos dados sintéticos |
| **Total** | **131** | |

Terminologia, conforme `docs/CONTRATOS.md`: C1 é busca linear com Insertion Sort; C2 é índice invertido com busca binária no vocabulário e Merge Sort nos candidatos; C3 é busca linear com Merge Sort. As três ordenam pela mesma regra: maior escore primeiro e, em empate, menor `source_order`.

## 3. Casos por módulo

### Corpus de exemplo usado nos testes unitários

A maior parte dos testes unitários roda sobre `CHUNKS_PYTHON`, cinco chunks com `source_order` de 0 a 4. Nas tabelas, eles aparecem como `a` a `e`:

| Chunk | `source_order` | Texto |
| --- | --- | --- |
| `a` | 0 | "Uma lista em Python armazena elementos em uma sequencia ordenada." |
| `b` | 1 | "Uma tupla em Python e imutavel e tambem armazena uma sequencia." |
| `c` | 2 | "Um dicionario associa chaves a valores." |
| `d` | 3 | "Funcoes em Python sao definidas com a palavra def." |
| `e` | 4 | "Operadores booleanos representam verdadeiro ou falso." |

Para a consulta `"lista python"`, os candidatos são `a`, `b` e `d`. O chunk `a` tem os dois termos e fica na frente; `b` e `d` têm só `python` e empatam, e o empate se resolve por `source_order` (`b` antes de `d`).

### `tests/unit/test_preprocessing.py`

| Caso | Entrada | Saída esperada | Função |
| --- | --- | --- | --- |
| Minúsculas | `"Python"` | `["python"]` | `test_lowercase` |
| Remoção de acentos | `"função"` | `["funcao"]` | `test_remove_acentos` |
| Remoção de pontuação | `"lista, Python!"` | `["lista", "python"]` | `test_remove_pontuacao` |
| Tokenização por espaço | `"uma lista em python"` | `["uma", "lista", "em", "python"]` | `test_tokenizacao` |
| Texto vazio | `""` | `[]` | `test_string_vazia` |

### `tests/unit/test_relevance.py`

Nos cinco chunks, N = 5, `df(lista) = 1`, `df(python) = 3` e `df(uma) = 2`. Com o idf suavizado, `idf(lista) = ln(6/2) + 1` e `idf(python) = ln(6/4) + 1`.

| Caso | Entrada | Saída esperada | Função |
| --- | --- | --- | --- |
| Estatísticas do corpus | `build_statistics(CHUNKS_PYTHON)` | `n_chunks == 5`, `df["lista"] == 1`, `df["python"] == 3` | `test_estatisticas` |
| df conta chunks, não ocorrências | `"uma"`, que ocorre duas vezes em `a` e duas em `b` | `df["uma"] == 2` | `test_df_conta_chunks_e_nao_ocorrencias` |
| Todos os termos presentes | consulta `"lista python"`, chunk `a` | `idf(lista) + idf(python)` | `test_relevancia_total` |
| Termo da consulta ausente no chunk | consulta `"lista python funcao"`, chunk `a` (não contém `funcao`) | `idf(lista) + idf(python)`: o termo ausente contribui 0 | `test_relevancia_parcial` |
| Nenhum termo presente | consulta `"lista python"`, chunk `e` | `0.0` | `test_sem_relevancia` |
| Consulta vazia | `""`, chunk `a` | `0.0` | `test_query_vazia` |
| Termo repetido na consulta (qtf) | `"lista lista lista python"`, chunk com texto `"Uma lista em Python."` | `3 · idf(lista) + idf(python)` | `test_termos_repetidos` |
| Termo repetido no chunk (tf) | consulta `"uma"`, chunk `a` (2 ocorrências) | `(1 + ln 2) · (ln(6/3) + 1)` | `test_termo_repetido_no_chunk` |
| Acento na consulta e no chunk | `"recursão"` e `"recursao"`, chunk com texto `"Recursão é útil."` | escore > 0 e igual para as duas grafias | `test_remove_acentos` |

### `tests/unit/test_linear_search.py`

| Caso | Entrada | Saída esperada | Função |
| --- | --- | --- | --- |
| Só candidatos | `"lista python"` | 3 pares, todos com escore > 0 | `test_devolve_so_candidatos` |
| Ordem do corpus preservada | `"lista python"` | chunks `[a, b, d]`, sem ordenar | `test_preserva_ordem_do_corpus` |
| Escore vem de `relevance_score` | `"lista python"` | cada escore igual a `relevance_score(consulta, chunk)` | `test_reutiliza_relevance_score` |
| Mais relevante e empate | `"lista python"` | primeiro escore é o máximo; segundo e terceiro iguais | `test_chunk_mais_relevante` |
| Relevância parcial | `"lista dicionario"` | chunks `[a, c]`, com escores iguais | `test_relevancia_parcial` |
| Nenhum termo no corpus | `"recursao grafo"` | `[]` | `test_sem_relevancia` |
| Consulta vazia | `""` | `[]` | `test_consulta_vazia` |
| Corpus vazio | `"lista python"`, `[]` | `[]` | `test_corpus_vazio` |

### `tests/unit/test_sort_key.py`

Os testes usam um objeto mínimo que só tem `source_order`.

| Caso | Entrada | Saída esperada | Função |
| --- | --- | --- | --- |
| Maior escore primeiro | escore 20.0 (`source_order` 1) contra 10.0 (`source_order` 2) | chave do 20.0 é menor | `test_maior_score_vem_primeiro` |
| Empate por `source_order` | dois itens com escore 10.0, `source_order` 1 e 2 | chave do `source_order` 1 é menor | `test_empate_usa_menor_source_order` |
| Transitividade | escores 30.0, 20.0, 10.0 | chave(30) < chave(20) < chave(10) e chave(30) < chave(10) | `test_ordem_transitiva` |

### `tests/unit/test_insertion_sort.py`

As entradas são pares `(chunk, escore)`.

| Caso | Entrada | Saída esperada | Função |
| --- | --- | --- | --- |
| Lista vazia | `[]` | `[]` | `test_lista_vazia` |
| Um elemento | `[(a, 0.5)]` | `[(a, 0.5)]` | `test_um_elemento` |
| Já ordenada | `[(a, 1.0), (b, 0.5), (c, 0.0)]` | igual à entrada | `test_ja_ordenada` |
| Ordem inversa | `[(c, 0.0), (b, 0.5), (a, 1.0)]` | `[(a, 1.0), (b, 0.5), (c, 0.0)]` | `test_ordem_inversa` |
| Empate já na ordem do corpus | `[(b, 0.5), (d, 0.5)]` | igual à entrada | `test_empate_na_ordem_do_corpus` |
| Empate fora da ordem do corpus | `[(d, 0.5), (b, 0.5)]` | `[(b, 0.5), (d, 0.5)]` | `test_empate_fora_da_ordem_do_corpus` |
| Empate triplo em ordem | `[(a, 0.5), (b, 0.5), (c, 0.5)]` | igual à entrada | `test_empate_tres_elementos` |
| Empate triplo embaralhado | `[(c, 0.5), (a, 0.5), (b, 0.5)]` | `[(a, 0.5), (b, 0.5), (c, 0.5)]` | `test_empate_tres_elementos_embaralhados` |
| Entrada preservada | `[(c, 0.0), (a, 1.0)]` | a lista original não muda | `test_nao_altera_entrada` |
| Saída é permutação da entrada | resultado da busca linear para `"lista python"` | mesmo multiconjunto de escores e mesmo conjunto de chunks | `test_reutiliza_busca_linear` |
| Consulta completa (C1) | `linear_search_sorted("lista python")` | chunks `[a, b, d]`; escore de `a` maior; `b` e `d` empatados | `test_consulta_lista_python` |
| Contador na ordem inversa | `[(c, 0.0), (b, 0.5), (a, 1.0)]` | exatamente 3 comparações e 3 trocas | `test_contador_ordem_inversa` |
| Contador na lista vazia | `[]` | 0 comparações e 0 trocas | `test_contador_lista_vazia` |

### `tests/unit/test_merge_sort.py`

Os nove primeiros casos repetem os do Insertion Sort, com as mesmas entradas e saídas. Os demais comparam o Merge Sort com o Insertion Sort, que serve de referência.

| Caso | Entrada | Saída esperada | Função |
| --- | --- | --- | --- |
| Lista vazia | `[]` | `[]` | `test_lista_vazia` |
| Um elemento | `[(a, 0.5)]` | `[(a, 0.5)]` | `test_um_elemento` |
| Já ordenada | `[(a, 1.0), (b, 0.5), (c, 0.0)]` | igual à entrada | `test_ja_ordenada` |
| Ordem inversa | `[(c, 0.0), (b, 0.5), (a, 1.0)]` | `[(a, 1.0), (b, 0.5), (c, 0.0)]` | `test_ordem_inversa` |
| Empate já na ordem do corpus | `[(b, 0.5), (d, 0.5)]` | igual à entrada | `test_empate_na_ordem_do_corpus` |
| Empate fora da ordem do corpus | `[(d, 0.5), (b, 0.5)]` | `[(b, 0.5), (d, 0.5)]` | `test_empate_fora_da_ordem_do_corpus` |
| Empate triplo em ordem | `[(a, 0.5), (b, 0.5), (c, 0.5)]` | igual à entrada | `test_empate_tres_elementos` |
| Empate triplo embaralhado | `[(c, 0.5), (a, 0.5), (b, 0.5)]` | `[(a, 0.5), (b, 0.5), (c, 0.5)]` | `test_empate_tres_elementos_embaralhados` |
| Entrada preservada | `[(c, 0.0), (a, 1.0)]` | a lista original não muda | `test_nao_altera_entrada` |
| Saída é permutação da entrada | resultado da busca linear para `"lista python"` | mesmo multiconjunto de escores e mesmo conjunto de chunks | `test_reutiliza_busca_linear` |
| Consulta completa (C3) | `linear_search_merge_sorted("lista python")` | chunks `[a, b, d]`; escore de `a` maior; `b` e `d` empatados | `test_consulta_lista_python` |
| Igual ao Insertion Sort | resultado da busca linear para `"lista python"` | `merge_sort(x) == insertion_sort(x)` | `test_equivalente_ao_insertion_sort` |
| Igual ao Insertion Sort em seis consultas | `"lista python"`, `"lista dicionario"`, `"python"`, `"uma sequencia"`, `"recursao grafo"`, `""` | `merge_sort(x) == insertion_sort(x)` em todas | `test_equivalencia_varias_consultas` |
| Empate triplo no meio | `[(a, 1.0), (b, 0.5), (c, 0.5), (d, 0.5), (e, 0.0)]` | `merge_sort(x) == insertion_sort(x)` | `test_equivalencia_empate_tres` |
| Entradas embaralhadas | 50 listas dos cinco chunks, escores sorteados em {0.5, 1.0, 2.0}, semente 2026 | `merge_sort(x) == insertion_sort(x)` em todas | `test_equivalencia_entrada_embaralhada` |
| Contador incrementa | `[(c, 0.0), (b, 0.5), (a, 1.0)]` | comparações > 0 e trocas > 0 | `test_contador_incrementa` |
| Contador na lista vazia | `[]` | 0 comparações e 0 trocas | `test_contador_lista_vazia` |

### `tests/unit/test_busca_binaria.py`

Vocabulário de referência: `["classe", "dicionario", "funcao", "lista", "loop", "recursao", "string", "tupla"]`.

| Caso | Entrada | Saída esperada | Função |
| --- | --- | --- | --- |
| Primeiro termo do vocabulário | busca `"classe"` | posição 0 | `test_primeiro_termo` |
| Último termo | busca `"tupla"` | posição 7 | `test_ultimo_termo` |
| Termo ausente, entre dois existentes | busca `"metodo"` | -1 | `test_termo_entre_duas_chaves_ausente` |
| Termo fora dos limites do vocabulário | busca `"aaa"` e `"zzz"` | -1, sem estourar índice | `test_termo_fora_dos_limites` |
| Vocabulário vazio | `[]` | -1 | `test_vocabulario_vazio` |
| Vocabulário de um elemento | `["so"]`, termo presente e ausente | 0 e -1 | `test_um_elemento` |
| Custo logarítmico | os 8 termos, um a um, com contador | no máximo 8 comparações por busca. O nome fala em 4 rodadas e a asserção cobra 8 comparações porque o código faz 2 comparações por rodada (igualdade e menor que) | `test_oito_termos_no_maximo_quatro_rodadas` |
| Contador é opcional | busca `"lista"` sem passar contador | posição 3, sem erro | `test_contador_nao_e_obrigatorio` |
| Propriedade contra oráculo | 200 vocabulários aleatórios, semente 2026, 10 buscas em cada | mesma resposta do `bisect` da biblioteca padrão | `test_concorda_com_bisect_em_vocabularios_aleatorios` |

O último caso é de natureza diferente dos outros: não confere um valor escolhido à mão, confere uma propriedade contra um oráculo independente, em 2.000 buscas.

### `tests/unit/test_indice.py`

O índice é construído sobre `CHUNKS_PYTHON`. As seis consultas usadas nos testes de igualdade são `"lista python"`, `"lista dicionario"`, `"python"`, `"uma sequencia"`, `"recursao grafo"` e `""`.

| Caso | Entrada | Saída esperada | Função |
| --- | --- | --- | --- |
| Vocabulário ordenado e sem repetição | `construir_indice(CHUNKS_PYTHON)` | `vocabulario == sorted(set(vocabulario))` | `test_vocabulario_ordenado_e_sem_repeticao` |
| Vocabulário completo | idem | conjunto do vocabulário igual ao conjunto de termos normalizados dos cinco chunks | `test_vocabulario_tem_todos_os_termos` |
| Postings crescentes e corretos | cada termo do vocabulário | lista crescente das posições dos chunks que contêm o termo | `test_postings_crescentes_e_corretos` |
| Postings de um termo conhecido | `"python"` | `[0, 1, 3]` | `test_postings_de_python` |
| Índice vazio | `construir_indice([])`, busca `"lista"` | vocabulário `[]` e busca devolve `[]` | `test_indice_vazio` |
| União de postings | `[1, 3, 5]` e `[2, 3, 6]` | `[1, 2, 3, 5, 6]` | `test_unir_postings` |
| União com lista vazia | `[]` e `[2, 4]`; `[1]` e `[]`; `[]` e `[]` | `[2, 4]`; `[1]`; `[]` | `test_unir_postings_com_lista_vazia` |
| União contra oráculo | 200 pares de listas aleatórias em 0..49, semente 2026 | `sorted(set(a) \| set(b))` | `test_unir_postings_listas_aleatorias` |
| Candidatos iguais aos da busca linear | as seis consultas | `buscar_indexado(...) == linear_search(...)` | `test_igual_a_busca_linear` |
| Termo fora do vocabulário | `"recursao grafo"` | `[]` | `test_termo_fora_do_vocabulario` |
| Termo repetido na consulta | `"python python"` | chunks `[a, b, d]`, sem duplicar candidato | `test_termo_repetido_nao_duplica_candidato` |
| Contador recebe a busca binária | `"lista python"` com contador | comparações > 0 | `test_contador_soma_comparacoes_da_busca_binaria` |
| C2 igual a C1 e C3 | as seis consultas, k em 0, 1, 2, 3, 10 e -1 | `recuperar_indexado` igual a `retrieve` com `"insertion"` e com `"merge"` | `test_recuperar_indexado_igual_c1_e_c3` |

### `tests/unit/test_pipeline.py`

Salvo indicação, a entrada é a consulta `"lista python"`, cujos candidatos ordenados são `a`, `b`, `d`.

| Caso | Entrada | Saída esperada | Função |
| --- | --- | --- | --- |
| k = 0 | `top_k(ordenados, 0)` | `[]` | `test_top_k_zero` |
| k negativo | `top_k(ordenados, -1)` e `top_k(ordenados, -5)` | `[]` nos dois | `test_top_k_negativo` |
| k = 2 | `top_k(ordenados, 2)` | 2 itens: `a` e `b` | `test_top_k_dois` |
| k maior que o número de candidatos | `top_k(ordenados, 100)` | os 3 candidatos, `[a, b, d]`, todos com escore > 0 | `test_top_k_maior_que_candidatos` |
| Escore zero fica fora | `[(a, 1.0), (c, 0.0), (e, 0.0)]`, k = 10 | `c` e `e` não aparecem | `test_top_k_exclui_score_zero` |
| Sem candidatos | `"recursao grafo"`, k = 5 | `[]` | `test_top_k_sem_candidatos` |
| `retrieve` com Insertion Sort | k = 2, `"insertion"` | `[(a, escore de a), (b, escore de b)]` | `test_retrieve_insertion` |
| `retrieve` com Merge Sort | k = 2, `"merge"` | `[(a, escore de a), (b, escore de b)]` | `test_retrieve_merge` |
| Insertion e Merge iguais | k em 0, 1, 2, 3, 10 e -1 | mesma lista nos dois algoritmos | `test_retrieve_insertion_igual_merge` |
| Contador repassado | k = 2, `"insertion"`, com contador | 2 itens e comparações > 0 | `test_retrieve_com_contador` |
| Só os candidatos são ordenados | k = 2, algoritmo padrão (`"insertion"`), com contador | exatamente 2 comparações. Se os dois chunks de escore zero entrassem na ordenação, seriam 4 | `test_retrieve_ordena_so_candidatos` |
| Consulta vazia | `""`, k = 5 | `[]` | `test_retrieve_consulta_vazia` |

### `tests/unit/test_fragmentacao.py`

As células são montadas no próprio teste, com capítulo "Condicionais e Recursão". Um texto de n palavras é gerado como `"p0 p1 ... p(n-1)"`.

| Caso | Entrada | Saída esperada | Função |
| --- | --- | --- | --- |
| Normalização mantém acento | `normalizar_texto("Função")` | `"função"` | `test_normalizacao_mantem_acento` |
| Espaços compactados e caracteres invisíveis removidos | `"Variáveis"`, dois espaços de largura zero (U+200B), `"e   Instruções"` | `"variáveis e instruções"` | `test_normalizacao_compacta_espacos_e_remove_invisiveis` |
| Tokenização separa pontuação | `tokenizar("a,b. c")` | `["a", "b", "c"]` | `test_tokenizar_separa_pontuacao` |
| Célula grande vira vários chunks | célula de 700 palavras, tamanho 256, sobreposição 32 | 3 chunks, com janelas `(0, 256)`, `(224, 480)` e `(448, 700)`; o primeiro com 256 tokens | `test_celula_grande_vira_varios_chunks` |
| Célula pequena vira um chunk | célula de 100 palavras | 1 chunk com `n_tokens == 100` | `test_celula_pequena_vira_um_chunk` |
| Código e markdown não se misturam | célula de código `"x = 1"` seguida de markdown `"texto solto"` | 2 chunks, tipos `["codigo", "markdown"]` | `test_codigo_e_markdown_nunca_dividem_chunk` |
| Ids únicos e `source_order` contíguo | 5 células de 600 palavras | ids sem repetição e `source_order` de 0 a n-1 | `test_ids_unicos_e_source_order_contiguo` |
| Determinismo | célula de 300 palavras e célula de código `"print(1)"` | duas chamadas de `fragmentar` dão o mesmo resultado | `test_fragmentar_e_deterministico` |
| Sobreposição inválida | tamanho 10, sobreposição 10 | `ValueError` | `test_sobreposicao_invalida` |
| Ida e volta pelo JSONL | chunks de uma célula de 300 palavras e uma de código | `carregar_chunks(salvar_chunks(x)) == x` | `test_salvar_e_carregar_dao_a_volta` |
| Arquivo com furo em `source_order` | JSONL gravado à mão com `source_order` 0 e 7 | `ValueError` na leitura | `test_carregar_rejeita_source_order_com_furo` |
| Extração de um notebook | notebook com cabeçalho de licença, célula de download, título `#`, código, título `##`, célula `raw` e célula de código vazia | só as células 2, 3 e 4, tipos `markdown`, `codigo`, `markdown`; capítulo "Condicionais e Recursão"; seção vazia nas duas primeiras e "Recursão" na terceira; `arquivo == "chap05.ipynb"` | `test_extrair_celulas_descarta_cabecalho_e_acompanha_titulos` |

### `tests/unit/test_modelos.py`

Os casos de rejeição partem de um chunk válido (`chunk_id` `"x-c0000"`, texto `"um dois tres"`, `n_tokens` 3) e alteram um campo.

| Caso | Entrada | Saída esperada | Função |
| --- | --- | --- | --- |
| Fixture carrega completo | `chunks_sinteticos.jsonl` | 20 chunks, `source_order` de 0 a 19 | `test_fixture_carrega_vinte_chunks_em_ordem` |
| Fixture tem exatamente os campos do contrato | primeira linha do fixture | as chaves são `CAMPOS_OBRIGATORIOS`, que tem 11 campos | `test_fixture_tem_os_onze_campos_e_nada_mais` |
| Fixture tem texto e código | tipos dos 20 chunks | `{"markdown", "codigo"}` | `test_fixture_tem_texto_e_codigo` |
| Ordem por id difere da ordem de leitura | ids ordenados alfabeticamente contra ids por `source_order` | as duas listas são diferentes | `test_fixture_ordem_alfabetica_dos_ids_difere_da_source_order` |
| `chunk_id` repetido | dois chunks com `"x-c0000"` | `ChunkInvalido` com "repetido" | `test_chunk_id_repetido_e_rejeitado` |
| Buraco em `source_order` | `source_order` 0 e 2 | `ChunkInvalido` com "source_order" | `test_source_order_com_buraco_e_rejeitado` |
| `source_order` repetido | dois chunks com `source_order` 0 | `ChunkInvalido` com "source_order" | `test_source_order_repetido_e_rejeitado` |
| Tipo desconhecido | JSONL com `tipo = "html"` | `ChunkInvalido` com "tipo" | `test_tipo_desconhecido_e_rejeitado` |
| Campo ausente | JSONL sem o campo `secao` | `ChunkInvalido` com "ausentes" | `test_campo_ausente_e_rejeitado` |
| `n_tokens` inconsistente | JSONL com `n_tokens = 99` para 3 tokens | `ChunkInvalido` com "n_tokens" | `test_n_tokens_inconsistente_e_rejeitado` |
| Escrita em ordem de `source_order` | os 20 chunks do fixture, gravados em ordem inversa | a leitura devolve a lista original, em ordem | `test_salvar_e_carregar_preserva_tudo` |
| Chunk imutável | atribuir `texto = "outro"` | exceção | `test_chunk_e_imutavel` |

### `tests/integration/test_equivalencia.py`

Roda sobre os 20 chunks e as 3 consultas de `tests/fixtures/`. O gabarito de cada consulta (k = 5) está em `esperado_q01.json`, `esperado_q02.json` e `esperado_q03.json`:

| Consulta | Resultado esperado, na ordem |
| --- | --- |
| `q01` "o que é recursão" | `recursao-c0007` (10,7071), `recursao-c0008` (10,7071), `recursao-c0012` (9,5192), `listas-c0018` (9,5192), `recursao-c0011` (6,1654) |
| `q02` "exemplo de função que devolve valor" | `funcoes-c0003` (17,5828), `funcoes-c0001` (16,0740), `funcoes-c0005` (6,1152), `funcoes-c0000` (5,7706), `recursao-c0012` (5,1999) |
| `q03` "diferença entre lista e tupla" | `listas-c0015` (20,1800), `listas-c0014` (6,4706), `listas-c0018` (5,9678), `listas-c0016` (3,5247), `recursao-c0013` (3,0352) |

| Caso | Entrada | Saída esperada | Função |
| --- | --- | --- | --- |
| C1, C2 e C3 batem com o gabarito | as 3 consultas, k = 5 | mesmos `chunk_id`, na ordem do gabarito, e escores com diferença menor que 1e-6 | `test_bate_com_gabarito` |
| C1, C2 e C3 iguais entre si | as 3 consultas, k em 0, 1, 5 e 100 | `c1 == c2 == c3` | `test_c1_c2_c3_iguais` |
| Índice devolve os mesmos candidatos | as 3 consultas | `buscar_indexado(...) == linear_search(...)` | `test_indice_devolve_os_mesmos_candidatos_da_busca_linear` |
| Ordem de chegada não muda o resultado | candidatos de cada consulta, embaralhados 20 vezes, semente 2026 | Insertion Sort e Merge Sort devolvem sempre a mesma lista da referência | `test_ordem_de_entrada_nao_muda_resultado` |
| Limite de comparações do Insertion Sort | candidatos de cada consulta, P = número de candidatos | comparações ≤ P(P - 1)/2. O nome fala em P ao quadrado; a asserção usa o limite exato do pior caso | `test_insertion_no_maximo_p_ao_quadrado` |

## 4. Dados sintéticos e armadilhas

Os testes de integração e parte de `test_modelos.py` usam os dados de `tests/fixtures/`: 20 chunks inventados sobre três notebooks fictícios, 3 consultas e o gabarito de cada uma, calculado por `calcular_gabarito.py` de forma independente de `src/`. Os dados trazem armadilhas plantadas de propósito: dois empates de escore em `q01`, um deles entre chunks cuja ordem alfabética de `chunk_id` é inversa à de `source_order`, e um chunk que não contém termo de nenhuma consulta. Quem desempatar pelo id textual, ou deixar passar escore zero, falha no teste. A descrição completa das armadilhas e a conferência à mão de um escore estão em [`tests/fixtures/README.md`](fixtures/README.md).

## 5. O que a suíte não cobre

**Complexidade do Merge Sort.** Em 19/09, numa cópia descartável do repositório, a linha `mid = len(items) // 2` de `merge_sort.py` foi trocada por `mid = 1`. Nenhum dos 118 testes falhou e os resultados continuaram idênticos, mas as comparações subiram de 8.717 para 251.066 com P = 1.000 candidatos (28,8 vezes), ou seja, o algoritmo passou a ser quadrático. Corretude e complexidade são propriedades independentes: a suíte verifica a primeira e só pega a segunda quando há um limite explícito de contagem, como em `test_insertion_no_maximo_p_ao_quadrado`. Não existe limite equivalente para o Merge Sort.

**Qualidade da recuperação.** A suíte roda sobre dados sintéticos, não sobre o corpus real do livro. Ela garante que C1, C2 e C3 calculam a fórmula do contrato 02 e devolvem a mesma lista, não que essa lista seja útil para quem pergunta. Isso é papel dos experimentos, com `data/queries.csv` e os julgamentos de relevância em `data/qrels.csv`.

**Sobreposição em `test_sort_key.py`.** `test_ordem_transitiva` exercita sobretudo a comparação de tuplas do Python, já que `sort_key` só monta a tupla `(-escore, source_order)`. Os outros dois testes do arquivo verificam a mesma regra que `test_merge_sort.py` e `test_insertion_sort.py` já cobrem pelos casos de empate.

**Tempo de execução.** Nenhum teste mede tempo. O custo é verificado só pelos contadores de comparações e trocas.
