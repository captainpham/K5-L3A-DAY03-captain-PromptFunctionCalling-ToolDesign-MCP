"""Streamlit demo using the same agent loop and transcript format as chat.py."""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import streamlit as st

from chat import (
    now_iso, run_model_tool_loop, safe_slug,
    tool_results_message, write_transcript,
)
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).resolve().parent
PROMPT = ROOT / "artifacts/system_prompt.md"
DECLARATIONS = ROOT / "artifacts/tools.yaml"


def new_session(provider_name: str, model: str, version: str, rounds: int) -> dict:
    provider = make_provider(provider_name)
    selected_model = model.strip() or provider.default_model
    artifact = build_artifact_version(version.strip() or "demo", PROMPT, DECLARATIONS)
    transcript_id = (
        f"{safe_slug(artifact.version)}_{provider_name}_ui_"
        f"{datetime.now():%Y%m%dT%H%M%S%f}_{uuid4().hex[:8]}"
    )
    return {
        "prompt": PROMPT.read_text(encoding="utf-8"),
        "tools": to_openai_tools(load_tool_declarations(DECLARATIONS)),
        "transcript": {
            "transcript_id": transcript_id,
            **artifact_version_dict(artifact),
            "provider": provider_name, "model": selected_model,
            "system_prompt": str(PROMPT), "tools": str(DECLARATIONS),
            "history_window": 5, "max_tool_rounds": rounds,
            "created_at": now_iso(), "updated_at": now_iso(), "turns": [],
            "interface": "streamlit",
        },
    }


def redact(value):
    """Keep credential values out of UI and saved evidence, including error URLs."""
    if isinstance(value, str):
        for name, secret in os.environ.items():
            if secret and len(secret) >= 8 and (name.endswith("_API_KEY") or name.endswith("_TOKEN")):
                value = value.replace(secret, "[REDACTED]")
        return value
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    return value


def conversation_messages(session: dict, user_text: str) -> list[dict]:
    messages = [{"role": "system", "content": session["prompt"]}]
    for turn in session["transcript"]["turns"][-5:]:
        if turn["status"] == "provider_error":
            continue
        messages.append({"role": "user", "content": turn["user"]})
        for round_record in turn.get("rounds", []):
            events = round_record.get("tool_results", [])
            if events:
                # Preserve actual source data and tool arguments across user turns.
                calls = round_record.get("tool_calls", [])
                messages.append({"role": "assistant", "content":
                    "TOOL_CALLS_JSON:\n" + json.dumps(calls, ensure_ascii=False)})
                messages.append(tool_results_message(events))
        if turn.get("assistant_text"):
            messages.append({"role": "assistant", "content": turn["assistant_text"]})
    messages.append({"role": "user", "content": user_text})
    return messages


def show_turn(turn: dict) -> None:
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant"):
        if turn["status"] == "provider_error":
            st.error("Không thể gọi model. Kiểm tra kết nối, API key và hạn mức rồi thử lại.")
        else:
            st.markdown(turn.get("assistant_text") or "Agent chưa trả về nội dung.")
        if turn["status"] == "waiting_for_user":
            st.caption("Đang chờ bạn bổ sung thông tin hoặc xác nhận.")
        if turn["status"] == "max_tool_rounds":
            st.warning("Đã đạt giới hạn gọi tool. Hãy xem chi tiết và thử yêu cầu cụ thể hơn.")
        events = turn.get("tool_events", [])
        errors = [event for event in events if event.get("result", {}).get("error")]
        if errors:
            st.warning("Một số tool chưa lấy được dữ liệu. Xem chi tiết bên dưới.")
        if events or turn.get("error"):
            with st.expander("Xem tool calls và kết quả"):
                st.json(redact(events if events else {"error": turn["error"]}))


