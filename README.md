# Recuperação de contexto para IA generativa em materiais educacionais abertos

Protótipo da Atividade 1 (AV1) de Projeto e Análise de Algoritmos, PROCC/UFS, período 2026.2. O sistema recebe uma consulta em português e devolve os trechos mais relevantes de um livro-texto aberto, comparando três estratégias algorítmicas de recuperação e ordenação.

Tema 8: materiais educacionais abertos.

## Equipe

| Integrante | Frente principal |
| --- | --- |
| João Cosme Sena Sá | Dados de teste, pacote e testes, protocolo experimental, índice invertido e busca binária (C2), entrega |
| Eduardo Henrique do Lago Silva | Experimentos, tabelas, gráfico e baseline de referência (C4) |
| Helena Carvalho Leal | Consultas, julgamentos de relevância, métricas, relação com IA generativa e limitações |
| Hernandison da Silva Bispo | Ingestão, normalização e fragmentação; manutenção do relatório |
| Nadianne Maria dos Santos Galvão | Corretude, modelo RAM, complexidade e recorrências |
| Rafael Takeguma Goto | Busca linear, Insertion Sort, Merge Sort, pontuação e consulta (C1 e C3) |

A tabela de contribuições com evidências está em `docs/CONTRIBUICOES.md`.

## Vídeo da atividade

Gravações individuais (a URL do vídeo consolidado substitui esta lista quando a junção for publicada):

- João Cosme Sena Sá: https://www.loom.com/share/aab4b4cd6a934bb892fd6c4bb73bcd85
- Helena Carvalho Leal: https://drive.google.com/file/d/1mrltLobY4q7kejFFrKunLzwvc68bTs38/view?usp=drive_link
- Nadianne Maria dos Santos Galvão: https://drive.google.com/file/d/1WWhyEl1k9qLuE8Sod03WE9qJ3bNDWx3Y/view?usp=drive_link
- Rafael Takeguma Goto: https://drive.google.com/file/d/13jiWmtcPA6ZGqowYDyxqEHd5966waPa8/view?usp=sharing

Dados completos de gravação e participantes em `VIDEO.md`.

## Corpus

Pense Python, tradução livre da 3ª edição de Think Python, de Allen B. Downey, traduzida por Rodrigo Castelan Carlson.

Fonte: https://rodrigocarlson.github.io/PensePython3ed/ e https://github.com/rodrigocarlson/PensePython3ed

Licenças do material original: texto em CC BY-NC-SA 4.0, códigos em MIT.

O texto do corpus não é versionado neste repositório. O que está aqui é o script de aquisição, que baixa o material no commit registrado, e o manifesto com os hashes que permitem conferir se o download reproduz o mesmo recorte. A ficha completa do corpus está em `data/README.md`.

## O que o protótipo faz

O pipeline vai da ingestão até a lista ordenada de trechos: baixa o corpus no commit fixado, normaliza o texto, segmenta em chunks que respeitam a hierarquia do livro, pontua cada chunk contra a consulta por frequência de termo e frequência inversa de documento, e devolve os k mais relevantes sob uma ordem total determinística.

Três configurações são comparadas sobre os mesmos dados e a mesma função de pontuação:

- C1: varredura linear com Insertion Sort implementado pela equipe (baseline).
- C2: índice invertido com busca binária no vocabulário, seguido de Merge Sort dos candidatos (busca indexada).
- C3: mesma varredura linear de C1 com Merge Sort implementado pela equipe (divisão e conquista).

A numeração segue a seção 7.1 do enunciado. As regras que todo o código segue estão em `docs/CONTRATOS.md`; a divisão de trabalho e as datas em `docs/PLANEJAMENTO.md`.

Uma quarta configuração usa o TF-IDF do scikit-learn apenas como referência externa. Ela não substitui nenhuma implementação exigida e é analisada em separado.

## Requisitos

Python 3.11 ou superior. As dependências estão travadas em `requirements.lock`.

```
python -m venv .venv
source .venv/bin/activate     # no Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Os testes rodam com `pytest` e usam só os dados sintéticos de `tests/fixtures/`, então não dependem do corpus baixado.

## Reprodução

O comando abaixo executa tudo, do download aos gráficos (cerca de 15 minutos; `--rapido` roda uma versão reduzida para conferir o fluxo):

```
python scripts/reproduzir_tudo.py
```

Os estágios também rodam isolados, na ordem:

```
python scripts/baixar_corpus.py        # baixa e registra hashes em data/corpus_manifest.csv
python scripts/preparar_corpus.py      # normaliza e gera data/processed/chunks.jsonl
python scripts/rodar_experimentos.py   # C1 a C4 x 3 tamanhos x 30 consultas x k 5 e 10 x 5 repetições, grava em experimentos/brutos
python scripts/gerar_figuras.py        # tabelas em experimentos/processados e gráficos em experimentos/figuras
python scripts/medir_ingestao.py       # tempo de ingestão e sensibilidade ao tamanho do chunk (128/16, 256/32, 512/64)
```

Para uma consulta avulsa, depois de preparar o corpus (`--config` aceita C1, C2 ou C3):

```
python scripts/consultar.py --consulta "o que é recursão" --k 5 --config C1
```

O julgamento de relevância é humano. O gabarito da equipe está em `data/perguntas_30_com_chunks_justificativas.csv`, e `python scripts/montar_qrels.py importar` o converte em `data/qrels.csv`. Como alternativa, `python scripts/montar_qrels.py pool` gera uma planilha de julgamento a partir dos resultados e `python scripts/montar_qrels.py consolidar` grava o `qrels.csv` depois de preenchida.

`preparar_corpus.py --notebooks 8` limita o corte aos oito primeiros notebooks, como no checkpoint de 10/09. O protocolo de medição está em `docs/PROTOCOLO_EXPERIMENTAL.md`.

Todos os scripts são idempotentes: rodar duas vezes produz o mesmo resultado e não duplica arquivos.

Cada execução registra hostname, processador, memória, sistema operacional, versão do Python, versões das bibliotecas, commit e linha de comando completa em `experimentos/logs`.

## Estrutura

```
src/paa_context/     fragmentacao, pontuacao, ordenacao, busca linear, busca binaria, indice, metricas
scripts/             comandos de ponta a ponta
tests/               unitários, integração e fixtures versionadas
data/                manifesto do corpus, consultas e julgamentos de relevância
experimentos/        dados brutos, processados, logs e figuras
relatorio/           relatório em PDF e fontes
slides/              apresentação e fontes
docs/                corretude, uso de IA e contribuições
```

## Licença

O código deste repositório está sob licença MIT, conforme o arquivo `LICENSE`. As condições do material de origem são outras e estão descritas em `data/README.md`; qualquer trecho do corpus reproduzido no relatório preserva atribuição a autor e tradutor.

## Documentos relacionados

- `docs/CORRETUDE.md`: teorema, prova por indução do Merge Sort, invariante do merge e limites do argumento.
- `docs/USO_DE_IA.md`: declaração de uso de IA generativa, preenchida durante o trabalho.
- `docs/CONTRIBUICOES.md`: contribuição individual com evidências.
