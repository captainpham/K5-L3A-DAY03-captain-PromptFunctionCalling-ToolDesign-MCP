# Day 03 Lab v2 Report — Research Agent

> Báo cáo giữ cấu trúc mẫu: Phần A giới thiệu agent để demo; Phần B trình bày kết quả và bằng chứng thực nghiệm. Số liệu được lấy từ run JSON, version log, transcript và kết quả pytest thực tế.

## Nhóm

- Tên nhóm: **captain**
- Thành viên:
- Nhà cung cấp/mô hình: **OpenRouter / openai/gpt-4o-mini**.
- Phiên bản demo hiện tại: **v5-demo**; mã artifacts: `v5-demo+p3e9aef21d9db+t23097cc67187`.

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Trợ lý nghiên cứu giúp tìm tin trên web và mạng xã hội, đọc nội dung URL, tìm tài liệu nội bộ hoặc bài báo khoa học, rồi trình bày các nguồn thành bản tin. Agent có thể hỏi lại khi thiếu thông tin; tool mới `deduplicate_sources` loại nguồn trùng URL và giữ nguồn xuất hiện đầu tiên.

**Link dùng thử (deploy):**

- URL public tạm thời: **https://melissa-sequences-sing-incidence.trycloudflare.com**
- URL trên máy chạy demo: http://127.0.0.1:8501.
- Link public chỉ hoạt động khi máy, Streamlit và Cloudflare Tunnel còn chạy. Giao diện sử dụng API và hạn mức của nhóm.
- Khởi động và kịch bản trình diễn: `DEMO.md`.
- Đã kiểm tra trang chủ và endpoint sức khỏe của link public đều trả HTTP 200; bằng chứng: `artifacts/demo_status.json`. Kiểm tra hành vi giao diện dùng Streamlit AppTest; công cụ trình duyệt trực quan không khả dụng trong phiên này.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi thông tin còn thiếu hoặc yêu cầu xác nhận và chờ người dùng trả lời | Không |
| timeline | Lấy bài đăng gần đây của một tài khoản Twitter/X; cần RapidAPI | Không |
| social_search | Tìm bài đăng theo chủ đề, hỗ trợ mới nhất hoặc phổ biến; cần RapidAPI | Không |
| lookup | Tìm thông tin hoặc tin tức web theo thời gian; cần Tavily | Không |
| fetch | Đọc nội dung một URL; cần Firecrawl | Không |
| format | Trình bày nguồn đã có thành bản tin, danh sách hoặc chuỗi bài | Không |
| send | Gửi nội dung Telegram khi có xác nhận và cấu hình bot hợp lệ | Không |
| policy | Tìm quy định trong thư mục tài liệu nội bộ của bài lab | Không |
| papers | Tìm bài báo khoa học trên arXiv | Không |
| paper_text | Tải PDF arXiv và trích xuất văn bản | Không |
| deduplicate_sources | Loại URL trùng, giữ mục đầu tiên và thứ tự ban đầu; chạy local | **Có** |

Phạm vi đã kiểm chứng: định tuyến tool, arguments, xử lý nguồn trùng, trình bày dữ liệu, hỏi lại và lịch sử hội thoại. Các tool Twitter đang thiếu `RAPIDAPI_KEY`; Telegram và arXiv chưa được kiểm chứng gửi/tải thật trong bản demo này.

## A3. Câu hỏi mẫu để thử

1. “Tìm tin tức robotics trong tuần này. Trả lời bằng tiếng Việt.”
2. “Tóm tắt bài viết này giúp tôi.” → Quan sát agent hỏi URL; sau đó bổ sung URL thật nếu đã cấu hình Firecrawl.
3. `Loại nguồn trùng URL: [{"url":"https://example.com/a"},{"url":"https://example.com/b"},{"url":"https://example.com/a"}]`
4. “Dùng tool format trình bày hai nguồn vừa giữ thành danh sách gạch đầu dòng, template bullets. Không tìm nguồn mới.”
5. “Theo quy định nội bộ, có được đưa API key vào báo cáo không?”

