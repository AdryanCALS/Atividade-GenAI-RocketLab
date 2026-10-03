"""
Interface de chat do agente Text-to-SQL do CineData Analytics.

Rodar com:  streamlit run app.py

Toda a lógica do agente vive em `cinedata_agent.py`; este arquivo só cuida de
exibir a conversa, os Passos ao vivo e o Rastro de Execução de cada resposta.
"""

from dataclasses import dataclass
from typing import List

import pandas as pd
import streamlit as st

from cinedata_agent import (
    FinalAnswer,
    Step,
    Turn,
    friendly_error_message,
    has_api_key,
    stream_agent,
)

# Uma pergunta de cada categoria da suíte de testes do notebook.
SUGGESTED_QUESTIONS = [
    ("💰", "Quais são os 10 filmes com maior receita em reais (receita_brl) no catálogo?"),
    ("🔥", "Quais são os 5 filmes mais populares do catálogo segundo a métrica de popularidade?"),
    ("🎬", "Quais são os diretores (tipo_pessoa = 'Diretor') com maior nota média IMDb, "
           "considerando apenas diretores com no mínimo 5 filmes dirigidos?"),
    ("🎭", "Qual é a quantidade de filmes cadastrados para cada gênero no catálogo?"),
    ("⭐", "Quais são os filmes mais avaliados pelos usuários segundo a tabela de reviews?"),
]


@dataclass
class ChatEntry:
    """Um Turno como exibido na tela, incluindo os que falharam."""
    question: str
    answer: str
    steps: List[Step]
    ok: bool  # False = falhou; não entra na Janela de Memória


# =============================================================================
# Renderização
# =============================================================================

def render_step(number: int, step: Step) -> None:
    st.markdown(f"**Passo {number} · `{step.tool_name}`**")

    if step.tool_name != "execute_sql_query":
        st.caption(f"Argumentos: {step.args}")
        st.text(step.output)
        return

    if step.sql is None:
        # Bloqueado pelo guardrail ou erro do SQLite: mostra o que o modelo tentou.
        st.code(step.args.get("query", ""), language="sql")
        st.warning(step.output)
        return

    st.code(step.sql, language="sql")
    if step.rows:
        st.dataframe(pd.DataFrame(step.rows), hide_index=True, width="stretch")
    else:
        st.caption("Nenhuma linha retornada.")


def render_entry(entry: ChatEntry) -> None:
    with st.chat_message("user"):
        st.markdown(entry.question)

    with st.chat_message("assistant"):
        if entry.ok:
            st.markdown(entry.answer)
        else:
            st.error(entry.answer)

        if entry.steps:
            with st.expander(f"Rastro de Execução ({len(entry.steps)} passos)"):
                for number, step in enumerate(entry.steps, start=1):
                    render_step(number, step)


# =============================================================================
# Execução de um Turno
# =============================================================================

def answer_question(question: str) -> ChatEntry:
    """Roda o agente mostrando os Passos ao vivo e devolve o Turno pronto para o histórico."""
    history = [Turn(e.question, e.answer) for e in st.session_state.entries if e.ok]
    steps: List[Step] = []

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.status("Consultando o CineData...", expanded=True) as status:
                for event in stream_agent(question, history=history):
                    if isinstance(event, Step):
                        steps.append(event)
                        render_step(len(steps), event)
                    elif isinstance(event, FinalAnswer):
                        final = event
                status.update(state="error" if final.reached_step_limit else "complete")
        except Exception as error:  # noqa: BLE001 - qualquer falha vira mensagem, sem derrubar a sessão
            return ChatEntry(question, friendly_error_message(error), steps, ok=False)

    return ChatEntry(question, final.content, steps, ok=not final.reached_step_limit)


# =============================================================================
# Página
# =============================================================================

st.set_page_config(page_title="CineData Analytics", page_icon="🎬")

if "entries" not in st.session_state:
    st.session_state.entries = []

with st.sidebar:
    st.header("🎬 CineData Analytics")
    st.write(
        "Pergunte em português sobre filmes, bilheteria, elenco e avaliações. "
        "O agente consulta o banco em modo somente leitura e mostra o SQL que executou."
    )
    if st.button("Nova conversa", width="stretch"):
        st.session_state.entries = []
        st.rerun()

st.title("Converse com o CineData")

api_key_ok = has_api_key()
if not api_key_ok:
    st.error(
        "A variável `GROQ_API_KEY` não foi encontrada. Crie um arquivo `.env` na raiz do "
        "projeto (veja `.env.example`) e reinicie o app."
    )

for entry in st.session_state.entries:
    render_entry(entry)

question = st.chat_input("Faça uma pergunta sobre o catálogo...", disabled=not api_key_ok)
question = question or st.session_state.pop("pending_question", None)

if not st.session_state.entries and not question:
    st.caption("Experimente uma destas perguntas:")
    for icon, suggestion in SUGGESTED_QUESTIONS:
        st.button(
            f"{icon} {suggestion}",
            width="stretch",
            disabled=not api_key_ok,
            on_click=st.session_state.__setitem__,
            args=("pending_question", suggestion),
        )

if question:
    st.session_state.entries.append(answer_question(question))
    st.rerun()  # redesenha o histórico com o Rastro de Execução recolhido
