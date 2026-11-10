"""Streamlit UI for the Research Agent.

Run from starter_v0/:
    streamlit run app.py

Uses the same prompt, tools.yaml, providers and transcript format as chat.py.
One extra guardrail lives here, outside the model: a `send` call with
confirmed=true is never executed directly. The UI holds it and shows the exact
text with Send / Cancel buttons, so nothing leaves the machine without a click.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    assistant_tool_message,
    execute_tool_call,
    now_iso,
    safe_slug,
    tool_results_message,
    trim_history,
    write_transcript,
)
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from tools.send.tool import send_telegram
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).parent
SYSTEM_PROMPT_PATH = ROOT / "artifacts" / "system_prompt.md"
TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"
TRANSCRIPTS_DIR = ROOT / "transcripts"
PROVIDERS = ["openrouter", "openai", "anthropic", "gemini", "ollama"]
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4

SAMPLE_PROMPTS = [
    "Tin tức AI hôm nay có gì nổi bật?",
    "Lấy 3 tweet mới nhất của Andrej Karpathy",
    "Trên Hacker News đang có bài nào nổi bật về AI agents?",
    "Tìm 3 repo GitHub nhiều sao nhất về RAG",
    "Tra Wikipedia tiếng Anh: Retrieval-augmented generation là gì?",
    "Tóm tắt bài viết này hộ mình",
]


def is_confirmed_send(call: ToolCall) -> bool:
    """True for a real outbound send. Matched by function, so renaming the tool keeps the guardrail."""
    return TOOL_FUNCTIONS.get(call.name) is send_telegram and bool(call.args.get("confirmed"))


def run_turn(
    *,
    provider: Any,
    messages: list[dict[str, str]],
    tools: list[dict[str, Any]],
    model: str | None,
    max_tool_rounds: int = MAX_TOOL_ROUNDS,
) -> dict[str, Any]:
    """chat.py's tool loop, plus the hold on confirmed `send` calls."""
    working_messages = list(messages)
    rounds: list[dict[str, Any]] = []
    all_tool_events: list[dict[str, Any]] = []

    for round_index in range(1, max_tool_rounds + 1):
        response = provider.complete(working_messages, tools, model=model, temperature=0.0)
        calls = response.tool_calls
        round_record: dict[str, Any] = {
            "round": round_index,
            "assistant_text": response.text,
            "tool_calls": [{"name": call.name, "args": call.args} for call in calls],
            "tool_results": [],
        }
        if not calls:
            rounds.append(round_record)
            return {"status": "answered", "assistant_text": response.text or "", "rounds": rounds, "tool_events": all_tool_events}

        working_messages.append(assistant_tool_message(response.text, calls))
        events: list[dict[str, Any]] = []
        for call in calls:
            if is_confirmed_send(call):
                event = {"tool": call.name, "args": call.args, "result": {"status": "held_for_ui_confirmation"}}
                round_record["tool_results"].append(event)
                all_tool_events.append(event)
                rounds.append(round_record)
                return {
                    "status": "waiting_for_send_confirmation",
                    "assistant_text": "Mình đã chuẩn bị nội dung bên dưới. Bấm **Gửi lên Telegram** để gửi, hoặc **Huỷ**.",
                    "pending_send": str(call.args.get("text") or ""),
                    "rounds": rounds,
                    "tool_events": all_tool_events,
                }

            event = execute_tool_call(call)
            round_record["tool_results"].append(event)
            all_tool_events.append(event)
            result = event.get("result", {})
            if isinstance(result, dict) and result.get("awaiting_user"):
                rounds.append(round_record)
                return {
                    "status": "waiting_for_user",
                    "assistant_text": result.get("question") or call.args.get("question") or "Bạn bổ sung thêm thông tin nhé.",
                    "rounds": rounds,
                    "tool_events": all_tool_events,
                }
            events.append(event)

        rounds.append(round_record)
        working_messages.append(tool_results_message(events))

    return {
        "status": "max_tool_rounds",
        "assistant_text": f"Đã dừng sau {max_tool_rounds} vòng gọi tool. Xem transcript để biết chi tiết.",
        "rounds": rounds,
        "tool_events": all_tool_events,
    }


# ---------------- Streamlit page ----------------

@st.cache_resource(show_spinner=False)
def get_provider(name: str) -> Any:
    return make_provider(name)


def start_session(provider_name: str, model: str | None, version: str) -> None:
    artifact_version = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    transcript_id = "_".join(["ui", safe_slug(version), safe_slug(provider_name), datetime.now().strftime("%Y%m%dT%H%M%S%f")])
    st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "ui": "streamlit",
        "provider": provider_name,
        "model": model,
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": HISTORY_WINDOW,
        "max_tool_rounds": MAX_TOOL_ROUNDS,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    st.session_state.history = []
    st.session_state.chat = []
    st.session_state.pending_send = None


def record_turn(user_text: str, result: dict[str, Any]) -> None:
    transcript = st.session_state.transcript
    transcript["turns"].append({
        "turn_index": len(transcript["turns"]) + 1,
        "started_at": result.pop("started_at", now_iso()),
        "user": user_text,
        **result,
        "ended_at": now_iso(),
    })
    write_transcript(st.session_state.transcript_path, transcript)


def add_exchange(user_text: str, assistant_text: str, tool_events: list[dict[str, Any]], *, show_user: bool = True) -> None:
    if show_user:
        st.session_state.chat.append({"role": "user", "text": user_text})
    st.session_state.chat.append({"role": "assistant", "text": assistant_text, "tool_events": tool_events})
    st.session_state.history += [
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": assistant_text},
    ]


