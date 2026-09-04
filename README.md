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

URL: a preencher até 22/09/2026.

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
pip install -r requirements.lock
```

## Reprodução

O comando abaixo executa tudo, do download aos gráficos:

```
python scripts/reproduzir_tudo.py
```

Os estágios também rodam isolados, na ordem:

```
python scripts/baixar_corpus.py        # baixa e registra hashes em data/corpus_manifest.csv
python scripts/preparar_corpus.py      # normaliza e gera os chunks
python scripts/rodar_experimentos.py   # 45 execuções, grava em experimentos/brutos
python scripts/gerar_figuras.py        # tabelas e gráficos em experimentos/figuras
```

Todos os scripts são idempotentes: rodar duas vezes produz o mesmo resultado e não duplica arquivos.

Cada execução registra hostname, processador, memória, sistema operacional, versão do Python, versões das bibliotecas, commit e linha de comando completa em `experimentos/logs`.

## Estrutura

```
src/paa_contexto/    aquisicao, normalizacao, fragmentacao, pontuacao, ordenacao, busca, indice, metricas
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
