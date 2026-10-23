# Recuperação e seleção de contexto para IA generativa em materiais educacionais abertos

Projeto da disciplina **Projeto e Análise de Algoritmos (PAA)**, do **Programa de Pós-Graduação em Ciência da Computação (PROCC/UFS)**, período **2026.2**.

**Tema 8:** materiais educacionais abertos.

O projeto investiga duas etapas complementares de um pipeline de recuperação de contexto: **recuperação e ordenação de trechos relevantes (AV1)** e **seleção de um subconjunto sob orçamento limitado (AV2)**. O material utilizado é o livro aberto *Pense Python*.

> **Estado da AV2 (23/10/2026):** Parte A — especificação do problema elaborada. Implementação, testes e experimentos específicos da AV2 ainda em desenvolvimento. Os comandos de reprodução documentados abaixo pertencem à AV1, até que os novos comandos sejam implementados e validados.

## Atividades

### AV2 — Seleção de contexto com programação dinâmica

A AV2 acrescenta uma etapa de escolha de chunks após a recuperação lexical. O problema é modelado como **mochila 0/1**, com:

- **Algoritmo principal:** programação dinâmica para maximizar a relevância acumulada dentro do orçamento.
- **Linha de base:** seleção gulosa por razão entre relevância e custo (`score_relevancia / n_tokens`).
- **Recuperação fixa:** configuração **C3** da AV1 (busca linear + Merge Sort).
- **Valor de cada candidato (`v_i`):** score lexical TF-IDF calculado para a consulta.
- **Custo de cada candidato (`w_i`):** valor de `n_tokens` registrado na AV1, usado como aproximação do custo de contexto em **unidades lexicais**, não como tokenização exata de um LLM.
- **Restrição:** a soma dos custos dos chunks selecionados não pode ultrapassar o orçamento `W`.

O objetivo formal é:

\[
\max \sum_{i=1}^{n} v_i x_i
\quad \text{sujeito a} \quad
\sum_{i=1}^{n} w_i x_i \le W,
\quad x_i \in \{0,1\}.
\]

A programação dinâmica deve encontrar uma solução ótima **para essa função objetivo aditiva**. Isso não implica, por si só, maior diversidade semântica nem melhor resposta de um modelo de linguagem.

### AV1 — Recuperação lexical de contexto

Na AV1, o protótipo recebe uma consulta em português, processa o livro e devolve trechos ranqueados por relevância lexical. Foram comparadas:

- **C1:** busca linear + Insertion Sort (baseline da AV1).
- **C2:** índice invertido + busca binária + Merge Sort.
- **C3:** busca linear + Merge Sort.
- **C4:** referência externa baseada no TF-IDF do scikit-learn, analisada separadamente.

A AV2 reutiliza o corpus, as consultas e a pontuação lexical da AV1; não substitui nem apaga seus resultados.

## Equipe

### Responsabilidades previstas na AV2

| Integrante | Partes da AV2 |
| --- | --- |
| João Cosme Sena Sá | B — Algoritmos e corretude; D — Experimentos |
| Eduardo Henrique do Lago Silva | B — Algoritmos e corretude; C — Complexidade; D — Experimentos |
| Helena Carvalho Leal | D — Experimentos; E — Relação com IA generativa |
| Hernandison da Silva Bispo | A — Especificação do problema; E — Relação com IA generativa |
| Nadianne Maria dos Santos Galvão | A — Especificação do problema; C — Complexidade |
| Rafael Takeguma Goto | B — Algoritmos e corretude; E — Relação com IA generativa |

### Frentes da AV1 (registro histórico)

| Integrante | Frente principal |
| --- | --- |
| João Cosme Sena Sá | Dados de teste, pacote e testes, protocolo experimental, índice invertido e busca binária (C2), entrega |
| Eduardo Henrique do Lago Silva | Experimentos, tabelas, gráficos e baseline de referência (C4) |
| Helena Carvalho Leal | Consultas, julgamentos de relevância, métricas, relação com IA generativa e limitações |
| Hernandison da Silva Bispo | Ingestão, normalização e fragmentação; manutenção do relatório |
| Nadianne Maria dos Santos Galvão | Corretude, modelo RAM, complexidade e recorrências |
| Rafael Takeguma Goto | Busca linear, Insertion Sort, Merge Sort, pontuação e consulta (C1 e C3) |

As evidências de contribuições da AV1 estão em [`docs/CONTRIBUICOES.md`](docs/CONTRIBUICOES.md). As contribuições da AV2 serão registradas no mesmo histórico ou em uma seção específica desse documento.

