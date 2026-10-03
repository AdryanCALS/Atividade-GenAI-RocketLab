"""
Testes do agente nas seams acordadas: o gerador `stream_agent` (Rastro de Execução),
a Janela de Memória e a tradução de falhas do Groq.

O LLM é substituído por um modelo roteirizado (fronteira externa: API do Groq) e o
banco por um SQLite temporário, então os testes não gastam tokens nem dependem do
arquivo de 581 MB.
"""

import sqlite3

import groq
import httpx
import pytest
from langchain_core.messages import AIMessage, ToolMessage

import cinedata_agent
from cinedata_agent import FinalAnswer, Step, Turn, friendly_error_message, stream_agent


class ScriptedLLM:
    """Devolve as respostas roteirizadas em ordem e guarda as mensagens recebidas."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(list(messages))
        return self.responses.pop(0)


def sql_call(query, call_id="call_1"):
    return AIMessage(
        content="",
        tool_calls=[{"name": "execute_sql_query", "args": {"query": query}, "id": call_id}],
    )


@pytest.fixture
def movies_db(tmp_path, monkeypatch):
    db = tmp_path / "movies.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE dim_movies (titulo TEXT, ano INTEGER)")
    conn.executemany(
        "INSERT INTO dim_movies VALUES (?, ?)",
        [(f"Filme {i:02d}", 2000 + i) for i in range(1, 21)],
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(cinedata_agent, "DB_PATH", str(db))
    return db


def test_turno_com_sql_gera_passo_com_query_executada_e_linhas(movies_db):
    llm = ScriptedLLM(
        sql_call("SELECT titulo, ano FROM dim_movies WHERE ano <= 2002 ORDER BY ano"),
        AIMessage(content="Os filmes são Filme 01 e Filme 02."),
    )

    events = list(stream_agent("Quais filmes saíram até 2002?", llm=llm))

    assert events == [
        Step(
            tool_name="execute_sql_query",
            args={"query": "SELECT titulo, ano FROM dim_movies WHERE ano <= 2002 ORDER BY ano"},
            output='[{"titulo": "Filme 01", "ano": 2001}, {"titulo": "Filme 02", "ano": 2002}]',
            sql="SELECT titulo, ano FROM dim_movies WHERE ano <= 2002 ORDER BY ano LIMIT 100",
            rows=[{"titulo": "Filme 01", "ano": 2001}, {"titulo": "Filme 02", "ano": 2002}],
        ),
        FinalAnswer(content="Os filmes são Filme 01 e Filme 02."),
    ]


def test_modelo_recebe_no_maximo_15_linhas_mas_passo_guarda_resultado_completo(movies_db):
    llm = ScriptedLLM(
        sql_call("SELECT titulo FROM dim_movies"),
        AIMessage(content="São 20 filmes."),
    )

    events = list(stream_agent("Liste os filmes", llm=llm))

    step = events[0]
    assert len(step.rows) == 20
    tool_message_seen_by_model = llm.calls[1][-1]
    assert isinstance(tool_message_seen_by_model, ToolMessage)
    assert tool_message_seen_by_model.content.count('"titulo"') == 15


def test_janela_de_memoria_envia_apenas_os_3_ultimos_turnos():
    history = [Turn(question=f"pergunta {i}", answer=f"resposta {i}") for i in range(1, 6)]
    llm = ScriptedLLM(AIMessage(content="ok"))

    list(stream_agent("e agora?", history=history, llm=llm))

    conversation = [(type(m).__name__, m.content) for m in llm.calls[0][1:]]
    assert conversation == [
        ("HumanMessage", "pergunta 3"),
        ("AIMessage", "resposta 3"),
        ("HumanMessage", "pergunta 4"),
        ("AIMessage", "resposta 4"),
        ("HumanMessage", "pergunta 5"),
        ("AIMessage", "resposta 5"),
        ("HumanMessage", "e agora?"),
    ]


def test_limite_de_passos_encerra_o_rastro_com_falha(movies_db):
    llm = ScriptedLLM(
        sql_call("SELECT titulo FROM dim_movies LIMIT 1", "c1"),
        sql_call("SELECT titulo FROM dim_movies LIMIT 2", "c2"),
    )

    events = list(stream_agent("pergunta difícil", llm=llm, max_steps=2))

    assert [type(e).__name__ for e in events] == ["Step", "Step", "FinalAnswer"]
    assert events[-1].reached_step_limit is True
    assert events[-1].content == "O limite maximo de iteracoes sem uma resposta boa foi atingido :("


def _groq_request():
    return httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")


@pytest.mark.parametrize(
    "error",
    [
        groq.RateLimitError(
            "rate limit", response=httpx.Response(429, request=_groq_request()), body=None
        ),
        groq.APIConnectionError(request=_groq_request()),
    ],
    ids=["limite-de-requisicoes", "falha-de-rede"],
)
def test_falhas_temporarias_do_groq_pedem_para_tentar_novamente(error):
    assert friendly_error_message(error) == (
        "O serviço do modelo está indisponível ou no limite de requisições. "
        "Tente novamente em alguns segundos."
    )


def test_falha_inesperada_vira_mensagem_generica_com_o_motivo():
    message = friendly_error_message(ValueError("algo quebrou"))

    assert message == "Ocorreu um erro inesperado ao consultar o agente: algo quebrou"
