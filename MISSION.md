# Mission: Agente Text-to-SQL Seguro para CineData Analytics com LangChain e Groq

## Why
Capacitar o estudante a projetar, implementar e depurar com domínio conceitual e técnico um agente Text-to-SQL seguro, com guardrails determinísticos e orquestração via LangChain, conectando consultas em linguagem natural à camada Gold do CineData Analytics (`cinerocket.db`) utilizando o modelo open-source `openai/gpt-oss-120b` hospedado no Groq, eliminando a dependência de "vibecoding".

## Success looks like
- O estudante compreende e domina os 4 passos do ciclo Text-to-SQL: Schema Linking seletivo, geração de SQL com contexto restrito, validação com Guardrails determinísticos (AST/read-only) e auto-correção em caso de erro de execução.
- Construção de ferramentas customizadas no LangChain (`inspect_tables`, `get_sample_values`, `execute_safe_sql`).
- Implementação de guardrails multicamada ativos que impedem qualquer operação destrutiva (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `ATTACH`), forçam limites de paginação (`LIMIT`) e validam sintaxe antes da execução no banco.
- O agente responde com precisão às principais classes de perguntas do CineData: finanças (faturamento/lucro/margem), popularidade/avaliações (TMDB vs IMDb) e junções complexas com tabelas bridge (atores, diretores, produtoras).
- Entrega de código modular, legível e versionável acompanhado de documentação clara e testes de execução.

## Constraints
- **Stack Tecnológico**: Python 3.12, LangChain (`langchain-core`, `langchain-groq`), modelo `openai/gpt-oss-120b` via Groq.
- **Base de Dados**: SQLite local `cinerocket.db` contendo 10 tabelas relacionais em estrela/floco de neve.
- **Tempo/Prazo**: Entrega da atividade Visagio RocketLab até 05/10/2026 às 18:00.
- **Economia de Tokens**: Planejamento cuidadoso de chamadas de LLM para evitar estourar limites de requisições por minuto do provedor.
- **Abordagem Pedagógica**: Construção incremental com desafios conceituais, verificação ativa de aprendizado e código explicado linha a linha.

## Out of scope
- Fine-tuning ou treinamento supervisionado de pesos de LLM.
- Construção de interfaces gráficas completas de chat (React, Next.js, etc.).
- Conexões de nuvem pagas ou migração para Databricks/Snowflake antes de validar 100% no SQLite local.
