# Demo Streamlit

Chạy các lệnh từ thư mục `starter_v0` trên PowerShell:

```powershell
uv --cache-dir ../.uv-cache pip install --python .venv/Scripts/python.exe -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
```

Mở http://localhost:8501. Nếu đã cài đủ dependency, chỉ cần lệnh thứ hai.
Nhập provider key trong `.env`; giao diện dùng chung cấu hình với `chat.py`.

## Kịch bản demo

Nhóm: **captain**. Phiên bản cấu hình hiện tại: **v5-demo**.
Giữ nhãn này ở thanh bên và bấm **Bắt đầu cuộc trò chuyện mới** sau khi cập nhật mã nguồn.

1. Gửi: `Tóm tắt bài viết này giúp tôi.` Agent cần hỏi URL.
2. Bổ sung một URL có thật. Với `fetch`, cần `FIRECRAWL_API_KEY` hợp lệ.
3. Thử tool mới bằng yêu cầu:

```text
Loại nguồn trùng URL: [{"url":"https://example.com/a"}, {"url":"https://example.com/b"}, {"url":"https://example.com/a"}]
```

Mở phần **Xem tool calls và kết quả** để kiểm tra arguments, kết quả thực thi
và lỗi tool nếu có. Tool mới không gọi mạng, nhưng model vẫn cần provider key.
Với tình huống tìm tin tức web, dùng `Tìm tin tức robotics trong tuần này.`;
tool `lookup` cần `TAVILY_API_KEY`. Tool Twitter cần `RAPIDAPI_KEY`.

Transcript được lưu sau mỗi lượt vào `transcripts/*.transcript.json`.
Dùng nút **Tải transcript JSON** ở thanh bên để tải bằng chứng nộp bài.
Khi đổi provider/model/nhãn phiên bản, bấm **Bắt đầu cuộc trò chuyện mới**.
Phiên cũ giữ nguyên file transcript. Prompt và khai báo tool được giữ cố định
trong từng phiên; tạo phiên mới sau khi sửa artifacts.

Đã có một phiên UI thật và một kịch bản ba lượt gọi model thật làm bằng chứng
trong `REPORT.md` phần B4. Kịch bản ba lượt thực hiện loại nguồn trùng,
trình bày lại nguồn và hỏi URL; không gửi Telegram hoặc đọc URL ví dụ.
Để chạy lại kịch bản qua API thật:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/demo_live.py --version v5-demo
```

Đây là kịch bản do chương trình nhập, không được ghi nhầm là thao tác người dùng
thủ công. Các lượt hỏi đáp vẫn dùng model và tool thật; transcript được lưu riêng.

## Link dùng thử

**Link public tạm thời đang dùng:** https://melissa-sequences-sing-incidence.trycloudflare.com

Link này đã được kiểm tra HTTP 200. Link chỉ tồn tại trong phiên Cloudflare Tunnel
hiện tại; nếu khởi động tunnel lại có thể nhận URL khác và cần cập nhật REPORT A1.
Nếu máy đã cài `cloudflared`, mở terminal khác:

```powershell
cloudflared tunnel --url http://localhost:8501
```

Nếu dùng bản cloudflared tải trong dự án:

```powershell
.\.demo-tools\cloudflared.exe tunnel --url http://127.0.0.1:8501 --protocol http2 --no-autoupdate
```

Dán URL HTTPS được cấp vào REPORT phần A1 và giữ cả hai terminal chạy khi demo.
Link tunnel cho phép người truy cập sử dụng model và tool của phiên demo.
Chỉ chia sẻ trong phạm vi buổi lab; tắt tunnel khi demo xong.
