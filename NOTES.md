# Working Notes & User Preferences

## User Preferences
- **Abordagem de ensino**: O usuário declarou explicitamente que **não quer vibecodar**. Quer entender a fundo a lógica, a arquitetura, os conceitos teóricos e cada linha de código implementada.
- **Orquestrador**: LangChain (usando padrões modernos de Tool Calling e gerenciamento de estado/mensagens).
- **Provedor / LLM**: Groq utilizando o modelo open-source de ponta `openai/gpt-oss-120b`.
- **Foco de valor**: Guardrails robustos (prevenção de SQL injection, bloqueio de comandos perigosos, limite de linhas, integridade de esquema).
- **Ambiente de Trabalho**: Windows, PowerShell, VS Code / Jupyter Notebook, Python 3.12 em virtualenv.

## Contexto da Atividade
- **Curso/Programa**: Visagio RocketLab 2026 - Atividade GenAI CineData Analytics.
- **Data limite de entrega**: 05/10/2026 às 18:00.
- **Entregável**: Notebook / Projeto Python versionado com README explicativo.
- **Banco de dados local**: SQLite `data/cinerocket.db` com ~581MB e 10 tabelas em modelo dimensional (fato, dimensões e tabelas bridge).

## Decisões Técnicas Alinhadas
1. **LangChain Moderno**: Usar `langchain_core` e `langchain_groq` com ferramentas decoradas (`@tool`) e fluxo de Tool Calling, que é o padrão recomendado e mais transparente.
2. **Defesa em Profundidade para Guardrails**:
   - Camada 1: Validação léxica/regex + AST (Abstract Syntax Tree) do SQL gerado (rejeição de qualquer token não-SELECT).
   - Camada 2: Injeção forçada de `LIMIT` e proibição de transações múltiplas.
   - Camada 3: Conexão SQLite em modo estritamente read-only (`file:...?mode=ro` e `PRAGMA query_only = ON`).
3. **Tratamento de Esquema (Schema Linking)**:
   - Não entupir o prompt com todo o schema de 10 tabelas e 700k linhas.
   - Fornecer ferramenta de inspeção sob demanda e recuperação de valores distintos para colunas categóricas (como ensinado no paper CHESS).