## Vídeos das atividades

### AV2

Apresentação e vídeo da AV2 **ainda não disponibilizados**.

### AV1

Gravações individuais:

- **João Cosme Sena Sá:** https://www.loom.com/share/aab4b4cd6a934bb892fd6c4bb73bcd85
- **Helena Carvalho Leal:** https://drive.google.com/file/d/1mrltLobY4q7kejFFrKunLzwvc68bTs38/view?usp=drive_link
- **Nadianne Maria dos Santos Galvão:** https://drive.google.com/file/d/1WWhyEl1k9qLuE8Sod03WE9qJ3bNDWx3Y/view?usp=drive_link
- **Rafael Takeguma Goto:** https://drive.google.com/file/d/13jiWmtcPA6ZGqowYDyxqEHd5966waPa8/view?usp=sharing

Mais informações em [`VIDEO.md`](VIDEO.md).

## Corpus

O corpus é o livro **Pense Python**, tradução livre da 3ª edição de *Think Python*, de **Allen B. Downey**, realizada por **Rodrigo Castelan Carlson**.

- **Livro:** https://rodrigocarlson.github.io/PensePython3ed/
- **Repositório de origem:** https://github.com/rodrigocarlson/PensePython3ed
- **Licenças do material de origem:** texto sob CC BY-NC-SA 4.0; códigos sob MIT.

O texto original não é versionado neste repositório. A aquisição utiliza um commit fixado e um manifesto de hashes para conferir a reprodução do recorte; consulte [`data/README.md`](data/README.md).

### Corpus processado na AV1

| Característica | Quantidade |
| --- | ---: |
| Notebooks | 21 |
| Chunks | 2.737 |
| Chunks Markdown | 1.405 |
| Chunks de código | 1.332 |

O corpus processado é gerado em `data/processed/chunks.jsonl`. Entre seus campos estão `chunk_id`, `source_order`, `texto`, `tipo`, `arquivo`, `capitulo`, `secao`, `celula_idx`, `token_inicio`, `token_fim` e `n_tokens`.

### Reutilização na AV2

Para cada uma das consultas, a configuração C3 recuperará candidatos de relevância positiva e os ordenará por score decrescente, com desempate por `source_order` crescente.

Na etapa de seleção, cada candidato terá, no mínimo:

| Atributo | Significado |
| --- | --- |
| `chunk_id` | Identificador do chunk |
| `texto` | Conteúdo do chunk |
| `source_order` | Ordem de origem no corpus |
| `score_relevancia` | Score calculado para a consulta (atributo derivado; **não** armazenado originalmente em `chunks.jsonl`) |
| `n_tokens` | Custo lexical reaproveitado da AV1 |

O conjunto candidato é específico de cada consulta. A programação dinâmica e a linha de base gulosa receberão **os mesmos itens, scores, custos e orçamento**.

## Funcionamento do pipeline

### Pipeline implementado na AV1

1. Aquisição do corpus em versão fixada.
2. Extração, normalização e fragmentação dos notebooks em chunks.
3. Pontuação lexical TF-IDF em relação à consulta.
4. Recuperação e ordenação dos candidatos conforme C1, C2 ou C3.
5. Exibição dos trechos mais relevantes.

A ordenação dos resultados usa o critério `(-score, source_order)`. Os detalhes de formato, pontuação e desempate estão em [`docs/CONTRATOS.md`](docs/CONTRATOS.md).

### Extensão planejada para a AV2

```text
Consulta
   ↓
Corpus processado na AV1
   ↓
Recuperação C3 (busca linear + Merge Sort)
   ↓
Candidatos: id, texto, relevância, custo, source_order
   ↓
Seleção sob orçamento W
   ├── Programação dinâmica (mochila 0/1)
   └── Guloso (relevância / custo)
   ↓
Subconjunto selecionado + relevância total + custo total
   ↓
Avaliação comparativa
```

A estratégia gulosa considera os chunks em ordem decrescente de `v_i/w_i`, incluindo um item apenas se couber no orçamento restante. Em empates de razão, prefere maior relevância absoluta e depois menor `source_order`.

Na programação dinâmica, entre soluções com relevância máxima igual, o critério previsto é: **menor custo total** e, persistindo o empate, **menor sequência lexicográfica dos `source_order` selecionados e ordenados crescentemente**.

Essas regras são **especificações para implementação e teste**, não resultados já medidos.

## Planejamento experimental da AV2

Os parâmetros abaixo são preliminares e serão confirmados antes da execução dos experimentos.

