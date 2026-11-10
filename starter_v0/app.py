from __future__ import annotations

import json
from uuid import uuid4

import streamlit as st

from chat import ROOT, now_iso, run_model_tool_loop, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


VERSION = "v3-deduplicate"
PROMPT_PATH = ROOT / "artifacts" / "system_prompt.md"
TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"


def new_session(provider_name: str, model: str) -> dict:
    provider = make_provider(provider_name)
    session_id = f"ui_{VERSION}_{provider_name}_{uuid4().hex}"
    return {
        "transcript_id": session_id,
        **artifact_version_dict(build_artifact_version(VERSION, PROMPT_PATH, TOOLS_PATH)),
        "provider": provider_name,
        "model": model or getattr(provider, "default_model", None),
        "system_prompt": str(PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": 5,
        "max_tool_rounds": 4,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
        # Freeze the configuration for the lifetime of this conversation.
        "prompt_snapshot": PROMPT_PATH.read_text(encoding="utf-8"),
        "tools_snapshot": to_openai_tools(load_tool_declarations(TOOLS_PATH)),
    }


def show_turn(turn: dict) -> None:
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant", avatar="🧭"):
        if turn["status"] == "provider_error":
            st.error("Chưa kết nối được model. Kiểm tra API key, credit và mạng rồi thử lại.")
        else:
            st.markdown(turn.get("assistant_text") or "Agent chưa trả về nội dung.")
        events = turn.get("tool_events", [])
        if events:
            with st.expander("Công cụ đã dùng · " + ", ".join(event["tool"] for event in events)):
                for event in events:
                    st.caption(event["tool"])
                    st.json(event)
            if any(isinstance(e.get("result"), dict) and e["result"].get("error") for e in events):
                st.warning("Có công cụ trả về lỗi. Mở chi tiết để kiểm tra kết quả và cấu hình dịch vụ.")


def main() -> None:
    st.set_page_config(page_title="Captain · Research Agent", page_icon="🧭", layout="wide")
    if "conversation" not in st.session_state:
        st.session_state.conversation = None

    with st.sidebar:
        st.title("🧭 captain")
        st.caption("RESEARCH WORKSPACE")
        active = st.session_state.conversation
        provider_name = st.selectbox("Model provider", ["openrouter", "openai", "anthropic", "gemini", "ollama"], disabled=bool(active))
        model = st.text_input("Model (tùy chọn)", placeholder="Dùng model mặc định", disabled=bool(active)).strip()
        if st.button("＋ Hội thoại mới", use_container_width=True):
            st.session_state.conversation = None
            st.rerun()
        st.divider()
        st.markdown("**Nghiên cứu cùng nguồn dẫn**\n\nTìm tin web, đọc bài viết, tra policy và paper; loại các URL trùng trước khi làm bản tin.")
        st.caption("API key được đọc từ cấu hình máy chủ. Mỗi yêu cầu model có thể sử dụng credit API.")
        if active:
            st.caption(f"{active['model']} · {len(active['turns'])} lượt")
            st.download_button(
                "↓ Tải transcript JSON",
                json.dumps(active, ensure_ascii=False, indent=2, default=str),
                file_name=active["transcript_id"] + ".transcript.json",
                mime="application/json",
                use_container_width=True,
            )

    st.caption("CAPTAIN / RESEARCH AGENT")
    st.title("Từ câu hỏi đến nguồn tin.")
    st.write("Nghiên cứu, đọc nguồn và tổng hợp trong một cuộc hội thoại.")
    conversation = st.session_state.conversation
    if not conversation:
        columns = st.columns(3)
        for column, title, example in zip(columns,
            ["Tìm tin mới", "Đọc nguồn", "Làm sạch bản tin"],
            ["Tìm 3 tin AI hôm nay trên web.", "Tóm tắt https://www.python.org/about/", "Loại URL trùng trong danh sách item tôi cung cấp."],
        ):
            with column.container(border=True):
                st.markdown(f"**{title}**")
                st.caption(example)
    else:
        for turn in conversation["turns"]:
            show_turn(turn)

    user_text = st.chat_input("Bạn muốn nghiên cứu điều gì?")
    if user_text and user_text.strip():
        if conversation is None:
            conversation = new_session(provider_name, model)
            st.session_state.conversation = conversation
        history = []
        for turn in conversation["turns"]:
            if turn["status"] != "provider_error":
                history.extend([
                    {"role": "user", "content": turn["user"]},
                    {"role": "assistant", "content": turn.get("assistant_text") or ""},
                ])
        record = {
            "turn_index": len(conversation["turns"]) + 1,
            "started_at": now_iso(), "user": user_text.strip(),
            "rounds": [], "tool_events": [],
        }
        with st.spinner("Đang nghiên cứu…"):
            try:
                result = run_model_tool_loop(
                    provider=make_provider(conversation["provider"]),
                    messages=[{"role": "system", "content": conversation["prompt_snapshot"]},
                              *trim_history(history, 5), {"role": "user", "content": user_text.strip()}],
                    tools=conversation["tools_snapshot"], model=conversation["model"], max_tool_rounds=4,
                )
                record.update(result)
            except Exception as exc:
                # Keep credential-bearing exception text out of the UI and transcript.
                record.update(status="provider_error", error=type(exc).__name__, assistant_text="")
        record["ended_at"] = now_iso()
        conversation["turns"].append(record)
        try:
            write_transcript(ROOT / "transcripts" / (conversation["transcript_id"] + ".transcript.json"), conversation)
        except OSError:
            st.warning("Chưa lưu được transcript trên máy chủ. Bạn vẫn có thể tải JSON ở thanh bên.")
            show_turn(record)
        else:
            st.rerun()


if __name__ == "__main__":
    main()
