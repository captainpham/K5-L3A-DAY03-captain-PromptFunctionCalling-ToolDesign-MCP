"""Streamlit UI for the Research Agent.

Run from starter_v0/:
    streamlit run app.py

Uses the same prompt, tools.yaml, providers and transcript format as chat.py.
One extra guardrail lives here, outside the model: a `send` call with
confirmed=true is never executed directly. The UI holds it and shows the exact
text with Send / Cancel buttons, so nothing leaves the machine without a click.

The page shows no configuration. Provider, model and version label come from
optional env vars: APP_PROVIDER (default openrouter), APP_MODEL (default: the
provider's default model), APP_VERSION (default v3). Every turn is still logged
to transcripts/*.transcript.json.
"""
from __future__ import annotations

import os
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
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4

SUGGESTIONS = [
    (":material/newspaper:", "Tin tức AI hôm nay có gì nổi bật?"),
    (":material/forum:", "Hacker News đang bàn gì về AI agents?"),
    (":material/code:", "Tìm 3 repo GitHub nhiều sao nhất về RAG"),
    (":material/menu_book:", "Tra Wikipedia: Transformer là gì?"),
]

# Names shown to people instead of internal tool names.
TOOL_LABELS = {
    "timeline": "Tweet theo tài khoản",
    "social_search": "Tìm trên X",
    "lookup": "Tìm trên web",
    "fetch": "Đọc trang web",
    "format": "Soạn bản tin",
    "send": "Gửi Telegram",
    "policy": "Chính sách nội bộ",
    "papers": "Tìm paper arXiv",
    "paper_text": "Đọc paper",
    "hackernews": "Hacker News",
    "wikipedia": "Wikipedia",
    "github_repos": "GitHub",
    "save_note": "Lưu ghi chú",
}

PAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Inter:wght@400;500;600&display=swap');

:root {
  --paper: #faf8f4;
  --card: #ffffff;
  --ink: #1c1b19;
  --muted: #7a756c;
  --line: #e6e1d8;
  --tint: #f1ede5;
  --accent: #1f3d36;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--paper);
  color: var(--ink);
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}

/* Streamlit chrome people never use */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
#MainMenu, footer { display: none !important; }

.block-container { max-width: 780px; padding: 2.25rem 1.25rem 8rem; }

/* Brand row */
.brand { display: flex; align-items: baseline; gap: .7rem; }
.brand-name { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.6rem; font-weight: 600; letter-spacing: .01em; }
.brand-mark { color: var(--accent); font-size: .8rem; transform: translateY(-.2rem); }
.rule { border: 0; border-top: 1px solid var(--line); margin: .9rem 0 0; }

/* Empty state */
.hero { text-align: center; padding: 4.5rem 0 2.2rem; }
.hero h1 { font-family: 'Cormorant Garamond', Georgia, serif; font-weight: 500; font-size: clamp(2.1rem, 5.4vw, 3rem); line-height: 1.12; margin: 0 0 .9rem; padding: 0; color: var(--ink); text-wrap: balance; }
.hero p { color: var(--muted); font-size: 1rem; line-height: 1.6; max-width: 34rem; margin: 0 auto; }
.eyebrow { color: var(--muted); font-size: .72rem; letter-spacing: .14em; text-transform: uppercase; margin: 0 0 .6rem; }

