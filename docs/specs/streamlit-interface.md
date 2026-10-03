# Spec: Interface Streamlit para o agente Text-to-SQL do CineData

Decisões acordadas na sessão de grilling de 03/10/2026. Vocabulário em [GLOSSARY.md](../../GLOSSARY.md).

## Objetivo
Interface leve e intuitiva para o usuário conversar com o agente Text-to-SQL hoje implementado em `main.ipynb`.

## Requisitos

1. **Stack**: Streamlit, execução apenas local (`streamlit run app.py`), documentada no README.
2. **Módulo único do agente**: guardrails, tools, system prompt e loop saem do notebook para `cinedata_agent.py` (raiz). `app.py` (raiz) e o notebook importam desse módulo.
3. **Notebook**: as células de código de guardrails/tools/loop são substituídas por imports do módulo; as células markdown explicativas permanecem; as perguntas de teste da atividade continuam rodando via módulo.
4. **Janela de Memória**: cada nova pergunta é enviada ao modelo junto com os últimos 3 Turnos (pergunta + resposta final, sem ToolMessages).
5. **Rastro de Execução visível**: cada resposta mostra a resposta final e um bloco recolhível com os Passos (tool chamada, argumentos, SQL efetivamente executado e tabela com as linhas).
6. **Artifact**: `execute_sql_query` usa `response_format="content_and_artifact"`: o modelo recebe o texto curto (máx. 15 linhas) e a interface recebe o resultado completo (SQL executado + linhas).
7. **Passos ao vivo**: o loop do agente é um gerador que emite cada Passo assim que ocorre, exibido dentro de `st.status`. O notebook usa um wrapper que consome o gerador e devolve só a resposta.
8. **Perguntas sugeridas**: com o chat vazio, botões com 1 pergunta de cada categoria de teste (finanças, popularidade, elenco, gêneros, avaliações).
9. **Falhas tratadas com mensagem amigável, sem derrubar a sessão**:
   - `GROQ_API_KEY` ausente → aviso na tela e input desabilitado;
   - limite de requisições (429) / falha de rede do Groq → "tente novamente em alguns segundos";
   - `max_steps` atingido → mensagem atual + Rastro de Execução.
   Turnos que falham **não entram** na Janela de Memória.
10. **Controles**: apenas o botão "Nova conversa" na sidebar (limpa histórico e Janela de Memória).
11. **Dependências**: `requirements.txt` com streamlit e pandas; `langchain-ollama` removido.

## Fora de escopo (por ora)
- Melhorias nos guardrails (`describe_tables` read-only e validação de nome de tabela) — adiadas por decisão explícita.
- Deploy em nuvem, seletor de modelo/temperatura/`max_steps`.
