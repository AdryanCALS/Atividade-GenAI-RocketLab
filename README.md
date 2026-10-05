# CineData Analytics - Agente Text-to-SQL com Guardrails

Agente inteligente Text-to-SQL desenvolvido para responder perguntas de negócio sobre a camada analítica de dados cinematográficos (`cinerocket.db`), utilizando orquestração via LangChain e o modelo `openai/gpt-oss-120b` hospedado na infraestrutura do Groq.

O sistema integra guardrails multicamada determinísticos, rastreabilidade de passos com visualização do SQL executado, janela de memória deslizante e interface interativa via Streamlit.

---

## Estrutura do Projeto

- **`cinedata_agent.py`**: Núcleo do agente. Implementa os guardrails de segurança, as ferramentas LangChain (`describe_tables` e `execute_sql_query` com suporte a `content_and_artifact`), o system prompt instrucional e o loop de execução orientado a eventos (`stream_agent`) com memória dos últimos 3 turnos.
- **`app.py`**: Interface web desenvolvida em Streamlit. Fornece acompanhamento ao vivo de cada passo de execução via `st.status`, rastro de execução recolhível com o SQL executado e tabela de resultados em `st.dataframe`, perguntas sugeridas e tratamento resiliente de falhas.
- **`download_db.py`**: Utilitário para download automatizado, validação de integridade e empacotamento do banco de dados SQLite a partir do GitHub Releases.
- **`tests/`**: Suíte de testes automatizados com Pytest, cobrindo guardrails, rastro de execução, limites de iterações, janela de memória, utilitário de download e renderização de componentes do Streamlit via `AppTest`.

---

## Gestão do Banco de Dados via GitHub Releases

O banco de dados analítico local (`cinerocket.db`) possui aproximadamente 554 MB descompactado, ultrapassando os limites recomendados e as restrições estritas de tamanho por arquivo do Git (máximo de 100 MB).

Para manter o repositório enxuto e reprodutível, adotou-se a distribuição do banco como um ativo anexado aos **Releases do GitHub**:

1. O banco original é compactado em formato zip (`cinerocket.db.zip`, ~251 MB) e hospedado como release asset no GitHub.
2. O utilitário `download_db.py` realiza o download com transferência em blocos (streaming), extrai o arquivo diretamente no diretório `data/` e valida a integridade estrutural do SQLite (`PRAGMA quick_check;`).
3. O download pode ser realizado previamente via terminal ou disparado de forma assistida na própria interface do Streamlit caso o arquivo não seja detectado localmente.

### Opções do Utilitário de Dados

- **Baixar o banco de dados via terminal:**
  ```bash
  python download_db.py
  ```

- **Especificar uma URL customizada de download:**
  ```bash
  python download_db.py --url "https://github.com/AdryanCALS/Atividade-GenAI-RocketLab/releases/download/v1.0.0/cinerocket.db.zip"
  ```

- **Empacotar a base local para publicação de um novo release (mantenedor):**
  ```bash
  python download_db.py --package
  ```

---

## Instalação e Configuração

### 1. Pré-requisitos
- Python 3.12 instalado.
- Chave de API da plataforma Groq (`GROQ_API_KEY`).

### 2. Ambiente Virtual e Dependências
Crie e ative o ambiente virtual e instale os pacotes necessários:

```bash
# Criação do ambiente virtual
python -m venv venv

# Ativação no Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Ativação no Linux/macOS
# source venv/bin/activate

# Instalação das dependências
pip install -r requirements.txt
```

### 3. Configuração de Variáveis de Ambiente
Copie o arquivo de exemplo e insira suas credenciais:

```bash
copy .env.example .env
```

Edite o arquivo `.env`:
```env
GROQ_API_KEY=gsk_sua_chave_aqui

# Opcional: caso deseje apontar para um release específico
# CINEDATA_DB_URL=https://github.com/AdryanCALS/Atividade-GenAI-RocketLab/releases/download/v1.0.0/cinerocket.db.zip
```

---

## Execução

### 1. Inicializar a Interface Web
Para iniciar a aplicação Streamlit:

```bash
streamlit run app.py
```

A interface estará acessível via navegador em `http://localhost:8501`. Caso o banco de dados analítico ainda não esteja presente, a própria tela apresentará a opção de download automatizado.

### 2. Executar a Suíte de Testes
Para rodar todos os testes automatizados com relatório de cobertura:

```bash
pytest
```

---

## Arquitetura e Decisões de Engenharia

- **Defesa em Profundidade nos Guardrails**:
  1. *Camada Léxica e Sintática*: Bloqueio imediato de comandos de mutação (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `PRAGMA`, etc.) e proibição estrita de consultas múltiplas empilhadas (`stacked queries` com `;`).
  2. *Paginação Automática Mandatória*: Injeção determinística de cláusula `LIMIT 100` caso a consulta gerada pelo modelo não declare um limite explícito.
  3. *Camada do Driver SQLite*: Conexão configurada em modo estritamente somente leitura via URI (`mode=ro`) e ativação da diretiva nativa `PRAGMA query_only = ON`.
- **Rastreabilidade e Transparência**: Apresentação explícita de todos os passos intermediários do agente (inspeção de esquemas e SQL executado) em blocos recolhíveis, permitindo auditoria humana dos dados gerados.
- **Eficiência de Contexto via Artifacts**: A ferramenta `execute_sql_query` devolve uma amostra restrita (até 15 registros) no conteúdo textual processado pelo modelo, desacoplando o consumo de tokens da exibição da tabela completa (até 100 registros) renderizada na interface.
- **Janela de Memória Deslizante**: Manutenção do contexto conversacional restrita aos últimos 3 turnos (pergunta e resposta final), prevenindo esgotamento de janela de contexto e consumo desnecessário de quota de requisições.
