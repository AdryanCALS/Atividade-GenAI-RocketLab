# Arquitetura de Tool Calling e Orquestração do Agente CineData

Definição e validação do fluxo ReAct de duas etapas (inspeção de esquema via `describe_tables` e execução de queries seguras via `execute_sql_query`) com o modelo `openai/gpt-oss-120b` orquestrado pelo LangChain.

## Evidence
- O modelo executou em 10 segundos o ciclo completo de schema linking sob demanda seguido da execução com guardrails e síntese de resposta executiva em português para contagem de registros na camada Gold.

## Implications
- A separação entre inspeção de esquema e execução impede alucinações de colunas e economiza tokens de contexto.
- O aluno implementará esse loop manualmente no notebook com lacunas conceituais guiadas.
