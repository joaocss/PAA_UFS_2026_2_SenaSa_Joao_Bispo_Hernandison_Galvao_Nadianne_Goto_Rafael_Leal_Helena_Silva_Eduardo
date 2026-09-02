# Ficha do corpus

## Identificação

| Campo | Registro |
| --- | --- |
| Nome | Pense Python, tradução livre da 3ª edição |
| Autor | Allen B. Downey |
| Tradução | Rodrigo Castelan Carlson |
| Fonte | https://rodrigocarlson.github.io/PensePython3ed/ e https://github.com/rodrigocarlson/PensePython3ed |
| Commit de referência | cfde2c450bf4f2ea65326da88e9968f400597e92 (branch main) |
| Data de acesso | 01/09/2026, a reconfirmar no dia da aquisição |
| Formato | 21 notebooks Jupyter: prefácio, introdução e capítulos 1 a 19 |
| Tamanho auditado | 817.578 bytes, 2.789 células, 73.867 palavras de texto e código na extração canônica |
| SHA-256 do recorte bruto | 20106262588b9041517ab675fccee3034d879f08b381b584cdd99f40a5768dc5 |
| SHA-256 da extração | pendente, será gravado por `preparar_corpus.py` |
| Idioma | Português brasileiro |
| Licença do texto | CC BY-NC-SA 4.0 |
| Licença dos códigos | MIT |
| Dados sensíveis | Nenhum. Conteúdo didático público |

O recorte são os 21 notebooks de `capitulos/*.ipynb`, no commit acima. As pastas `brancos` e `solucoes` do repositório de origem ficam de fora: uma repete o texto sem as respostas, a outra traz gabaritos. A subpasta `capitulos/teste` também não entra.

O hash do recorte é calculado assim: para cada arquivo, concatena-se o caminho relativo e o SHA-256 do conteúdo; a lista é ordenada alfabeticamente, unida por quebras de linha, e o SHA-256 dessa string é o valor registrado. A ordem de leitura não influencia o resultado, e qualquer arquivo que entre, saia ou mude altera o hash.

O valor acima foi produzido por `scripts/baixar_corpus.py` em 02/09/2026. O total de 817.578 bytes confere com o levantamento de planejamento, o que confirma que o recorte é o mesmo. Divergência em execuções futuras significa que o material mudou na origem e precisa ser investigada antes de qualquer experimento.

## Por que o texto não está versionado aqui

A licença do texto é não comercial e com compartilhamento pelas mesmas condições. Redistribuir o material dentro deste repositório criaria uma obrigação de licenciamento que não se aplica ao código da equipe, que é MIT. A solução é não versionar o texto: `scripts/baixar_corpus.py` baixa o material no commit fixado e `corpus_manifest.csv` permite conferir que o download reproduz o mesmo recorte auditado. Trechos citados no relatório preservam atribuição a autor e tradutor.

## Limpeza e segmentação

A normalização é deliberadamente simples, para poder ser auditada. Células Markdown passam por NFKC, minúsculas, separação controlada de pontuação e compactação de espaços, com acentos preservados. Células de código guardam a fonte intacta e ganham uma visão lexical à parte, sem alteração de indentação. Stopwords não são removidas na configuração principal, porque em português isso apaga termos funcionais que importam para a consulta.

A segmentação respeita notebook, título e seção, e nunca mistura célula de texto com célula de código. A configuração principal usa 256 tokens com sobreposição de 32, o que rende algo em torno de 330 chunks. As configurações de 128/16 e 512/64 entram apenas no experimento de sensibilidade.

## Riscos conhecidos

A tradução ainda carrega termos em inglês vindos do Python e do Jupyter, o que afeta consultas com e sem estrangeirismos. Um único livro introdutório não representa o universo dos materiais educacionais abertos em português, de modo que os resultados valem como estudo de caso. Saídas de célula são descartadas para não introduzir texto derivado de execução.

## Arquivos deste diretório

- `corpus_manifest.csv`: um registro por arquivo baixado, com URL, tamanho, SHA-256 e data de acesso, mais o hash agregado do recorte.
- `queries.csv`: as 30 consultas, escritas antes de qualquer resultado ser observado.
- `qrels.csv`: julgamentos de relevância em escala 0, 1 e 2, com dois avaliadores independentes e a adjudicação registrada.