Trong demo, mở **Xem tool calls và kết quả** để đối chiếu hành động thực tế; tải bằng chứng bằng nút **Tải transcript JSON**.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Bằng chứng phiên bản

Chỉ số trước/sau là tỷ lệ case đúng của cùng bộ eval. Bộ gốc có 20 case; bộ nhóm có 10 case. Không so trực tiếp 100% của bộ nhóm với điểm bộ gốc.

| Phiên bản | Artifacts thay đổi | Giả thuyết | Điểm trước | Điểm sau | File run |
|---|---|---|---:|---:|---|
| v0 (bộ gốc) | Bản gốc | Đo hành vi ban đầu của agent | — | 70% | `runs/v0_B_base_openrouter_20261110T101526319256.json` |
| v1 (bộ gốc) | system_prompt.md | Quy tắc clarify rõ ràng sửa R10 và R11 | 70% | 95% | `runs/v1_B_base_openrouter_20261110T110207578174.json` |
| v2 (bộ gốc) | system_prompt.md | Quy tắc xác nhận ngăn gửi ngay trong R12 | 95% | 90% | `runs/v2_B_base_openrouter_20261110T111637308717.json` |
| v3 (bộ gốc) | Không đổi | Đo lại cùng cấu hình; không phải vòng tối ưu mới | 90% | 90% | `runs/v3_B_base_openrouter_20261110T112035325561.json` |
| v4-tool (bộ gốc) | tools.yaml; tools/deduplicate_sources; tools/__init__.py; run_eval.py | Thêm tool loại nguồn trùng không làm giảm routing cũ | 90% | 80% | `runs/v4-tool_B_base_openrouter_20261110T112835582113.json` |
| v4-tool (bộ nhóm) | tools.yaml; tools/deduplicate_sources; tools/__init__.py; data/eval_group.json; run_eval.py | Agent chọn đúng tool mới và giữ ngữ cảnh nhiều lượt | — | 100% | `runs/v4-tool_B_group_openrouter_20261110T112813402207.json` |
| v5-demo (bộ gốc) | system_prompt.md | Giữ thay đổi nguồn qua các lượt sẽ sửa lỗi M06 | 80% | 85% | `runs/v5-demo_B_base_openrouter_20261110T123743909259.json` |
| v5-demo (bộ nhóm) | system_prompt.md | Giữ routing của tool mới và ngữ cảnh nhiều lượt | 100% | 100% | `runs/v5-demo_B_group_openrouter_20261110T123723623726.json` |

- `v0` là baseline; `v1` thay hướng dẫn đoán thông tin bằng quy tắc hỏi lại và tăng từ 70% lên 95% trong run đã ghi nhận.
- `v2` thêm yêu cầu xác nhận trước khi gửi. `v3` có cùng hash với `v2`, nên là lần chạy lại, không được tính là một thay đổi độc lập.
- `v4-tool` bổ sung tool mới; điểm bộ gốc giảm từ 90% xuống 80%. Giả thuyết “thêm tool không ảnh hưởng định tuyến cũ” chưa được kết quả này ủng hộ.
- `v5-demo` giữ nguồn/chủ đề/ràng buộc qua các lượt và bỏ ép hoàn thành một bước. Bộ gốc đạt **17/20 (85%)**, bộ nhóm đạt **10/10 (100%)**. M06 đã đúng trong run này; R04, R12 và M02 vẫn chưa đạt.
- Cấu hình có điểm bộ gốc cao nhất đã ghi nhận là `v1` (95%); không khẳng định cấu hình mới nhất tốt nhất. Một lần chạy không đủ để kết luận mức cải thiện ổn định.
- Eval chấm tool calls và arguments, không bảo đảm mọi API tool trả dữ liệu thành công. Có 5 case nhóm chọn đúng tool Twitter nhưng tool trả lỗi thiếu key.
- Các run `v4-tool` ban đầu gặp `APIConnectionError` có 0 case đo được; giữ file bằng chứng nhưng không dùng điểm 0% đó để so sánh chất lượng model.

