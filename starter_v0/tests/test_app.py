from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

import chat


APP = Path(__file__).resolve().parents[1] / "app.py"


def test_ui_preserves_clarification_context_and_saves_transcript(monkeypatch):
    requests = []
    saved = []

    def fake_loop(**kwargs):
        requests.append(kwargs)
        question = len(requests) == 1
        return {
            "status": "waiting_for_user" if question else "answered",
            "assistant_text": "Bạn gửi URL nhé." if question else "Đã đọc bài viết.",
            "rounds": [],
            "tool_events": [{"tool": "clarify" if question else "fetch", "args": {}, "result": {}}],
        }

    monkeypatch.setattr(chat, "run_model_tool_loop", fake_loop)
    monkeypatch.setattr(chat, "write_transcript", lambda path, data: saved.append(deepcopy(data)))
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    app.chat_input[0].set_value("Tóm tắt bài này").run()
    assert not app.exception
    app.chat_input[0].set_value("https://example.com/article").run()
    assert not app.exception
    assert len(saved[-1]["turns"]) == 2
    assert requests[-1]["messages"][-2]["content"] == "Bạn gửi URL nhé."
    assert requests[-1]["messages"][-1]["content"] == "https://example.com/article"
    assert len(app.chat_message) == 4


def test_new_conversation_clears_history_without_deleting_saved_transcript(monkeypatch):
    saved = []
    monkeypatch.setattr(chat, "run_model_tool_loop", lambda **kwargs: {
        "status": "answered", "assistant_text": "Xin chào", "rounds": [], "tool_events": [],
    })
    monkeypatch.setattr(chat, "write_transcript", lambda path, data: saved.append(deepcopy(data)))
    app = AppTest.from_file(str(APP)).run()
    app.chat_input[0].set_value("Chào bạn").run()
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["conversation"] is None
    assert len(app.chat_message) == 0
    assert len(saved) == 1


def test_provider_failure_is_visible_and_does_not_expose_exception_text(monkeypatch):
    def fail(**kwargs):
        raise RuntimeError("private-token-must-not-appear")

    monkeypatch.setattr(chat, "run_model_tool_loop", fail)
    monkeypatch.setattr(chat, "write_transcript", lambda path, data: None)
    app = AppTest.from_file(str(APP)).run()
    app.chat_input[0].set_value("Tìm tin mới").run()
    assert not app.exception
    assert len(app.error) == 1
    record = app.session_state["conversation"]["turns"][-1]
    assert record["status"] == "provider_error"
    assert record["error"] == "RuntimeError"
    assert "private-token" not in str(record)
