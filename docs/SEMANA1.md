# Semana 1: de 04 a 10/09, Rafael, Hernandison e João

Objetivo do checkpoint de 10/09, em sala: uma pergunta entra pelo terminal e os cinco melhores trechos do livro saem, sobre pelo menos 8 capítulos reais, com o contador de comparações impresso junto. Tudo o que está aqui serve a isso. O que não serve fica para a semana 2.

Os contratos em `docs/CONTRATOS.md` valem para todo arquivo desta lista. Nomes de módulos, funções e variáveis em português, sem acento, `snake_case`.

## Uma decisão que precisa ser tomada antes de tudo

O que é "um token" para nós. O plano fala em chunks de 256 tokens, e isso pode ser lido como token de LLM ou como palavra. Decisão: **token é uma palavra após a normalização**, obtida por expressão regular sobre letras, dígitos e sublinhado, com acentos preservados. É simples, auditável e o mesmo tokenizador serve para o texto e para a consulta. Fica registrado na ficha do corpus e no relatório.

## Ordem de dependência

```
modelos.py + fixtures (João, dia 1)
    ├── ordenacao.py (Rafael, dia 1, não depende de nada)
    ├── pontuacao.py → busca_linear.py (Rafael, dias 2 e 3)
    │       └── recuperacao.py → scripts/consultar.py (Rafael, dias 4 e 5)
    ├── indice.py + busca_binaria.py (João, dias 2 e 3, contra os fixtures)
    └── normalizacao.py → fragmentacao.py → scripts/preparar_corpus.py (Hernandison, até 07/09)
            └── chunks reais para o CLI e para o índice (integração, dias 4 e 5)
pyproject + CI + tests/README + protocolo (João, dias 4 e 5)
```

O único bloqueio real é o primeiro dia: Rafael precisa do `Chunk` e dos fixtures para escrever `busca_linear`. Por isso João entrega isso primeiro, antes de qualquer outra coisa. `ordenacao.py` não depende de chunk nenhum, então Rafael começa por ele. A fragmentação real não bloqueia ninguém na primeira semana porque todos programam contra os fixtures; ela só precisa existir para a demonstração de 10/09. Se não estiver pronta em 07/09, João assume.

## Rafael

### `src/paa_contexto/ordenacao.py`

```python
@dataclass
class Contador:
    comparacoes: int = 0
    trocas: int = 0

def insertion_sort(itens: list, chave: Callable, contador: Contador) -> list
def merge_sort(itens: list, chave: Callable, contador: Contador) -> list
```

- Recebem qualquer lista e uma função `chave` que devolve uma tupla comparável. Para os chunks, a chave é `(-escore, source_order)`, mas o módulo não sabe disso: só compara chaves.
- Devolvem lista nova, não alteram a entrada.
- `contador.comparacoes` incrementa em **toda** comparação entre chaves de dois itens, sem exceção. `contador.trocas` incrementa em cada deslocamento no Insertion Sort e em cada cópia para a lista de saída no merge. A definição exata vai em docstring, porque a Nadianne vai usar isso na análise RAM.
- Merge Sort recursivo, dividindo ao meio. Sem otimização de "já está ordenado" nem troca para Insertion em listas pequenas: qualquer atalho muda a recorrência que a Nadianne vai escrever.

Testes em `tests/unit/test_ordenacao.py`, para os dois algoritmos:

| Caso | Entrada | Esperado |
|---|---|---|
| lista vazia | `[]` | `[]`, 0 comparações |
| um elemento | `[x]` | `[x]`, 0 comparações |
| já ordenada, n = 8 | `[1..8]` | igual; Insertion faz exatamente 7 comparações; Merge faz entre 12 e 17 |
| ordem inversa, n = 8 | `[8..1]` | `[1..8]`; Insertion faz exatamente 28 comparações |
| chaves empatadas | itens com escore igual e `source_order` diferente | saem por `source_order` crescente |
| entrada preservada | qualquer | a lista original continua igual depois da chamada |
| propriedade | 200 listas aleatórias com semente fixa | saída igual a `sorted(itens, key=chave)` |

### `src/paa_contexto/pontuacao.py`

```python
def tokenizar(texto: str) -> list[str]
@dataclass
class Estatisticas:
    n_chunks: int
    df: dict[str, int]          # em quantos chunks cada termo aparece
def construir_estatisticas(chunks: list[Chunk]) -> Estatisticas
def pontuar(termos_consulta: list[str], chunk: Chunk, est: Estatisticas) -> float
```

- Fórmula do contrato 02: `tf = 1 + ln f` se o termo ocorre, senão 0; `idf = ln((N + 1) / (df + 1)) + 1`; escore = soma de `qtf · tf · idf` sobre os termos distintos da consulta.
- `tokenizar` é o único lugar que decide o que é uma palavra. `fragmentacao.py` do João importa daqui, não reimplementa.

Testes em `tests/unit/test_pontuacao.py`:

| Caso | Esperado |
|---|---|
| termo ausente no chunk | contribui 0 |
| termo presente uma vez | `tf = 1` |
| termo presente `e` vezes | `tf = 2` |
| termo em todos os chunks vs. em um só | idf menor no primeiro |
| consulta vazia | escore 0 para qualquer chunk |
| valor conhecido | um mini corpus de 3 chunks calculado à mão, escore batendo com 6 casas |

### `src/paa_contexto/busca_linear.py`

```python
@dataclass
class Candidato:
    chunk_id: str
    source_order: int
    escore: float
def buscar_linear(chunks: list[Chunk], termos_consulta: list[str], est: Estatisticas) -> list[Candidato]
```

- Percorre todos os chunks, pontua cada um, devolve só os de escore maior que zero, na ordem em que apareceram. Não ordena: ordenação é responsabilidade do próximo módulo.

Testes em `tests/unit/test_busca_linear.py`: escore zero fica fora; consulta sem termo conhecido devolve lista vazia sem erro; a ordem de saída é a ordem de entrada.

### `src/paa_contexto/recuperacao.py`

```python
def recuperar(chunks, consulta: str, k: int, config: str, est: Estatisticas) -> tuple[list[tuple[str, float]], Contador]
```

- `config` em `"C1"` (busca linear + Insertion) e `"C3"` (busca linear + Merge). `"C2"` (índice + busca binária + Merge) chama `buscar_indexado` do João quando existir; até lá levanta `NotImplementedError`.
- Aplica a chave `(-escore, source_order)`, corta em `min(k, len(candidatos))`, devolve pares `(chunk_id, escore)` e o contador.
- `k <= 0` devolve lista vazia.

Testes em `tests/integration/test_equivalencia.py`: para cada consulta em `tests/fixtures/consultas_sinteticas.csv`, `recuperar(..., "C1")` e `recuperar(..., "C3")` devolvem exatamente a mesma lista, e essa lista bate com `tests/fixtures/esperado_<query_id>.json`. Esse é o teste que o professor vai querer ver rodando.

### `scripts/consultar.py`

```
python scripts/consultar.py --consulta "o que é recursão" --k 5 --config C1
```

Imprime, para cada resultado: posição, `chunk_id`, capítulo, escore com 4 casas, e as primeiras 120 letras do texto. No fim, uma linha com número de chunks varridos, candidatos com escore > 0, comparações e trocas. É a demonstração do dia 10.

## João

### Dia 1: `src/paa_contexto/modelos.py` e os fixtures

```python
@dataclass(frozen=True)
class Chunk:
    chunk_id: str; source_order: int; texto: str; tipo: str; arquivo: str
    capitulo: str; secao: str; celula_idx: int; token_inicio: int; token_fim: int; n_tokens: int
def carregar_chunks(caminho: Path) -> list[Chunk]
def salvar_chunks(chunks: list[Chunk], caminho: Path) -> None
```

- `carregar_chunks` valida: `chunk_id` único, `source_order` contíguo de 0 a n-1, `tipo` em {markdown, codigo}. Erro claro se falhar, porque é aqui que um arquivo mal gerado é pego.

`tests/fixtures/chunks_sinteticos.jsonl`: 20 chunks inventados, em português, sobre 3 "capítulos" fictícios, com:
- pelo menos 2 chunks de código e 18 de texto;
- pelo menos dois pares que empatam de propósito na consulta "recursão" (mesma contagem do termo, mesmo tamanho);
- um chunk que não contém nenhum termo de nenhuma consulta de teste (para provar que escore zero fica fora);
- `source_order` fora de ordem alfabética de `chunk_id`, para provar que o desempate usa `source_order` e não o id.

`tests/fixtures/consultas_sinteticas.csv` com 3 consultas no cabeçalho do contrato 03, e `tests/fixtures/esperado_<query_id>.json` com a lista correta de `(chunk_id, escore)` para k = 5, calculada à mão ou em planilha e conferida por Rafael. Sem esse "gabarito" o teste de equivalência só prova que C1 e C3 erram igual.

### Dias 2 e 3: índice invertido e busca binária (configuração C2)

`src/paa_contexto/indice.py`

```python
@dataclass
class Posting:
    source_order: int
    chunk_id: str
    frequencia: int
@dataclass
class IndiceInvertido:
    vocabulario: list[str]                 # ordenado, para a busca binária
    postings: dict[str, list[Posting]]
def construir_indice(chunks: list[Chunk]) -> IndiceInvertido
def busca_binaria(vocabulario: list[str], termo: str, contador: Contador) -> int   # índice ou -1
def buscar_indexado(indice: IndiceInvertido, termos_consulta: list[str], est: Estatisticas, contador: Contador) -> list[Candidato]
```

- `busca_binaria` conta cada comparação de string no `contador`, como a ordenação do Rafael. É o que a Nadianne vai usar para a recorrência `T(V) = T(V/2) + Θ(1)`.
- `buscar_indexado` só pontua chunks que aparecem nos postings de algum termo da consulta. O resultado tem que ser igual ao de `buscar_linear` para a mesma consulta, a menos da ordem: essa é a metade do teste de equivalência.
- Depende de `pontuacao.py` do Rafael para a fórmula. Enquanto ele não entrega, dá para escrever o índice e a busca binária, que não usam a nota.