## B2. Phân tích lỗi

| Case | Loại lỗi | Tool thực tế | Lỗi quan sát | Cách xử lý / trạng thái |
|---|---|---|---|---|
| v0 / R10 | Thiếu thông tin | `timeline(screenname="sama")` | Tự chọn tài khoản khi người dùng chưa nêu | Thêm quy tắc `clarify`; R10 đạt ở v1 |
| v0 / R11 | Thiếu thông tin | `fetch(url="https://example.com/article")` | Tự bịa URL | Cấm bịa URL, hỏi lại; R11 đạt ở v1 |
| v0 / R08, R14 | Ngoài phạm vi | `send` | Dùng tool gửi để trả lời câu toán/coding | Sau thay đổi prompt, các case đạt trong run v1; vẫn cần quy tắc phạm vi rõ hơn |
| v5-demo / R04 | Sai tool | `clarify(response_type="yes_no")` | Đã có URL nhưng hỏi xác nhận thay vì đọc bằng `fetch` | Chưa sửa; cần phân biệt đọc dữ liệu với hành động ghi/gửi |
| v5-demo / R12 | Ranh giới hành động | `clarify(response_type="text")` | Hỏi nội dung còn thiếu, trong khi eval yêu cầu xác nhận `yes_no` | Chưa đạt theo bộ chấm; cần đánh giá thủ công vì hỏi nội dung thiếu là hành vi có lý do |
| v5-demo / M02 | Sai định tuyến/arguments | `social_search(query="robotics", search_type="Latest")` | Người dùng đang hỏi tin web nhưng agent chuyển sang Twitter | Chưa sửa; cần làm rõ giữ nguồn và thời gian trong ngữ cảnh |
| v2, v4-tool / M06 | Sai tool | `social_search` | Không giữ thay đổi từ Twitter sang web | Thêm quy tắc giữ nguồn trong v5-demo; case đã đạt ở run v5-demo |

Bằng chứng: các file run tương ứng ở B1, trường `results[*].result.actual_tool_calls` và `failures`. Tên `failure_type` do case định nghĩa có thể rộng hơn sai lệch thực tế; phân tích dựa cả arguments và tool được gọi.

## B3. Case eval của nhóm

`data/eval_group.json` gồm **5 single-turn (G01–G05)** và **5 multi-turn (G06–G10)**. Bộ chấm dùng các lượt trước làm ngữ cảnh và chấm hành động ở lượt cuối; không thay thế kiểm tra hội thoại tương tác thật.

| Case | Nội dung kiểm tra | Tool/hành vi mong đợi | Kết quả v5-demo |
|---|---|---|---|
| G01_handle_without_at | Bỏ ký tự @ và giữ đúng số lượng tweet. | `timeline — {"screenname": "elonmusk", "limit": 3}` | Đạt |
| G02_top_social_posts | Phân biệt tweet phổ biến với tweet mới nhất. | `social_search — {"query": "robotics", "search_type": "Top", "limit": 4}` | Đạt |
| G03_monthly_web_news | Tin web theo tháng phải dùng news và month. | `lookup — {"query": "robotics", "topic": "news", "timeframe": "month"}` | Đạt |
| G04_missing_article_url | Thiếu URL phải hỏi lại, không bịa địa chỉ. | `clarify — {"response_type": "text"}` | Đạt |
| G05_deduplicate_sources | Chọn tool mới và truyền nguyên danh sách đầu vào gồm cả nguồn trùng. | `deduplicate_sources — giữ nguồn đầu tiên, truyền đủ danh sách` | Đạt |
| G06_carry_limit_after_clarification | Giữ số lượng từ lượt trước khi người dùng bổ sung account. | `timeline — {"screenname": "elonmusk", "limit": 4}` | Đạt |
| G07_carry_timeframe_change_topic | Đổi chủ đề nhưng giữ nguồn web, topic news và thời gian month. | `lookup — {"query": "robotics", "topic": "news", "timeframe": "month"}` | Đạt |
| G08_switch_social_to_web | Thay đổi nguồn vẫn có hiệu lực khi lượt cuối chỉ nhắc lại chủ đề. | `lookup — {"query": "robotics", "topic": "news", "timeframe": "week"}` | Đạt |
| G09_correct_limit | Ưu tiên số lượng mới nhất và giữ account từ lịch sử. | `timeline — {"screenname": "elonmusk", "limit": 2}` | Đạt |
| G10_switch_latest_to_top | Đổi Latest sang Top, giữ query và limit. | `social_search — {"query": "robotics", "search_type": "Top", "limit": 3}` | Đạt |

