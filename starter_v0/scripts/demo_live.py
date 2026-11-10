"""Chạy kịch bản demo ba lượt qua model thật, lưu đầy đủ transcript."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import conversation_messages, new_session, redact
from chat import now_iso, run_model_tool_loop, write_transcript
from providers import make_provider


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", default="openrouter")
    parser.add_argument("--model", default="")
    parser.add_argument("--version", default="v5-demo")
    args = parser.parse_args()
    session = new_session(args.provider, args.model, args.version, 4)
    transcript = session["transcript"]
    transcript["interface"] = "scripted_live_demo"
    transcript["transcript_id"] = transcript["transcript_id"].replace("_ui_", "_demo_")
    transcript["demo_note"] = (
        "Kịch bản do chương trình nhập, gọi model và tool thật; "
        "không phải lượt thao tác thủ công trên giao diện hoặc test dùng provider giả."
    )
    path = ROOT / "transcripts" / f"{transcript['transcript_id']}.transcript.json"
    queries = [
        'Loại nguồn trùng URL trong danh sách này, giữ bản đầu tiên: '
        '[{"title":"Nguồn A","url":"https://example.com/a"},'
        '{"title":"Nguồn B","url":"https://example.com/b"},'
        '{"title":"Nguồn A trùng","url":"https://example.com/a"}]. '
        'Chỉ xử lý danh sách đã có, không mở URL. Trả lời bằng tiếng Việt.',
        'Dùng tool format trình bày hai nguồn đã giữ ở lượt trước thành danh sách '
        'gạch đầu dòng, template bullets. Không tìm nguồn mới. Trả lời bằng tiếng Việt.',
        'Tóm tắt bài viết này giúp tôi. Tôi chưa cung cấp đường dẫn ở lượt này; '
        'bài viết mới không phải các nguồn ví dụ ở trên. Hãy hỏi tôi bằng tiếng Việt '
        'nếu thiếu thông tin.',
    ]
    for index, query in enumerate(queries, start=1):
        print(f"Đang chạy lượt {index}/3...", flush=True)
        turn = {"turn_index": index, "started_at": now_iso(), "user": query,
                "status": "started", "assistant_text": None, "rounds": [], "tool_events": []}
        try:
            turn.update(run_model_tool_loop(
                provider=make_provider(args.provider),
                messages=conversation_messages(session, query), tools=session["tools"],
                model=transcript["model"], max_tool_rounds=4,
            ))
        except Exception as exc:
            turn.update(status="provider_error", error=f"{type(exc).__name__}: {exc}")
        turn["ended_at"] = now_iso()
        transcript["turns"].append(redact(turn))
        write_transcript(path, redact(transcript))
        print(f"Lượt {index}: {turn['status']}", flush=True)
    print(f"Đã lưu: {path}")
    if any(turn["status"] == "provider_error" for turn in transcript["turns"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
