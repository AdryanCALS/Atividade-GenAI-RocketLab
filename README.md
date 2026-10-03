# CineData Analytics - Agente Text-to-SQL com Guardrails

Agente inteligente Text-to-SQL seguro para responder perguntas de negócio sobre a camada analítica de dados de filmes (`cinerocket.db`), utilizando orquestração via LangChain e o modelo `openai/gpt-oss-120b` hospedado no Groq.

O projeto inclui:
- **Módulo Central (`cinedata_agent.py`)**: guardrails determinísticos multicamada (regex/AST, injeção forçada de `LIMIT`, modo estritamente somente leitura com SQLite `PRAGMA query_only = ON` e URI `mode=ro`), ferramentas LangChain (`describe_tables`, `execute_sql_query` com suporte a `content_and_artifact`) e loop de agente orientado a eventos (`stream_agent`) com Janela de Memória (últimos 3 turnos).
- **Interface Web Interativa (`app.py`)**: interface moderna e intuitiva em Streamlit com exibição ao vivo de cada Passo em `st.status`, Rastro de Execução recolhível com o SQL executado e tabela de resultados em `st.dataframe`, perguntas sugeridas e isolamento de falhas.
- **Notebook de Desenvolvimento e Avaliação (`main.ipynb`)**: documentação passo a passo do fluxo, testes das 5 categorias analíticas da atividade e integração com o módulo central.
- **Suíte de Testes Automatizados (`tests/`)**: testes unitários e de integração cobrindo guardrails, Rastro de Execução, limites de passos, Janela de Memória, tratamento de falhas e renderização do Streamlit via `AppTest`.

---

## 🚀 Como Executar

### 1. Pré-requisitos e Instalação

Certifique-se de ter o Python 3.12 instalado. Crie e ative o ambiente virtual, em seguida instale as dependências:

```bash
# Criar ambiente virtual (caso ainda não possua)
python -m venv venv

# Ativar no Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar a Chave de API

Copie o arquivo de exemplo de variáveis de ambiente e configure sua chave do Groq:

```bash
copy .env.example .env
```

Edite o arquivo `.env` inserindo sua chave:
```env
GROQ_API_KEY=gsk_sua_chave_aqui
```

### 3. Executar a Interface Web (Streamlit)

Para iniciar o chat localmente:

```bash
streamlit run app.py
```

A interface estará disponível em seu navegador (geralmente em `http://localhost:8501`).

### 4. Executar os Testes Automatizados

Para rodar a suíte completa de testes:

```bash
pytest
```

---

## 🏛️ Arquitetura e Decisões Técnicas

- **Defesa em Profundidade nos Guardrails**:
  1. *Léxica/Sintaxe*: Bloqueio imediato de palavras proibidas (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, etc.) e proibição de consultas múltiplas (stacked queries com `;`).
  2. *Paginação Automática*: Injeção mandatória de `LIMIT 100` caso a LLM não especifique limites.
  3. *Camada do Driver*: Conexão SQLite estritamente `mode=ro` e ativação da diretiva nativa `PRAGMA query_only = ON`.
- **Rastro de Execução Transparente**: O usuário acompanha os passos de inspeção de esquema e execução do SQL real em tempo real.
- **Eficiência de Tokens via Artifacts**: A ferramenta `execute_sql_query` devolve uma amostra enxuta (até 15 registros) no conteúdo para o modelo de linguagem, mantendo o resultado tabular completo (até 100 linhas) no artefato exibido na interface visual.
- **Janela de Memória Enxuta**: Manutenção de contexto conversacional focada apenas nos últimos 3 turnos (pergunta e resposta final), prevenindo estouro de limites de contexto e consumo excessivo de taxa de requisições.
