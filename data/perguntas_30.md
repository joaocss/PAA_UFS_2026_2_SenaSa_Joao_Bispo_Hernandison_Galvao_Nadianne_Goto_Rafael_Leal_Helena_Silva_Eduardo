# Conjunto de consultas para avaliação do sistema de recuperação de contexto

Autora: Helena Carvalho Leal (frente de consultas, julgamentos de relevância e limitações).
Disciplina: Projeto e Análise de Algoritmos (PROCC0083), PROCC/UFS, 2026.2, Atividade 1, Tema 8.
Versão de 21/09/2026, revisada em 22/09/2026.
Versão legível por máquina: `data/queries.csv`, no formato do contrato 03 de `docs/CONTRATOS.md`.

## 1. Contexto

Este entregável apresenta um conjunto de 30 perguntas destinadas à avaliação de um protótipo de recuperação de contexto para aplicações de Inteligência Artificial Generativa.

O corpus utilizado no experimento é o livro *Pense Python*, tradução livre da 3ª edição de *Think Python*, de Allen B. Downey, feita por Rodrigo Castelan Carlson. O recorte são os 21 notebooks do repositório de origem no commit `cfde2c4` (prefácio, introdução ao Jupyter e capítulos 1 a 19); a ficha completa, com fonte, hashes e licenças, está em `data/README.md`. O sistema de recuperação recebe uma consulta em linguagem natural e retorna os k trechos, ou *chunks*, considerados mais relevantes.

A recuperação implementada nesta etapa é lexical e utiliza uma representação baseada em TF-IDF (Term Frequency-Inverse Document Frequency). O TF-IDF atribui maior peso aos termos que são frequentes em um determinado documento ou *chunk*, mas menos frequentes no conjunto total de documentos.

A fórmula usada pelas configurações C1, C2 e C3 é a do contrato 02 de `docs/CONTRATOS.md`. Para um termo t da consulta q e um *chunk* c, com f(t, c) ocorrências de t em c, N *chunks* no corpus e df(t) *chunks* que contêm t:

```
tf(t, c)     = 1 + ln f(t, c), se f(t, c) > 0; senão 0
idf(t)       = ln((N + 1) / (df(t) + 1)) + 1
escore(q, c) = soma, sobre os termos distintos t de q, de qtf(t) · tf(t, c) · idf(t)
```

em que qtf(t) é o número de ocorrências de t na consulta. Trechos com escore zero não são devolvidos, e empates são desfeitos pela posição do trecho no livro (`source_order`). A configuração de referência C4 (`TfidfVectorizer` do scikit-learn) usa o mesmo tf e o mesmo idf, mas normaliza os vetores (norma L2) e pontua por cosseno; por isso a lista dela pode diferir da lista das três configurações da equipe.

O pré-processamento realizado antes da recuperação, o mesmo para a consulta e para o *chunk* (função `normalize`, em `src/paa_context/preprocessing.py`), inclui:

1. conversão do texto para letras minúsculas;
2. remoção de acentos;
3. substituição de caracteres não alfanuméricos por espaços;
4. tokenização do texto.

As perguntas foram definidas antes da execução do sistema de recuperação, como exige o contrato 03, evitando que os resultados retornados pelo sistema influenciassem a formulação das consultas utilizadas na avaliação.

## 2. Critérios de construção

O conjunto foi organizado em três níveis de dificuldade:

- 10 perguntas fáceis: apresentam forte correspondência lexical com a terminologia utilizada no corpus;
- 10 perguntas médias: apresentam alguma variação de vocabulário, mantendo termos importantes em comum com o conteúdo relevante;
- 10 perguntas difíceis: apresentam formulações mais naturais ou indiretas, reduzindo a correspondência lexical direta com os trechos esperados.

O nível de cada pergunta foi atribuído pela autora no momento da redação, a partir da proximidade estimada entre a formulação e o vocabulário do trecho esperado; ele não foi medido.