def main() -> None:
    st.set_page_config(page_title="Trợ lý nghiên cứu", page_icon="🔎", layout="centered")
    st.title("🔎 Trợ lý nghiên cứu")
    st.caption("Tìm nguồn, đọc bài viết và loại nguồn trùng. Theo dõi từng tool mà agent sử dụng.")

    with st.sidebar:
        st.header("Phiên demo")
        with st.form("settings"):
            provider_name = st.selectbox("Nhà cung cấp mô hình", ["openrouter", "openai", "anthropic", "gemini", "ollama"])
            model = st.text_input("Mô hình (để trống dùng mặc định)")
            version = st.text_input("Nhãn phiên bản", value="v5-demo")
            rounds = st.slider("Số vòng gọi tool tối đa", 2, 8, 4)
            start = st.form_submit_button("Bắt đầu cuộc trò chuyện mới", use_container_width=True)
        st.caption("Thay đổi cấu hình sẽ áp dụng khi bắt đầu cuộc trò chuyện mới.")

    if start or "research_session" not in st.session_state:
        try:
            st.session_state.research_session = new_session(provider_name, model, version, rounds)
        except Exception:
            st.error("Không thể đọc cấu hình agent. Kiểm tra system_prompt.md và tools.yaml.")
            st.stop()

    session = st.session_state.research_session
    transcript = session["transcript"]
    transcript_path = ROOT / "transcripts" / f"{transcript['transcript_id']}.transcript.json"
    with st.sidebar:
        st.write(f"**Mô hình:** {transcript['model']}")
        st.caption(f"Phiên bản: {transcript['artifact_version']}")
        st.caption(f"Đã ghi {len(transcript['turns'])} lượt hội thoại.")
        if transcript["turns"]:
            st.download_button(
                "Tải transcript JSON",
                data=json.dumps(redact(transcript), ensure_ascii=False, indent=2),
                file_name=transcript_path.name, mime="application/json",
                use_container_width=True,
            )
        with st.expander("Tool có sẵn"):
            for tool in session["tools"]:
                st.write(f"• {tool['function']['name']}")

    if not transcript["turns"]:
        st.info("Nhập yêu cầu để bắt đầu. Agent sẽ hỏi lại nếu thiếu thông tin.")
        with st.expander("Câu hỏi mẫu để demo", expanded=True):
            st.code("Tìm tin tức robotics trong tuần này.", language=None)
            st.code("Tóm tắt bài viết này giúp tôi.", language=None)
            st.code('Loại nguồn trùng URL: [{"url":"https://example.com/a"}, '
                    '{"url":"https://example.com/b"}, {"url":"https://example.com/a"}]', language=None)

    for turn in transcript["turns"]:
        show_turn(turn)

    user_text = st.chat_input("Bạn muốn tìm hiểu điều gì?")
    if user_text and user_text.strip():
        turn = {
            "turn_index": len(transcript["turns"]) + 1,
            "started_at": now_iso(), "user": user_text.strip(),
            "status": "started", "assistant_text": None,
            "rounds": [], "tool_events": [],
        }
        with st.spinner("Agent đang xử lý…"):
            try:
                result = run_model_tool_loop(
                    provider=make_provider(transcript["provider"]),
                    messages=conversation_messages(session, turn["user"]),
                    tools=session["tools"], model=transcript["model"],
                    max_tool_rounds=transcript["max_tool_rounds"],
                )
                turn.update(result)
            except Exception as exc:
                turn.update(status="provider_error", error=f"{type(exc).__name__}: {exc}")
        turn["ended_at"] = now_iso()
        transcript["turns"].append(redact(turn))
        try:
            write_transcript(transcript_path, redact(transcript))
        except OSError:
            show_turn(transcript["turns"][-1])
            st.error("Không lưu được transcript vào ổ đĩa. Bạn vẫn có thể tải JSON ở thanh bên.")
            st.download_button("Tải bản sao transcript", json.dumps(redact(transcript), ensure_ascii=False, indent=2),
                               file_name=transcript_path.name, mime="application/json")
            st.stop()
        st.rerun()


if __name__ == "__main__":
    main()
