"""
Agente Text-to-SQL do CineData Analytics.

Módulo único usado pelo notebook (`main.ipynb`) e pela interface (`app.py`).
Contém, nesta ordem: guardrails, tools, system prompt e o loop do agente.
"""

import json
import os
import re
import sqlite3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union

import groq
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq

DB_PATH = str(Path(__file__).resolve().parent / "data" / "cinerocket.db")


# =============================================================================
# Guardrails
# =============================================================================

BANNED_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
                   "CREATE", "ATTACH", "DETACH", "PRAGMA", "REPLACE", "TRUNCATE"]


def validade_query(query: str) -> Tuple[bool, str]:
    """
    Valida se a query digitada pelo usuario é segura e somente de leitura.
    Retorna (True, "OK") ou (False, "Motivo de bloqueio").
    """
    cleaned_query = query.strip()

    if cleaned_query.endswith(";"):
        cleaned_query = cleaned_query[:-1].strip()

    if ";" in cleaned_query:
        return False, "Consultas Múltiplas não são permitidas"

    query_upper = cleaned_query.upper()
    query_sem_strings = re.sub(r"'(?:''|[^'])*'", "''", query_upper)

    if ";" in query_sem_strings:
        return False, "Consultas Múltiplas não são permitidas"

    if not (query_upper.startswith("WITH") or query_upper.startswith("SELECT")):
        return False, "A consulta deve obrigatoriamente ser um SELECT ou WITH."

    for keyword in BANNED_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, query_upper):
            return False, f"Comando proibido {keyword} detectado."

    return True, "OK"


def enforce_query_limits(query: str, default_limit: int = 100) -> str:
    """
    Inpeciona a Query e injeta um limit caso o da LLM não tenha sido definido.
    """
    cleaned_query = query.strip()
    if cleaned_query.endswith(";"):
        cleaned_query = cleaned_query[:-1].strip()

    query_upper = cleaned_query.upper()

    if re.search(r"\bLIMIT\b", query_upper):
        return cleaned_query
    else:
        return f"{cleaned_query} LIMIT {default_limit}"


def execute_safe_query(db_path: str, query: str) -> Dict[str, Any]:
    """
    Executa a query com todos os guardrails ativos.
    Retorna um  dicionário com:
    - sucess: bool
    - data: lista de registros ou erro
    - row_count: qtd de linhas
    """
    is_valid, reason = validade_query(query)
    if not is_valid:
        return {"success": False, "error": f"Guardrail Bloqueou: {reason}", "data": []}

    safe_query = enforce_query_limits(query)

    abs_path = os.path.abspath(db_path)
    if not os.path.exists(abs_path):
        return {
            "success": False,
            "error": f"Arquivo de banco de dados não encontrado em '{abs_path}'. Execute 'python download_db.py' para baixá-lo.",
            "data": [],
        }

    uri_path = f"file:{abs_path}?mode=ro"

    try:
        conn = sqlite3.connect(uri_path, uri=True)
        cursor = conn.cursor()

        cursor.execute("PRAGMA query_only = ON")

        cursor.execute(safe_query)

        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchall()

        results = [dict(zip(columns, row)) for row in rows]

        conn.close()

        return {
            "success": True,
            "data": results,
            "row_count": len(results),
            "executed_query": safe_query
        }
    except sqlite3.Error as e:
        return {"success": False, "error": f"Erro SQLite: {str(e)}", "data": []}


# =============================================================================
# Tools (LangChain)
# =============================================================================

@tool
def describe_tables(table_names: str) -> str:
    """
    Inspeciona o esquema do banco CineData.
    Passe 'list' para ver os nomes de todas as tabelas disponíveis.
    Ou passe nomes de tabelas separados por vírgula (ex: 'dim_movies, fact_movies_performance')
    para ver suas colunas e tipos de dados.
    """
    if not os.path.exists(DB_PATH):
        return f"Arquivo de banco de dados não encontrado em '{DB_PATH}'. Execute 'python download_db.py' para baixá-lo."

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cleaned = table_names.strip().lower()

    if cleaned == "list":
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall() if not r[0].startswith("alembic")]
        conn.close()
        return f"Tabelas disponíveis: {', '.join(tables)}"

    output = []
    for table in table_names.split(","):
        table_clean = table.strip()
        cur.execute(f"PRAGMA table_info({table_clean})")
        cols = [f"{col[1]} ({col[2]})" for col in cur.fetchall()]
        if cols:
            output.append(f"Tabela {table_clean}:\n  - " + "\n  - ".join(cols))
        else:
            output.append(f"Tabela '{table_clean}' não encontrada no banco.")

    conn.close()
    return "\n\n".join(output)


@tool(response_format="content_and_artifact")
def execute_sql_query(query: str) -> Tuple[str, Dict[str, Any]]:
    """
    Executa uma consulta SQL analítica no banco SQLite do CineData.
    A query deve ser estritamente de leitura (SELECT ou WITH) e é protegida por guardrails.
    Retorna os dados em formato JSON ou a mensagem de erro detalhada para correção.
    """
    result = execute_safe_query(DB_PATH, query)

    if not result["success"]:
        return f"ERRO NA CONSULTA: {result['error']}", result

    if not result["data"]:
        return "Consulta executada com sucesso, mas nenhum registro foi retornado com esses criterios.", result

    return json.dumps(result["data"][:15], ensure_ascii=False, default=str), result



TOOLS = [describe_tables, execute_sql_query]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}


# =============================================================================
# System Prompt
# =============================================================================