As perguntas foram construídas exclusivamente a partir de conceitos presentes na 3ª edição em português do livro, tomando como referência a lista de seções dos 21 notebooks, e distribuídas por diferentes capítulos e tópicos, incluindo operadores, expressões, variáveis, funções, condicionais, recursão, iteração, strings, listas, dicionários, tuplas, arquivos, classes, objetos, métodos, herança e conjuntos.

A divisão por dificuldade tem como objetivo permitir a análise do comportamento do mecanismo de recuperação diante de diferentes níveis de proximidade lexical entre a consulta e o corpus.

## 3. Conjunto de perguntas

| ID | Pergunta | Dificuldade | Tema principal | Palavras-chave esperadas | Capítulo e seção provável |
| --- | --- | --- | --- | --- | --- |
| Q01 | Qual é a diferença entre divisão convencional e divisão inteira em Python? | Fácil | Operadores aritméticos | divisão, divisão inteira, operador, inteiro | Cap. 1: Operadores aritméticos (ver também Cap. 5: Divisão inteira e módulo) |
| Q02 | Como os parênteses alteram a ordem de operações em uma expressão? | Fácil | Expressões | expressão, parênteses, ordem, operações | Cap. 1: Expressões |
| Q03 | Como criar uma variável e atribuir um valor a ela em Python? | Fácil | Variáveis e atribuição | variável, valor, atribuição, expressão | Cap. 2: Variáveis |
| Q04 | Quais nomes podem ou não ser usados como nomes de variáveis em Python? | Fácil | Nomes de variáveis | nomes, variáveis, palavra-chave, sintaxe | Cap. 2: Nomes de variáveis |
| Q05 | Como definir uma nova função com def e depois chamá-la? | Fácil | Definição de funções | função, def, definição, chamada | Cap. 3: Definindo novas funções |
| Q06 | Qual é a relação entre um argumento passado para uma função e seu parâmetro? | Fácil | Parâmetros e argumentos | argumento, parâmetro, função, valor | Cap. 3: Parâmetros |
| Q07 | O que significa encapsular um código em uma função e como um parâmetro pode generalizar essa função? | Fácil | Encapsulamento e generalização | encapsulamento, generalização, função, parâmetro | Cap. 4: Encapsulamento e generalização |
| Q08 | Como usar if, elif e else para tratar diferentes condições em um programa? | Fácil | Condicionais | if, elif, else, condição | Cap. 5: Instruções if / A cláusula `else` / Condicionais encadeadas |
| Q09 | O que é recursão e como uma função pode chamar a si mesma? | Fácil | Recursão | recursão, função, chamada, recursiva | Cap. 5: Recursão |
| Q10 | Como uma função usa return para devolver um valor? | Fácil | Valores devolvidos | return, valor devolvido, função, variável | Cap. 6: Algumas funções devolvem valores |
| Q11 | Como usar um laço for para percorrer os caracteres de uma string? | Média | Iteração em strings | for, string, caracteres, variável de iteração | Cap. 7: Laços de repetição e *strings* |
| Q12 | Como ler um arquivo de palavras linha por linha e remover a quebra de linha de cada palavra? | Média | Leitura de arquivos | open, readline, strip, arquivo | Cap. 7: Lendo a lista de palavras |
| Q13 | Como atualizar uma variável dentro de um laço para contar ocorrências? | Média | Atualização de variáveis | atualização, variável, incremento, laço | Cap. 7: Atualizando variáveis |
| Q14 | Como acessar o último caractere de uma string usando um índice negativo? | Média | Índices em strings | string, índice, negativo, caractere | Cap. 8: Uma *string* é uma sequência |
| Q15 | Por que não é possível alterar diretamente um caractere de uma string em Python? | Média | Imutabilidade de strings | string, imutável, TypeError, caractere | Cap. 8: *Strings* são imutáveis |
| Q16 | Como append e extend alteram uma lista de maneiras diferentes? | Média | Métodos de listas | append, extend, lista, elementos | Cap. 9: Métodos de listas |
| Q17 | Por que duas variáveis podem acabar se referindo ao mesmo objeto lista? | Média | Referências e objetos | variável, lista, objeto, referência | Cap. 9: Objetos e valores / *Aliasing* |
| Q18 | Como um dicionário associa uma chave a um valor e como recuperar esse valor? | Média | Mapeamento com dicionários | dicionário, chave, valor, mapeamento | Cap. 10: Um dicionário é um mapeamento |
| Q19 | Por que verificar a existência de uma chave em um dicionário pode ser muito mais rápido do que procurar um elemento em uma lista? | Média | Eficiência de busca | dicionário, lista, in, tabela hash | Cap. 10: O operador `in` |
| Q20 | Como a atribuição de tupla permite trocar os valores de duas variáveis sem usar uma variável temporária? | Média | Atribuição de tuplas | tupla, atribuição, variáveis, temporária | Cap. 11: Atribuição de tupla |
| Q21 | Se eu fornecer apenas o nome memo.txt, como o Python decide em qual diretório procurar o arquivo e como obtenho seu caminho completo? | Difícil | Caminhos de arquivos | diretório atual, caminho relativo, caminho absoluto, abspath | Cap. 13: Nomes de arquivos e caminhos |
| Q22 | Por que modificar uma lista recuperada de uma prateleira não atualiza automaticamente o valor armazenado nela? | Difícil | Persistência de estruturas de dados | prateleira, lista, chave, atualizar, shelve | Cap. 13: Armazenando estruturas de dados |
| Q23 | Como criar um tipo próprio para representar uma hora do dia e armazenar hora, minuto e segundo dentro de cada objeto? | Difícil | Classes e atributos | classe, Time, objeto, atributos, instanciação | Cap. 14: Tipos definidos pelo programador / Atributos |
| Q24 | Quando uma função recebe um objeto Time e altera seus atributos, por que o objeto original também é modificado? | Difícil | Mutabilidade de objetos | objeto, Time, mutável, atributos, modificar | Cap. 14: Objetos são mutáveis |
| Q25 | Por que start.print_time() consegue usar start dentro do método mesmo sem ele aparecer explicitamente entre os argumentos da chamada? | Difícil | Métodos e self | método, self, objeto, receptor, argumento | Cap. 15: Definindo métodos |
| Q26 | O que precisa ser definido em Time para que dois objetos possam ser somados usando diretamente o operador +? | Difícil | Sobrecarga de operador | `__add__`, operador, Time, método especial, sobrecarga | Cap. 15: Sobrecarga de operador |
| Q27 | Por que copiar um Rectangle pode fazer o original e a cópia continuarem compartilhando o mesmo objeto Point? | Difícil | Cópia rasa e profunda | copy, deepcopy, Rectangle, Point, cópia profunda | Cap. 16: Cópia profunda |
| Q28 | Como dois objetos diferentes podem representar o mesmo ponto sem serem o mesmo objeto na memória? | Difícil | Identidade e equivalência | identidade, equivalência, objeto, is, == | Cap. 16: Equivalência e identidade |
| Q29 | Como criar uma classe mais específica que reutiliza atributos e métodos de outra classe, mas acrescenta comportamento próprio? | Difícil | Herança e especialização | herança, classe mãe, classe filha, especialização | Cap. 17: Mães e filhas / Especialização |
| Q30 | Como eliminar valores repetidos de uma sequência sem percorrer manualmente todos os elementos para verificar duplicatas? | Difícil | Conjuntos | set, conjunto, elementos únicos, duplicatas | Cap. 18: Conjuntos |

