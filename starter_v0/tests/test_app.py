"""Exercise the UI agent integration offline; never create live demo evidence."""
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from providers.base import ModelResponse, ToolCall


APP = Path(__file__).resolve().parents[1] / "app.py"


class ScriptedProvider:
    default_model = "offline-test-model"

    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def complete(self, messages, tools=None, **kwargs):
        self.requests.append(deepcopy(messages))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def test_ui_clarification_tool_execution_history_and_transcript(monkeypatch):
    import chat
    import providers

    items = [{"url": "https://example.com/a"}, {"url": "https://example.com/a"}]
    provider = ScriptedProvider([
        ModelResponse(text=None, tool_calls=[ToolCall("clarify", {"question": "Which sources?"})]),
        ModelResponse(text=None, tool_calls=[ToolCall("deduplicate_sources", {"items": items})]),
        ModelResponse(text="One unique source.", tool_calls=[]),
        ModelResponse(text="The source is example.com/a.", tool_calls=[]),
    ])
    saved = []
    monkeypatch.setattr(providers, "make_provider", lambda name: provider)
    monkeypatch.setattr(chat, "write_transcript", lambda path, value: saved.append((path, deepcopy(value))))
    at = AppTest.from_file(str(APP), default_timeout=10).run()
    assert not at.exception
    at.chat_input[0].set_value("Remove duplicates from my sources.").run()
    assert not at.exception
    assert saved[-1][1]["turns"][-1]["status"] == "waiting_for_user"
    at.chat_input[0].set_value(str(items)).run()
    assert not at.exception
    turn = saved[-1][1]["turns"][-1]
    assert turn["assistant_text"] == "One unique source."
    assert turn["tool_events"][0]["result"]["removed_count"] == 1
    assert saved[-1][0].suffixes == [".transcript", ".json"]
    at.chat_input[0].set_value("Which source did you keep?").run()
    assert not at.exception
    assert len(saved[-1][1]["turns"]) == 3
    assert any('"removed_count": 1' in msg["content"] for msg in provider.requests[-1])
    assert len(at.get("download_button")) == 1
    at.button[0].click().run()
    assert not at.exception
    assert len(at.session_state["research_session"]["transcript"]["turns"]) == 0
    assert len(saved) == 3  # Reset never overwrites the saved conversation.


def test_ui_provider_error_is_visible_and_does_not_break_chat(monkeypatch):
    import chat
    import providers

    provider = ScriptedProvider([RuntimeError("offline failure")])
    saved = []
    monkeypatch.setattr(providers, "make_provider", lambda name: provider)
    monkeypatch.setattr(chat, "write_transcript", lambda path, value: saved.append(deepcopy(value)))
    at = AppTest.from_file(str(APP), default_timeout=10).run()
    at.chat_input[0].set_value("Find sources.").run()
    assert not at.exception
    assert at.error
    assert saved[-1]["turns"][-1]["status"] == "provider_error"
    assert len(at.get("download_button")) == 1
