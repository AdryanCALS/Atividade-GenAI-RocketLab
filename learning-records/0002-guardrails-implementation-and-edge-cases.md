# Implementação dos Guardrails e Descoberta de Falso Positivo em Literais de Texto

O estudante implementou com sucesso a tríade de guardrails em código (rejeição de comandos não-SELECT, bloqueio de comandos encadeados com ponto-e-vírgula, injeção de LIMIT e conexão read-only com PRAGMA). O teste automatizado revelou um desafio clássico de parsers léxicos: palavras-chave proibidas (como `UPDATE` ou `DROP`) contidas dentro de literais de string (ex: `WHERE titulo LIKE '%update%'`) acionam falsos positivos se as aspas não forem isoladas antes da análise de tokens.

## Evidence
- O código escrito pelo estudante em `main.ipynb` bloqueou com precisão ataques de `DROP TABLE`, ataques de SQL injection encadeado (`SELECT ...; DELETE ...`) e executou com sucesso queries analíticas complexas com agregação e CTE (`WITH`).
- O teste de borda com `WHERE titulo LIKE '%update%'` identificou a necessidade de desconsiderar o conteúdo de strings entre aspas simples ao escanear palavras banidas.

## Implications
- Refinar a validação com um pré-processamento leve que remove literais de string (`'...'`) antes de buscar palavras-chave proibidas, consolidando a robustez do guardrail antes de integrá-lo como Tool do LangChain.