Os nomes de seção são os títulos exatos das seções nos notebooks, inclusive o itálico e o código, para que a coluna possa ser conferida contra `data/processed/chunks.jsonl`.

## 4. Verificação do conjunto

### 4.1 Distribuição por dificuldade

O conjunto possui exatamente 30 perguntas, distribuídas da seguinte forma:

- 10 perguntas fáceis: Q01 a Q10;
- 10 perguntas médias: Q11 a Q20;
- 10 perguntas difíceis: Q21 a Q30.

Essa distribuição permite analisar separadamente o desempenho da recuperação em consultas com diferentes níveis de correspondência vocabular com o corpus.

### 4.2 Cobertura de capítulos e tópicos

As perguntas cobrem conteúdos dos capítulos 1 a 11 e dos capítulos 13 a 18 da 3ª edição de *Pense Python*. Ficam de fora o capítulo 12 (Análise e geração de texto), o capítulo 19 (Considerações finais), o prefácio e a introdução ao Jupyter, que completam os 21 notebooks do corpus. A seleção não busca necessariamente produzir o mesmo número de questões para cada capítulo, mas incluir diferentes tipos de conteúdo e diferentes níveis de dificuldade lexical.

Entre os principais tópicos contemplados estão:

- operadores aritméticos e expressões;
- variáveis e atribuição;
- nomes de variáveis e palavras-chave;
- funções;
- parâmetros e argumentos;
- encapsulamento e generalização;
- condicionais;
- recursão;
- valores devolvidos;
- iteração;
- atualização de variáveis;
- leitura de arquivos;
- strings e índices;
- imutabilidade;
- listas e seus métodos;
- referências a objetos;
- dicionários e tabelas hash;
- tuplas;
- caminhos e diretórios;
- persistência de estruturas de dados;
- classes e atributos;
- mutabilidade de objetos;
- métodos e self;
- sobrecarga de operadores;
- identidade e equivalência;
- cópia rasa e profunda;
- herança e especialização;
- conjuntos.