/* Buttons */
.stButton, .stButton > button { width: 100%; }
.stButton > button p { white-space: normal; overflow: visible; text-overflow: clip; }
.stButton > button {
  width: 100%; min-height: 3.4rem; justify-content: flex-start; text-align: left;
  background: var(--card); color: var(--ink); border: 1px solid var(--line); border-radius: 14px;
  padding: .8rem 1rem; font-size: .92rem; font-weight: 400; line-height: 1.35; box-shadow: none;
  transition: border-color .15s ease, transform .15s ease;
}
.stButton > button:hover { border-color: var(--accent); color: var(--ink); background: var(--card); transform: translateY(-1px); }
.stButton > button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.stButton > button [data-testid="stIconMaterial"] { color: var(--accent); }
.stButton > button[kind="primary"] { background: var(--accent); border-color: var(--accent); color: #fff; justify-content: center; font-weight: 500; }
.stButton > button[kind="primary"]:hover { background: #17302a; color: #fff; }
.st-key-new_chat button { min-height: 2.2rem; padding: .3rem .8rem; font-size: .82rem; color: var(--muted); border-radius: 999px; justify-content: center; background: transparent; }
.st-key-cancel_send button { justify-content: center; }

/* Conversation */
[data-testid="stChatMessage"] { background: transparent; padding: .2rem 0; gap: 0; }
[data-testid="stChatMessage"] > [data-testid^="stChatMessageAvatar"] { display: none; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: var(--tint); border-radius: 18px 18px 4px 18px; padding: .7rem 1.05rem;
  width: fit-content; max-width: 85%; margin-left: auto;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { font-size: .97rem; line-height: 1.65; }
[data-testid="stChatMessage"] a { color: var(--accent); }
[data-testid="stChatMessage"] h1, [data-testid="stChatMessage"] h2, [data-testid="stChatMessage"] h3 {
  font-family: 'Cormorant Garamond', Georgia, serif; font-weight: 600;
}

/* "Sources used" disclosure */
[data-testid="stExpander"] details { border: 1px solid var(--line); border-radius: 12px; background: transparent; }
[data-testid="stExpander"] summary { color: var(--muted); font-size: .8rem; padding: .45rem .8rem; }
[data-testid="stExpander"] summary:hover { color: var(--accent); }

/* Pending-send card */
.send-title { font-weight: 600; margin: 0 0 .2rem; }
.send-note { color: var(--muted); font-size: .85rem; margin: 0 0 .4rem; }

/* Input */
[data-testid="stBottom"], [data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] { background: var(--paper); }
[data-testid="stBottomBlockContainer"] { max-width: 780px; padding: .6rem 1.25rem 1.4rem; }
[data-testid="stChatInput"] > div { background: var(--card); border: 1px solid var(--line); border-radius: 18px; box-shadow: 0 6px 24px rgba(28, 27, 25, .06); }
[data-testid="stChatInput"] > div:focus-within { border-color: var(--accent); }
[data-testid="stChatInput"] textarea { font-size: .97rem; color: var(--ink); }
[data-testid="stChatInputSubmitButton"] { color: var(--accent); }
</style>
"""


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
                    "assistant_text": "Mình đã chuẩn bị nội dung bên dưới. Bạn xem lại rồi chọn gửi hoặc huỷ.",
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
        "assistant_text": "Mình chưa hoàn tất được yêu cầu này sau nhiều bước. Bạn thử diễn đạt lại ngắn gọn hơn nhé.",
        "rounds": rounds,
        "tool_events": all_tool_events,
    }


# ---------------- Session + transcript ----------------

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
    except Exception as exc:  # provider/network failure: log the detail, show a plain message, keep the app alive
        error = f"{type(exc).__name__}: {exc}"
        st.session_state.chat.append({"role": "user", "text": user_text})
        st.session_state.chat.append({
            "role": "assistant",
            "text": "Mình chưa kết nối được tới mô hình. Bạn thử lại sau ít phút nhé.",
            "tool_events": [],
        })
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
        reply = "Chưa gửi được lên Telegram. Kênh Telegram chưa được cấu hình hoặc đang lỗi kết nối."
    add_exchange("[Giao diện] Người dùng bấm xác nhận gửi.", reply, [event], show_user=False)
    record_turn("[UI] confirm send", {"status": "send_confirmed_in_ui", "assistant_text": reply, "rounds": [], "tool_events": [event]})


# ---------------- Page ----------------

def render_sources(events: list[dict[str, Any]]) -> None:
    """One quiet line naming what the agent used; raw detail stays folded away."""
    shown = [event for event in events if event.get("tool") in TOOL_LABELS]
    if not shown:
        return
    labels = list(dict.fromkeys(TOOL_LABELS[event["tool"]] for event in shown))
    with st.expander("Đã dùng: " + " · ".join(labels)):
        for event in shown:
            st.caption(TOOL_LABELS[event["tool"]])
            st.json({"args": event.get("args"), "result": event.get("result")}, expanded=False)


def render_header(show_new_chat: bool) -> bool:
    left, right = st.columns([4, 1.25], vertical_alignment="center")
    left.markdown(
        '<div class="brand"><span class="brand-mark">&#9670;</span><span class="brand-name">Research Agent</span></div>',
        unsafe_allow_html=True,
    )
    clicked = show_new_chat and right.button("Trò chuyện mới", key="new_chat")
    st.markdown('<hr class="rule">', unsafe_allow_html=True)
    return bool(clicked)


def render_empty_state() -> str | None:
    st.markdown(
        '<div class="hero">'
        '<p class="eyebrow">Trợ lý nghiên cứu</p>'
        "<h1>Hôm nay bạn muốn tìm hiểu điều gì?</h1>"
        "<p>Tìm tin tức, đọc và tóm tắt một đường link, xem mọi người đang bàn gì, "
        "rồi gói lại thành bản tin có dẫn nguồn.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    picked: str | None = None
    columns = st.columns(2)
    for index, (icon, prompt) in enumerate(SUGGESTIONS):
        if columns[index % 2].button(prompt, icon=icon, key=f"suggestion_{index}", width="stretch"):
            picked = prompt
    return picked


def render_pending_send() -> None:
    with st.container(border=True):
        st.markdown(
            '<p class="send-title">Gửi nội dung này lên Telegram?</p>'
            '<p class="send-note">Chưa có gì được gửi. Nội dung chỉ rời máy khi bạn bấm Gửi.</p>',
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state.pending_send)
        left, right = st.columns(2)
        if left.button("Gửi lên Telegram", type="primary", key="confirm_send", width="stretch"):
            resolve_pending_send(True)
            st.rerun()
        if right.button("Huỷ", key="cancel_send", width="stretch"):
            resolve_pending_send(False)
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="Research Agent", page_icon="◆", layout="centered", initial_sidebar_state="collapsed")
    st.markdown(PAGE_CSS, unsafe_allow_html=True)

    provider_name = os.getenv("APP_PROVIDER", "openrouter")
    model = os.getenv("APP_MODEL") or None
    version = os.getenv("APP_VERSION", "v3")

    try:
        provider = get_provider(provider_name)
    except Exception:
        render_header(show_new_chat=False)
        st.markdown(
            '<div class="hero"><h1>Trợ lý chưa sẵn sàng</h1>'
            "<p>Chưa kết nối được tới mô hình. Người quản trị cần kiểm tra khoá API trong file cấu hình, rồi tải lại trang.</p></div>",
            unsafe_allow_html=True,
        )
        return

    if "transcript" not in st.session_state:
        start_session(provider_name, model or getattr(provider, "default_model", None), version)

    if render_header(show_new_chat=bool(st.session_state.chat)):
        start_session(provider_name, st.session_state.transcript["model"], version)
        st.rerun()

    picked: str | None = None
    if not st.session_state.chat:
        picked = render_empty_state()

    for entry in st.session_state.chat:
        with st.chat_message(entry["role"]):
            st.markdown(entry["text"])
            render_sources(entry.get("tool_events") or [])

    if st.session_state.pending_send is not None:
        render_pending_send()

    typed = st.chat_input("Hỏi về tin tức, một đường link, hay một chủ đề...")
    user_text = (typed or picked or "").strip()
    if user_text:
        with st.chat_message("user"):
            st.markdown(user_text)
        with st.spinner("Đang tìm hiểu..."):
            handle_user_message(user_text, provider, model)
        st.rerun()


if __name__ == "__main__":
    main()