def handle_user_message(user_text: str, provider: Any, model: str | None) -> None:
    if st.session_state.pending_send is not None:
        # A new message while a send is waiting counts as "not confirmed".
        st.session_state.pending_send = None
        add_exchange("[Giao diện] Người dùng không xác nhận gửi.", "Đã huỷ gửi lên Telegram.", [], show_user=False)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")},
        *trim_history(st.session_state.history, HISTORY_WINDOW),
        {"role": "user", "content": user_text},
    ]
    tools = to_openai_tools(load_tool_declarations(TOOLS_PATH))
    started_at = now_iso()
    try:
        result = run_turn(provider=provider, messages=messages, tools=tools, model=model)
    except Exception as exc:  # provider/network failure: show it, log it, keep the app alive
        error = f"{type(exc).__name__}: {exc}"
        st.session_state.chat.append({"role": "user", "text": user_text})
        st.session_state.chat.append({"role": "assistant", "text": f"Lỗi provider: {error}", "tool_events": []})
        record_turn(user_text, {"started_at": started_at, "status": "provider_error", "error": error})
        return

    st.session_state.pending_send = result.get("pending_send")
    add_exchange(user_text, result["assistant_text"], result["tool_events"])
    record_turn(user_text, {"started_at": started_at, **result})


def resolve_pending_send(confirmed: bool) -> None:
    text = st.session_state.pending_send
    st.session_state.pending_send = None
    if not confirmed:
        add_exchange("[Giao diện] Người dùng bấm Huỷ.", "Đã huỷ, không gửi gì lên Telegram.", [], show_user=False)
        record_turn("[UI] cancel send", {"status": "send_cancelled", "assistant_text": "Đã huỷ gửi.", "rounds": [], "tool_events": []})
        return

    outcome = send_telegram(text=text, confirmed=True)
    event = {"tool": "send", "args": {"text": text, "confirmed": True}, "result": outcome}
    if outcome.get("status") == "sent":
        reply = "Đã gửi lên Telegram."
    else:
        reply = f"Gửi thất bại: {outcome.get('message') or outcome.get('error') or outcome}"
    add_exchange("[Giao diện] Người dùng bấm xác nhận gửi.", reply, [event], show_user=False)
    record_turn("[UI] confirm send", {"status": "send_confirmed_in_ui", "assistant_text": reply, "rounds": [], "tool_events": [event]})


def render_tool_events(events: list[dict[str, Any]]) -> None:
    if not events:
        return
    names = ", ".join(event.get("tool", "?") for event in events)
    with st.expander(f"Tool đã gọi ({len(events)}): {names}"):
        for event in events:
            st.markdown(f"**{event.get('tool', '?')}**")
            st.json({"args": event.get("args"), "result": event.get("result")}, expanded=False)


def main() -> None:
    st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="centered")

    with st.sidebar:
        st.header("Cấu hình")
        provider_name = st.selectbox("Provider", PROVIDERS, index=0)
        model_input = st.text_input("Model (để trống = mặc định của provider)", value="")
        version = st.text_input("Version label", value="v3")
        model = model_input.strip() or None

    try:
        provider = get_provider(provider_name)
    except Exception as exc:
        st.title("Research Agent")
        st.error(f"Không khởi tạo được provider `{provider_name}`: {exc}")
        st.info("Kiểm tra key trong file `.env` của `starter_v0/`, rồi tải lại trang.")
        return

    settings = (provider_name, model, version)
    if st.session_state.get("settings") != settings or "transcript" not in st.session_state:
        st.session_state.settings = settings
        start_session(provider_name, model or getattr(provider, "default_model", None), version)

    declarations = load_tool_declarations(TOOLS_PATH)
    queued: str | None = None
    with st.sidebar:
        st.caption(f"Model: `{st.session_state.transcript['model']}`")
        st.caption(f"Artifact: `{st.session_state.transcript['artifact_version']}`")
        if st.button("Cuộc trò chuyện mới", use_container_width=True):
            start_session(provider_name, st.session_state.transcript["model"], version)
            st.rerun()
        st.subheader("Câu hỏi mẫu")
        for index, sample in enumerate(SAMPLE_PROMPTS):
            if st.button(sample, key=f"sample_{index}", use_container_width=True):
                queued = sample
        with st.expander(f"Tool ({len(declarations)})"):
            for item in declarations:
                st.markdown(f"**{item['name']}**: {item.get('description', '')}")
        st.caption(f"Transcript: `{st.session_state.transcript_path.name}`")

    st.title("Research Agent")
    st.caption("Tìm tin, đọc link, xem tweet, tra Hacker News / Wikipedia / GitHub, tổng hợp digest, lưu ghi chú.")

    for entry in st.session_state.chat:
        with st.chat_message(entry["role"]):
            st.markdown(entry["text"])
            render_tool_events(entry.get("tool_events") or [])

    if st.session_state.pending_send is not None:
        with st.container(border=True):
            st.warning("Agent muốn gửi nội dung sau lên Telegram. Chưa có gì được gửi.")
            st.code(st.session_state.pending_send, language="markdown")
            left, right = st.columns(2)
            if left.button("Gửi lên Telegram", type="primary", use_container_width=True):
                resolve_pending_send(True)
                st.rerun()
            if right.button("Huỷ", use_container_width=True):
                resolve_pending_send(False)
                st.rerun()

    typed = st.chat_input("Nhập yêu cầu research...")
    user_text = (typed or queued or "").strip()
    if user_text:
        with st.spinner("Agent đang xử lý..."):
            handle_user_message(user_text, provider, model)
        st.rerun()


if __name__ == "__main__":
    main()
