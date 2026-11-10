"""Tests for the UI tool loop (app.run_turn) with a scripted fake provider. No model, no network."""
from __future__ import annotations

import pytest

pytest.importorskip("streamlit")

from app import is_confirmed_send, run_turn  # noqa: E402
from conftest import FakeResponse  # noqa: E402
from providers.base import ModelResponse, ToolCall  # noqa: E402


class ScriptedProvider:
    """Returns one prepared ModelResponse per call and records the messages it was given."""

    def __init__(self, responses: list[ModelResponse]) -> None:
        self.responses = list(responses)
        self.seen: list[list[dict]] = []

    def complete(self, messages, tools=None, *, model=None, temperature=0.0, tool_choice=None) -> ModelResponse:
        self.seen.append(list(messages))
        return self.responses.pop(0)


def _run(provider: ScriptedProvider) -> dict:
    return run_turn(provider=provider, messages=[{"role": "user", "content": "x"}], tools=[], model=None)


def test_confirmed_send_is_held_and_never_reaches_the_network(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TEST")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "@test_channel")
    calls = fake_http(FakeResponse({"ok": True}))
    provider = ScriptedProvider([
        ModelResponse(text=None, tool_calls=[ToolCall("send", {"text": "Bản tin", "confirmed": True})]),
    ])

    result = _run(provider)

    assert result["status"] == "waiting_for_send_confirmation"
    assert result["pending_send"] == "Bản tin"
    assert result["tool_events"][0]["result"] == {"status": "held_for_ui_confirmation"}
    assert calls == []


def test_unconfirmed_send_is_not_held_and_result_goes_back_to_model(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    provider = ScriptedProvider([
        ModelResponse(text=None, tool_calls=[ToolCall("send", {"text": "Bản tin", "confirmed": False})]),
        ModelResponse(text="Bạn xác nhận gửi chứ?", tool_calls=[]),
    ])

    result = _run(provider)

    assert result["status"] == "answered"
    assert result["assistant_text"] == "Bạn xác nhận gửi chứ?"
    assert result["tool_events"][0]["result"]["status"] == "needs_confirmation"
    assert "needs_confirmation" in provider.seen[1][-1]["content"]
    assert calls == []


def test_clarify_pauses_the_loop_with_the_question() -> None:
    provider = ScriptedProvider([
        ModelResponse(text=None, tool_calls=[ToolCall("clarify", {"question": "Tài khoản nào?"})]),
    ])

    result = _run(provider)

    assert result["status"] == "waiting_for_user"
    assert result["assistant_text"] == "Tài khoản nào?"
    assert len(provider.seen) == 1


def test_loop_stops_after_max_tool_rounds() -> None:
    looping = [ModelResponse(text=None, tool_calls=[ToolCall("format", {"items": [], "template": "bullets"})]) for _ in range(4)]

    result = _run(ScriptedProvider(looping))

    assert result["status"] == "max_tool_rounds"
    assert len(result["rounds"]) == 4


def test_is_confirmed_send_only_matches_the_send_tool_with_confirmed_true() -> None:
    assert is_confirmed_send(ToolCall("send", {"text": "x", "confirmed": True})) is True
    assert is_confirmed_send(ToolCall("send", {"text": "x"})) is False
    assert is_confirmed_send(ToolCall("save_note", {"content": "x", "confirmed": True})) is False
