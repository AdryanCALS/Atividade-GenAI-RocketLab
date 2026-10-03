# Baseline: Conhecimento Prévio de GenAI e Definição do Stack

O estudante já teve contato teórico com o paradigma Text-to-SQL (conceitos do CHESS e CHASE-SQL em aulas anteriores) e realizou o setup inicial de conexão com o modelo `openai/gpt-oss-120b` via Groq. Seu objetivo central é transicionar da teoria para uma implementação prática e segura utilizando LangChain com guardrails determinísticos, rejeitando expressamente atalhos de "vibecoding" em favor da compreensão profunda dos mecanismos de agentes.

## Evidence
- O usuário possui em seu repositório os notebooks das aulas de apoio (`text_to_sql_workshop.ipynb` e `Criacao_de_Comunicacao_com_LLM.ipynb`).
- Testou com sucesso no `main.ipynb` a chamada bruta ao endpoint da Groq com `openai/gpt-oss-120b`.
- Especificou no prompt que deseja entender os conceitos, o código e implementar guardrails robustos no contexto do banco do CineData.

## Implications
- As aulas futuras devem focar no "porquê" de cada componente do LangChain (Tool Calling, `AIMessage.tool_calls`, `ToolMessage`, loop de execução) e na arquitetura de segurança multicamadas para SQL.
- Não partiremos do zero absoluto em LLMs (o estudante já conhece tokens e APIs), mas partiremos do zero no desenho arquitetural do agente Text-to-SQL em LangChain e na engenharia de guardrails defensivos.