Bằng chứng: `runs/v5-demo_B_group_openrouter_20261110T123723623726.json`. Tất cả 10 case đạt về routing/arguments; tool mới thực thi thành công và loại đúng một nguồn trùng.

## B4. Bằng chứng chat live

| Lượt | Yêu cầu người dùng | Tool được gọi | Bằng chứng phiên bản | Kết quả |
|---|---|---|---|---|
| UI / 1 | Tìm bài báo mới về Jensen Huang | `lookup` | `v4-tool+p3e9aef21d9db+t23097cc67187` | Model trả lời từ kết quả tìm kiếm; chưa kiểm chứng độc lập các tin được dẫn |
| Kịch bản / 1 | Loại nguồn trùng trong danh sách A, B, A | `deduplicate_sources` | `v5-demo+p3e9aef21d9db+t23097cc67187` | Giữ 2 nguồn, `removed_count=1`, trạng thái `answered` |
| Kịch bản / 2 | Dùng lại hai nguồn vừa giữ và trình bày dạng bullets | `format` | `v5-demo+p3e9aef21d9db+t23097cc67187` | Giữ được dữ liệu qua lượt sau, tạo danh sách, trạng thái `answered` |
| Kịch bản / 3 | Tóm tắt bài viết mới nhưng chưa cung cấp URL | `clarify` | `v5-demo+p3e9aef21d9db+t23097cc67187` | Hỏi URL bằng tiếng Việt, trạng thái `waiting_for_user` |

- Transcript thao tác UI: `transcripts/v4-tool_openrouter_ui_20261110T122102768242_344400a3.transcript.json`.
- Transcript kịch bản 3 lượt: `transcripts/v5-demo_openrouter_demo_20261110T123608502128_86fecb4c.transcript.json`.
- Kịch bản dùng model API và tool thật, được chương trình nhập qua `scripts/demo_live.py`; không phải ba lượt người dùng nhập thủ công trên UI và không phải test provider giả. Có thể chạy lại bằng hướng dẫn trong `DEMO.md`.
- Nhãn `v4-tool` của transcript UI cũ có prompt hash `3e9aef21d9db`, khác prompt hash `a476e353fffa` của run eval v4-tool. Vì vậy không gán điểm 80% của run cũ cho phiên UI này. Run v5-demo đã đo đúng prompt hiện tại.

## B5. Bằng chứng bonus và kiểm thử

| Hạng mục | File bằng chứng | Đã làm được | Giới hạn / kiểm soát |
|---|---|---|---|
| send / Telegram | `tests/test_tools_todo.py`, `tests/test_tools_examples.py` | Mock xác nhận, payload gửi và lỗi thiếu cấu hình | Chưa gửi Telegram thật; test không gọi mạng |
| arXiv / tài liệu nội bộ | `tools/papers/`, `tools/paper_text/`, test policy | Có implementation arXiv; policy được kiểm tra lọc lĩnh vực và tách chỉ dẫn không tin cậy | Chưa chạy bonus arXiv thật; không tuyên bố hoàn thành bonus này |
| UI | `app.py`, `DEMO.md`, `tests/test_app.py` | Chat nhiều lượt, hiển thị tool, giữ lịch sử, lưu/tải transcript, link public tạm thời | Link phụ thuộc phiên chạy; API cần key và hạn mức hợp lệ |
| Unit test | `tests/`, `artifacts/tool_tests.txt` | **104 đạt, 0 lỗi, 0 bỏ qua**; có 14 trường hợp cho tool mới | HTTP dùng mock, không thay thế thử nghiệm tích hợp API thật |
| Lỗi bộ chấm | `run_eval.py`, `tests/test_eval_arguments.py` | Sửa so sánh danh sách object không sắp xếp được bằng Python | Giữ thứ tự và phần tử trùng khi so sánh nguồn; vẫn giữ cách so sánh danh sách scalar trước đó |