### 4.3 Como as consultas serão julgadas

O julgamento de relevância segue o contrato 03 de `docs/CONTRATOS.md` e é humano. As colunas `capitulo_esperado` e `secao_esperada` de `data/queries.csv` reproduzem a última coluna da tabela acima e servem de ponto de partida para o julgamento, não o substituem: um trecho de outra seção pode responder à pergunta, e um trecho da seção esperada pode não responder.

Para cada consulta, `python scripts/montar_qrels.py pool` reúne os trechos a julgar: todos os trechos da seção esperada e os dez primeiros devolvidos pela configuração C3 (a mesma lista de C1 e C2). A planilha resultante, `data/processed/qrels_para_julgar.csv`, traz o texto dos trechos e por isso fica fora do versionamento, como o corpus; gerada em 22/09/2026, ela tem 754 linhas para as 30 consultas. Cada linha recebe relevância 0 (o trecho não ajuda a responder), 1 (ajuda em parte) ou 2 (responde à pergunta), com dois avaliadores independentes, metade das consultas cada, e o valor conciliado registrado na coluna `adjudicada`. Em seguida, `python scripts/montar_qrels.py consolidar` grava `data/qrels.csv` e recusa qualquer linha sem julgamento, para que nenhuma sugestão automática entre como se fosse avaliação.

Com o `qrels.csv` pronto, `python scripts/gerar_figuras.py` calcula Precision@k, Recall@k, nDCG@k e MRR, com k em 5 e 10, para as quatro configurações, sem refazer o experimento. Até lá, `docs/RESULTADOS.md` usa como indicador auxiliar a fração do top-k que cai na seção esperada.

### 4.4 Limitações do conjunto

Os três níveis de dificuldade coincidem com a ordem do livro: as perguntas fáceis vêm dos capítulos 1 a 6, as médias dos capítulos 7 a 11 e as difíceis dos capítulos 13 a 18. Dificuldade e posição no livro ficam, portanto, confundidas. Uma diferença de desempenho entre níveis pode vir do vocabulário mais específico dos capítulos finais (objetos, métodos, `self`), e não só da formulação das perguntas, e a análise por nível deve considerar os dois fatores juntos.

O capítulo e a seção prováveis são a expectativa da autora, não a verdade de referência. A Q01, por exemplo, também é respondida pela seção Divisão inteira e módulo do capítulo 5, que a configuração C3 devolve entre os dez primeiros trechos. O que conta como acerto é definido pelos julgamentos de relevância, e não por esta coluna.

As palavras-chave esperadas registram os termos que a autora previa encontrar nos trechos relevantes e servem para conferir a cobertura lexical do conjunto; elas não entram na pontuação.
