from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


def test_app_sem_api_key_exibe_aviso_e_desabilita_input():
    at = AppTest.from_file(APP_PATH)
    with patch("cinedata_agent.has_api_key", return_value=False):
        at.run(timeout=15)

    assert not at.exception
    assert at.title[0].value == "Converse com o CineData"
    # Deve haver mensagem de erro avisando sobre a GROQ_API_KEY
    assert any("GROQ_API_KEY" in err.value for err in at.error)
    # Chat input desabilitado
    assert at.chat_input[0].disabled is True


def test_app_com_api_key_exibe_perguntas_sugeridas_e_input_habilitado():
    at = AppTest.from_file(APP_PATH)
    with patch("cinedata_agent.has_api_key", return_value=True):
        at.run(timeout=15)

    assert not at.exception
    assert at.chat_input[0].disabled is False
    # Há 5 botões com as perguntas sugeridas na tela inicial
    button_labels = [b.label for b in at.button]
    assert any("Nova conversa" in label for label in button_labels)
    # 5 perguntas sugeridas + 1 botão de nova conversa na sidebar = 6 botões
    assert len(at.button) == 6


def test_botao_nova_conversa_limpa_historico():
    at = AppTest.from_file(APP_PATH)
    with patch("cinedata_agent.has_api_key", return_value=True):
        at.run(timeout=15)
        # Simula histórico existente no session_state
        at.session_state["entries"] = [{"pergunta": "teste", "resposta": "ok"}]
        # Clica no botão "Nova conversa" (primeiro botão na sidebar)
        sidebar_button = [b for b in at.sidebar.button if "Nova conversa" in b.label][0]
        sidebar_button.click().run(timeout=15)

    assert not at.exception
    assert at.session_state["entries"] == []
