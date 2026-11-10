# Captain Research Agent — Streamlit UI

Chạy từ thư mục `starter_v0` (giữ API key trong `.env`):

```powershell
uv pip install -r requirements.txt
uv run python -m streamlit run app.py
```

Mở địa chỉ local mà Streamlit hiển thị, thông thường là
`http://localhost:8501`. Dừng server bằng `Ctrl+C`.

## Dùng thử

- Tìm tin: `Tìm 3 tin AI hôm nay trên web.`
- Trong hội thoại mới: `Tóm tắt bài viết này giúp mình`, sau đó bổ sung URL
  khi agent hỏi lại. Nếu đã có nhiều link trong ngữ cảnh, chỉ rõ bài muốn đọc.
- Tool mới: `Loại URL trùng: [{"title":"A","url":"https://example.com/a"},{"title":"B","url":"https://example.com/a"}]`.

Thanh bên cho chọn provider và model trước lượt đầu tiên. Muốn thay cấu hình
hoặc thử yêu cầu thiếu thông tin từ đầu, chọn **Hội thoại mới**.
Mở **Công cụ đã dùng** bên dưới câu trả lời để xem arguments và kết quả thật.
Lỗi công cụ được hiển thị riêng, không đồng nghĩa toàn bộ yêu cầu thành công.

Mỗi lượt tự lưu vào `transcripts/ui_*.transcript.json`. Có thể tải transcript
hiện tại bằng nút **Tải transcript JSON**. Nội dung có thể bao gồm dữ liệu
người dùng và kết quả công cụ; chỉ chia sẻ transcript phù hợp để demo.

## Link cho nhóm khác dùng thử

Sau khi UI hoạt động, làm theo phần Cloudflare Tunnel trong README chính:

```powershell
cloudflared tunnel --url http://localhost:8501
```

Giữ cả terminal Streamlit và tunnel đang chạy. Link tunnel chỉ tồn tại trong
phiên đó; điền link thực tế vào Phần A của `artifacts/REPORT.md`.
Khách dùng UI sẽ sử dụng API credit của máy chủ. Việc xây UI local không tự
tạo link public. Không đưa `.env` vào repository.

## Kiểm tra offline

```powershell
uv run python -m pytest
```

`tests/test_app.py` kiểm tra UI bằng Streamlit AppTest với model giả:
không gọi API thật, không gửi Telegram và không tạo transcript demo giả vào
thư mục nộp bài.