SYSTEM_PROMPT = """Você é o Agente Analítico Especialista do CineData Analytics.
    Sua missão é responder perguntas de negócio consultando a camada Gold no banco SQLite.

    DIRETRIZES DE ARQUITETURA E EXECUÇÃO:
    1. Sempre verifique o esquema das tabelas com `describe_tables` antes de chutar nomes de colunas.
    2. A tabela fato central de métricas financeiras e notas é `fact_movies_performance`.
    3. A tabela dimensão com títulos e datas é `dim_movies`. Ambas se unem por `sk_movie_id`.
    4. Para atores e diretores, use `dim_people` ligada pela tabela bridge `bridge_movie_person`.
    5. Gere apenas SQL válido e utilize a ferramenta `execute_sql_query` para buscar os dados reais.
    6. Sempre responda ao usuário em português brasileiro claro, objetivo e executivo.
    """


# =============================================================================
# Agent Loop
# =============================================================================

MEMORY_TURNS = 3


@dataclass(frozen=True)
class Turn:
    """Um Turno concluído: pergunta do usuário + resposta final do agente."""
    question: str
    answer: str


@dataclass(frozen=True)
class Step:
    """Um Passo do Rastro de Execução: uma chamada de ferramenta e seu resultado."""
    tool_name: str
    args: Dict[str, Any]
    output: str                                   # texto que o modelo recebeu
    sql: Optional[str] = None                     # SQL efetivamente executado (com LIMIT)
    rows: Optional[List[Dict[str, Any]]] = None   # linhas completas retornadas


@dataclass(frozen=True)
class FinalAnswer:
    """Fim do Rastro de Execução: a resposta do agente ao Turno."""
    content: str
    reached_step_limit: bool = False   # True = o agente não chegou a uma resposta


def _step_from(tool_call: Dict[str, Any], tool_message: ToolMessage) -> Step:
    artifact = tool_message.artifact or {}
    succeeded = artifact.get("success", False)
    return Step(
        tool_name=tool_call["name"],
        args=tool_call["args"],
        output=str(tool_message.content),
        sql=artifact.get("executed_query") if succeeded else None,
        rows=artifact.get("data") if succeeded else None,
    )


def _memory_window(history: Sequence[Turn]) -> List[BaseMessage]:
    """Converte os últimos MEMORY_TURNS Turnos em mensagens (sem ToolMessages)."""
    messages: List[BaseMessage] = []
    for turn in list(history)[-MEMORY_TURNS:]:
        messages.append(HumanMessage(content=turn.question))
        messages.append(AIMessage(content=turn.answer))
    return messages


def stream_agent(question: str, history: Sequence[Turn] = (), llm=None, max_steps: int = 5) -> Iterator[Union[Step, FinalAnswer]]:
    """
    Executa o ciclo de conversa do agente com tool-calling e auto-correção,
    emitindo cada Passo assim que ele acontece e, por fim, a FinalAnswer.
    `history` são os Turnos anteriores; só a Janela de Memória vai para o modelo.
    `llm` só precisa ser passado nos testes; por padrão usa o ChatGroq real.
    """
    llm = llm or get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *_memory_window(history),
        HumanMessage(content=question),
    ]

    for _ in range(max_steps):
        response = llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            yield FinalAnswer(content=response.content)
            return

        for tool_call in response.tool_calls:
            tool_obj = TOOLS_BY_NAME[tool_call["name"]]
            # Invocar com o tool_call inteiro (e não só com os args) faz o LangChain
            # devolver um ToolMessage pronto, com tool_call_id e artifact preenchidos.
            tool_message = tool_obj.invoke(tool_call)
            messages.append(tool_message)
            yield _step_from(tool_call, tool_message)

    yield FinalAnswer(
        content="O limite maximo de iteracoes sem uma resposta boa foi atingido :(",
        reached_step_limit=True,
    )


def run_cinedata_agente(question: str, max_steps: int = 5, verbose: bool = True) -> str:
    """
    Versão para o notebook: consome o Rastro de Execução, imprime os Passos
    (se verbose) e devolve só o texto da resposta final.
    """
    answer = ""
    for step_number, event in enumerate(stream_agent(question, max_steps=max_steps), start=1):
        if isinstance(event, FinalAnswer):
            answer = event.content
        elif verbose:
            print(f"[Passo {step_number}] O agente chamou essa tool: {event.tool_name} com esses argumentos: {event.args}")
    return answer


# =============================================================================
# Modelo (Groq) e falhas
# =============================================================================

MODEL_NAME = "openai/gpt-oss-120b"

def has_api_key() -> bool:
    """True se a GROQ_API_KEY estiver disponível (no ambiente ou no .env)."""
    load_dotenv()
    return bool(os.getenv("GROQ_API_KEY"))


@lru_cache(maxsize=1)
def get_llm():
    """
    Cria o ChatGroq com as tools vinculadas uma única vez, sob demanda.
    Não é criado no import para que o módulo carregue mesmo sem a chave.
    """
    load_dotenv()
    return ChatGroq(model=MODEL_NAME, temperature=0).bind_tools(TOOLS)


def friendly_error_message(error: Exception) -> str:
    """Traduz uma exceção do agente numa mensagem curta para o usuário."""
    if isinstance(error, (groq.RateLimitError, groq.APIConnectionError)):
        return (
            "O serviço do modelo está indisponível ou no limite de requisições. "
            "Tente novamente em alguns segundos."
        )
    return f"Ocorreu um erro inesperado ao consultar o agente: {error}"