| Parâmetro | Valor previsto |
| --- | --- |
| Consultas | 30 consultas de `data/queries.csv`, reutilizadas da AV1 |
| Quantidade de candidatos | 10, 30 e 50, quando houver suficientes com score positivo |
| Orçamentos `W` | 256, 512 e 1.024 unidades lexicais |
| Repetições | Mínimo de 3 por cenário |
| Comparação | Programação dinâmica versus guloso, sob entradas idênticas |
| Qualidade da seleção | Relevância acumulada, custo utilizado, utilização do orçamento, diferença de relevância, redundância |
| Custo computacional | Tempo de seleção, tempo total do fluxo e memória aproximada |

**Observação:** a relevância acumulada é a soma dos scores lexicais dos chunks escolhidos. Ela não constitui avaliação automática da qualidade de respostas geradas por LLM.

## Requisitos

A implementação da AV1 utiliza **Python 3.11 ou superior**. As dependências são registradas em `requirements.lock`.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

A suíte de testes existente pode ser executada com:

```bash
pytest
```

Os testes da AV1 utilizam dados sintéticos de `tests/fixtures/` e não exigem o download do corpus para os casos cobertos por essas fixtures.

## Reprodução da AV1

> **Atenção:** os comandos desta seção executam as funcionalidades **já existentes da AV1**. A interface de execução específica da AV2 será documentada após sua implementação.

Para reproduzir o fluxo da AV1, da aquisição aos gráficos:

```bash
python scripts/reproduzir_tudo.py
```

Os estágios podem ser executados separadamente:

```bash
python scripts/baixar_corpus.py
python scripts/preparar_corpus.py
python scripts/rodar_experimentos.py
python scripts/gerar_figuras.py
python scripts/medir_ingestao.py
```

Para consultar o corpus após sua preparação:

```bash
python scripts/consultar.py --consulta "o que é recursão" --k 5 --config C3
```

O arquivo `data/perguntas_30_com_chunks_justificativas.csv` contém os julgamentos utilizados como base para o gabarito humano. A ferramenta `scripts/montar_qrels.py` permite importar, preparar ou consolidar julgamentos no arquivo `data/qrels.csv`.

O protocolo original de avaliação está em [`docs/PROTOCOLO_EXPERIMENTAL.md`](docs/PROTOCOLO_EXPERIMENTAL.md).

## Estrutura do repositório

```text
src/paa_context/       Código do pipeline lexical da AV1
scripts/               Aquisição, processamento, consulta e experimentos da AV1
tests/                 Testes unitários, de integração e fixtures
data/                  Manifesto, consultas e dados processados gerados
experimentos/          Registros, tabelas, gráficos e logs
relatorio/             Fontes e entregas do relatório
slides/                Materiais de apresentação
docs/                  Contratos, corretude, resultados e contribuições
```

**Documentos previstos para a AV2** (adicionar os links apenas depois de criar os arquivos):

- `docs/ESPECIFICACAO_AV2.md` — conteúdo da Parte A.
- `docs/CONTRATOS_AV2.md` — formatos de entrada/saída, interfaces e decisões de implementação.
- `docs/PLANEJAMENTO_AV2.md` — responsabilidades e prazos da AV2.

Os documentos `docs/PLANEJAMENTO.md`, `docs/CONTRATOS.md` e `docs/SEMANA1.md` continuam como registros da AV1 e **não devem ser sobrescritos**.

## Licença

O código deste repositório é distribuído sob a licença **MIT**, conforme o arquivo [`LICENSE`](LICENSE). As condições do corpus original são distintas e estão descritas em [`data/README.md`](data/README.md). Qualquer trecho reproduzido do livro deve preservar a atribuição ao autor e ao tradutor e observar a licença correspondente.

## Documentação relacionada

### AV1

- [`docs/CONTRATOS.md`](docs/CONTRATOS.md) — contratos técnicos da recuperação e ordenação.
- [`docs/PLANEJAMENTO.md`](docs/PLANEJAMENTO.md) — planejamento histórico da AV1.
- [`docs/SEMANA1.md`](docs/SEMANA1.md) — registro do primeiro checkpoint.
- [`docs/CORRETUDE.md`](docs/CORRETUDE.md) — argumento de corretude do Merge Sort.
- [`docs/CONTRIBUICOES.md`](docs/CONTRIBUICOES.md) — contribuições e evidências.
- [`docs/USO_DE_IA.md`](docs/USO_DE_IA.md) — declaração de utilização de ferramentas de IA.

### AV2

A especificação da Parte A e os contratos específicos da AV2 serão adicionados à branch `av2-programacao-dinamica` e vinculados aqui quando estiverem versionados.