Testes em `tests/unit/test_indice.py`:

| Caso | Esperado |
|---|---|
| primeiro termo do vocabulário | encontrado, posição 0 |
| último termo | encontrado, última posição |
| termo entre duas chaves, ausente | -1, sem exceção |
| termo menor que o primeiro e maior que o último | -1, sem sair dos limites |
| vocabulário vazio | -1 |
| vocabulário de 8 termos, termo presente | no máximo 4 comparações |
| conjunto de candidatos | igual ao conjunto de `buscar_linear` com escore > 0, para as 3 consultas dos fixtures |

### Dias 4 e 5: infraestrutura e integração

- `pyproject.toml`: pacote `paa_contexto` em layout `src/`, Python `>=3.11`, dependências do `requirements.lock`, `pytest` configurado com `testpaths = ["tests"]`.
- `.github/workflows/ci.yml`: em cada push, instala e roda `pytest`. Sem corpus (a licença impede), então os testes de integração usam só os fixtures.
- `tests/README.md`: tabela caso → entrada → saída esperada → arquivo, reunindo as tabelas acima. É o entregável 10.7 do enunciado.
- `docs/PROTOCOLO_EXPERIMENTAL.md`, uma página: as 45 execuções, os 3 tamanhos, o que se mede, em que máquina, com que semente. Vai para o quadro no dia 10.
- README: tabela de frentes preenchida, comando do `consultar.py` na seção de reprodução.
- Integração: rodar `preparar_corpus.py --capitulos 8`, depois `consultar.py` com três perguntas reais, e conferir a olho que os trechos fazem sentido. Se "o que é recursão" não trouxer o capítulo 5 ou 6 no topo, tem bug em algum lugar.

## Hernandison

### Normalização e fragmentação, até 07/09

`src/paa_contexto/normalizacao.py`

```python
def normalizar_markdown(texto: str) -> str      # NFKC, minúsculas, pontuação separada, espaços compactados, acentos mantidos
def visao_lexical_codigo(fonte: str) -> str     # identificadores e palavras de célula de código, indentação intacta na origem
```

`src/paa_contexto/fragmentacao.py`

```python
@dataclass
class Celula:
    arquivo: str; capitulo: str; secao: str; indice: int; tipo: str; conteudo: str
def extrair_celulas(caminho_notebook: Path) -> list[Celula]
def fragmentar(celulas: list[Celula], tamanho: int = 256, sobreposicao: int = 32) -> list[Chunk]
```

- `extrair_celulas` lê o `.ipynb`, descarta saídas e metadados, acompanha o último título `#`/`##` para preencher `capitulo` e `secao`.
- `fragmentar` nunca mistura célula de texto com célula de código no mesmo chunk. Célula com mais de 256 tokens gera vários chunks com sobreposição de 32. Célula com menos gera um chunk só. `source_order` é global, na ordem dos arquivos e das células.

`scripts/preparar_corpus.py`: lê `data/raw/capitulos/*.ipynb` na ordem `jupyter_intro`, `chap00`, `chap01`...`chap19`, grava `data/processed/chunks.jsonl`, imprime quantos chunks saíram e grava o SHA-256 do arquivo gerado no `corpus_manifest.csv` (a linha "extração" que está como pendente na ficha). Aceita `--tamanho` e `--sobreposicao` para o experimento de sensibilidade da semana 2, e `--capitulos 8` para o checkpoint.

Testes em `tests/unit/test_normalizacao.py` e `tests/unit/test_fragmentacao.py`:

| Caso | Esperado |
|---|---|
| `"Função"` normalizado | `"função"`, acento mantido |
| `"a,b"` | `"a , b"` |
| célula de 700 tokens, 256/32 | 4 chunks; o segundo começa no token 224 |
| célula de 100 tokens | 1 chunk, `n_tokens = 100` |
| célula de código seguida de markdown | dois chunks, nunca um |
| `chunk_id` | únicos em todo o conjunto |
| `source_order` | exatamente 0..n-1 |
| determinismo | rodar `fragmentar` duas vezes dá saída idêntica |

## Dia 10, em sala

Rafael mostra o `consultar.py` com uma pergunta e explica o contador. Hernandison mostra o livro cortado e a contagem de chunks. João mostra o protocolo experimental e a suíte de testes verde. Dois minutos cada. A pergunta que o professor mais provavelmente faz é "por que o tempo de C1 e C3 quase não difere", e a resposta está na contagem de comparações, não no cronômetro.

## O que fica de fora de propósito

C4, qrels, 45 execuções, gráfico, prova escrita, integração do relatório. Tudo isso é semana 2 e tem dono. Se sobrar tempo na semana 1, o melhor uso é revisar o código um do outro e deixar o `tests/README.md` impecável, não adiantar tarefa alheia.
