# Planejamento da Atividade 1

## O que vamos construir

Um buscador sobre o livro Pense Python. A pessoa digita uma pergunta e o programa devolve os trechos do livro que melhor respondem. Vamos fazer essa busca de três jeitos (C1, C2 e C3), provar que um deles está correto, medir o tempo e a memória de cada um, e escrever um relatório comparando.

A nota se divide assim: código 2,0; prova de corretude 1,5; análise de complexidade 2,0; experimentos 1,5; definição do problema 1,0; discussão sobre IA 1,0; relatório, vídeo e apresentação 1,0.

## Datas do professor

| Data | O que acontece |
| --- | --- |
| 05/09, 23h59 | Reserva do corpus no Classroom (feita) |
| 10/09 | Checkpoint em sala: mostrar o programa rodando e o plano dos experimentos |
| 23/09, 23h59 | Entrega de tudo no GitHub e no Classroom |
| 24/09 | Apresentação |

## Como a divisão foi montada

Cruza a proposta de frentes que Hernandison trouxe no rascunho do relatório (04/09) com o que já estava combinado no repositório. Do rascunho dele ficam João no índice invertido e Hernandison na ingestão e fragmentação. Do combinado anterior ficam Rafael na ordenação, que ele já confirmou, e Nadianne na corretude e análise, que ela pediu no grupo.

Cada pessoa é dona de uma parte do começo ao fim e revisa a parte de outra pessoa. A tabela de contribuição do relatório registra commits, arquivos e execuções, porque é assim que o enunciado pede.

## Fase 1: até 10/09

| Quem | Faz o quê | Por que importa | Prazo |
| --- | --- | --- | --- |
| Rafael | Busca linear, Insertion Sort, Merge Sort e a função que dá nota a cada trecho. Um comando de terminal que recebe a pergunta e mostra os melhores trechos. | É o coração do trabalho. Três dos cinco algoritmos obrigatórios estão aqui. | 10/09 |
| Hernandison | Cortar o livro em trechos: leitura dos notebooks, normalização, fragmentação em 256 tokens e o script que gera o arquivo de chunks. | Todo o resto usa os trechos. É a etapa de ingestão do enunciado. | 10/09 |
| João | Os trechos falsos de teste com gabarito (dia 1, para o Rafael começar), o pacote Python, os testes automáticos, o plano dos experimentos em uma página e o índice invertido com busca binária (C2). | Sem os trechos falsos ninguém testa antes de o livro estar cortado. O plano dos experimentos é o que o professor pede no checkpoint. | 10/09 |

No dia 10, em sala: Rafael mostra uma pergunta entrando e os trechos saindo. Hernandison mostra o livro cortado em trechos. João mostra o plano dos experimentos e os testes passando.

Se a fragmentação real não estiver pronta a tempo do checkpoint, João assume essa parte, e Hernandison segue com o relatório na fase 2. O prazo interno para essa decisão está em `docs/SEMANA1.md`.

## Fase 2: até 23/09, todos

| Quem | Faz o quê | Por que importa | Precisa de | Prazo |
| --- | --- | --- | --- | --- |
| Nadianne | Prova de que o Merge Sort está correto, análise no modelo RAM, melhor/pior/médio e recorrências. Revisa e completa as seções 7 a 10 do rascunho do relatório sobre o código real do Rafael. | 3,5 pontos da nota. | Código do Rafael | 23/09 |
| Eduardo | Rodar os experimentos (45 execuções), medir tempo, memória e comparações, fazer as tabelas e o gráfico, e a comparação com a biblioteca scikit-learn (C4). | 1,5 da nota. Sem tabela e gráfico o professor não conta como experimento. | C1, C2, C3 rodando e o gabarito da Helena | 23/09 |
| Helena | Escrever as 30 perguntas de teste, marcar quais trechos respondem cada uma (gabarito, com um segundo avaliador), calcular Precision@k, e cuidar das seções sobre IA generativa e limitações. | Sem gabarito não dá para medir se o buscador acerta. A seção sobre IA vale 1,0. | Trechos do livro | 23/09 |
| Hernandison | Manter o rascunho do relatório: incorporar as seções dos outros, alinhar numeração e fórmula com `docs/CONTRATOS.md`, exportar o PDF final. | O rascunho é dele e é o entregável principal. | Seções de todos | 23/09 |
| Rafael | Revisar a prova da Nadianne contra o próprio código. | O professor confere se a prova bate com o código. | Prova da Nadianne | 23/09 |
| João | Testar em máquina limpa, publicar a versão final com tag, conferir links, organizar o vídeo. | Reprodução e vídeo são entregáveis. | Tudo pronto | 23/09 |

## Ordem em que as coisas precisam existir

```
trechos falsos (João, dia 1) ── ordenação e nota (Rafael) ──┐
trechos reais (Hernandison) ── índice (João) ────────────────┼── experimentos e C4 (Eduardo)
perguntas e gabarito (Helena) ───────────────────────────────┘
prova e análise (Nadianne, em paralelo, sobre o código do Rafael)
relatório (Hernandison junta; João fecha a entrega)
```

## O que todo mundo faz

- Aparece no vídeo de até 10 minutos explicando a própria parte.
- Registra os próprios usos de IA em `docs/USO_DE_IA.md` no dia em que usar.
- Preenche a própria linha em `docs/CONTRIBUICOES.md` com commits e arquivos.
- Apresenta a própria parte em 24/09.
- Antes de programar, lê `docs/CONTRATOS.md`: formato dos trechos, regra de desempate, formato dos arquivos.

## Onde está o detalhe

- `docs/CONTRATOS.md`: as regras técnicas que todos seguem, inclusive a numeração das configurações e a fórmula da nota, que o rascunho do relatório precisa seguir.
- `docs/SEMANA1.md`: a lista de arquivos e testes da fase 1.
- `relatorio/`: o rascunho do relatório trazido por Hernandison, base do documento final.