Đã hoàn thành 14 test TODO có sẵn. Các trường hợp tham số hóa đưa tổng suite tool/eval lên 102; thêm 2 test tích hợp giao diện thành 104. Fixture chặn mọi HTTP thật. Không phát hiện thêm bug trong code tool có sẵn qua các test TODO này; lỗi thực tế được sửa nằm ở bộ chấm danh sách object.

Ví dụ unit test bổ sung giá trị cho eval: `test_lookup_without_timeframe_omits_time_range` kiểm tra request HTTP thực sự bỏ `time_range` khi `timeframe=None`. Model có thể gọi đúng arguments nhưng tool vẫn gửi payload sai; eval routing không phát hiện được lỗi ở lớp request này. Test policy còn kiểm tra câu chỉ dẫn được truy xuất nằm trong `untrusted_text`, không trở thành `facts`.

## B6. Nhìn lại

- **Sửa gì trong system prompt?** Quy tắc hỏi lại khi thiếu URL/account, điều kiện xác nhận trước khi gửi, giữ nguồn và ràng buộc qua nhiều lượt, cho phép nhiều vòng gọi tool. Đây là hành vi chung áp dụng cho nhiều yêu cầu.
- **Sửa gì trong tools.yaml?** Khai báo tool mới, điều kiện dùng/không dùng, schema danh sách nguồn và yêu cầu truyền nguyên dữ liệu có phần tử trùng. Cần tiếp tục làm rõ mô tả các tool cũ để hạn chế nhầm `lookup` với `social_search`.
- **Lỗi nào cần xem thủ công?** R12 hỏi nội dung thiếu thay vì xác nhận có/không; bộ chấm báo sai dù agent đã dừng gửi. Ngoài ra, so khớp query chính xác có thể đánh trượt hai truy vấn gần nghĩa. Giữ kết quả chấm gốc và giải thích, không sửa case để nâng điểm.
- **Bài học từ versioning?** Đổi nhãn không đồng nghĩa đổi artifacts: v2 và v3 cùng hash. Phải so hash và case lỗi trước khi giải thích điểm tăng/giảm. Nhãn transcript cũng phải đối chiếu hash.
- **Cải thiện tiếp theo?** Tách rõ thao tác đọc với ghi; bổ sung routing giữ nguồn/thời gian; chạy lặp lại để đo độ dao động; hoàn thiện RapidAPI; tăng case chưa từng dùng khi tối ưu; kiểm tra chất lượng câu trả lời và độ tin cậy nguồn ngoài routing.

## B7. Thử thách model local nhỏ (bonus)

**Chưa thực hiện.** Chưa có run Ollama, chưa thử ít nhất hai model local và chưa có hai vòng tối ưu local; không nhận hoàn thành bonus này.

| Phiên bản | Mô hình/nhà cung cấp | Prompt/tools | Đúng case | Định tuyến | Arguments | Nhiều lượt | File run |
|---|---|---|---|---|---|---|---|
| Chưa thực hiện | Chưa đo model local | Chưa có | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa có |

| Kiểu lỗi model nhỏ | Số lượng | Case ví dụ | Cách sửa đã thử | Có cải thiện? |
|---|---|---|---|---|
| Chưa có dữ liệu thực nghiệm | Chưa đo | Không có | Chưa thực hiện | Chưa kết luận |

Chưa đủ bằng chứng để kết luận prompt nào giúp model nhỏ gọi tool tốt hơn, hoặc so sánh chất lượng cloud với local. Khi làm phần này sẽ giữ riêng prompt/tools local, chạy cùng bộ case và ghi đầy đủ log thay vì suy đoán.
