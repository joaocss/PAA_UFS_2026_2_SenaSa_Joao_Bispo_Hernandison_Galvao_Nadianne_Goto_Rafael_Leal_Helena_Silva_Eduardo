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
| SHA-256 do recorte bruto | 86e71e127f4e0e557333bcd1d469162c2ad9b613c0708830ba570ff57cf8b34c |
| SHA-256 da extração | b0354898a9e6c58231c4f11014521c6c888afcf433a9495253011d6c9b8513fa |
| Idioma | Português brasileiro |
| Licença do texto | CC BY-NC-SA 4.0 |
| Licença dos códigos | MIT |
| Dados sensíveis | Nenhum. Conteúdo didático público |

Os hashes acima vieram da auditoria de planejamento. O script de aquisição recalcula e grava os valores efetivos em `corpus_manifest.csv`; divergência entre os dois é sinal de que o material mudou na origem e precisa ser investigada antes de qualquer execução.

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
