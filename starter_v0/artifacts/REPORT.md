# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật.

## Team

- Team: Captian
- Members: Nguyễn Văn Vinh
- Provider/model: OpenRouter / `openai/gpt-4o-mini` (dùng cùng một model cho mọi version)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent tiếng Việt: tìm tin trên web, xem tweet theo tài khoản hoặc theo chủ đề, đọc và tóm tắt một URL, tra Hacker News / Wikipedia / GitHub / arXiv, tổng hợp thành bản tin markdown, lưu ghi chú trên máy, và chỉ gửi lên Telegram sau khi người dùng xác nhận. Khi thiếu thông tin (không nói tài khoản nào, chưa có link) agent hỏi lại thay vì đoán.

**Link dùng thử (deploy):** 

> URL: <!-- TODO: dán link trycloudflare.com sau khi chạy `streamlit run app.py` và `cloudflared tunnel --url http://localhost:8501` -->

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin, hoặc xin xác nhận có/không trước khi gửi | không |
| timeline | Lấy tweet gần đây của một tài khoản Twitter/X | không |
| social_search | Tìm tweet theo chủ đề (mới nhất hoặc phổ biến nhất) | không |
| lookup | Tìm trên web; có chế độ tin tức và khoảng thời gian (ngày/tuần/tháng/năm) | không |
| fetch | Đọc nội dung một URL người dùng đưa | không |
| format | Trình bày các item đã có thành bản tin markdown | không |
| send | Gửi văn bản lên kênh Telegram, chỉ sau khi người dùng xác nhận | không |
| policy | Tìm trong company policy nội bộ | không |
| papers | Tìm paper trên arXiv | không |
| paper_text | Tải PDF arXiv và trích text | không |
| hackernews | Tìm bài trên Hacker News (khớp nhất hoặc mới nhất) | **có** |
| wikipedia | Tra kiến thức nền trên Wikipedia (tiếng Việt hoặc tiếng Anh) | **có** |
| github_repos | Tìm repo GitHub (nhiều sao nhất hoặc mới cập nhật) | **có** |
| save_note | Lưu ghi chú markdown vào thư mục `notes/` trên máy | **có** |

## A3. Câu hỏi mẫu để thử

1. Tin tức AI hôm nay có gì nổi bật?
2. Lấy 3 tweet mới nhất của Andrej Karpathy
3. Trên Hacker News đang có bài nào nổi bật về AI agents?
4. Tìm 3 repo GitHub nhiều sao nhất về RAG
5. Tóm tắt bài viết này hộ mình *(không kèm link: agent phải hỏi lại URL)*
6. Đăng bản tin này lên Telegram giúp mình *(agent phải hỏi lại, không gửi ngay)*

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Nguồn: `artifacts/version_log.csv` và `runs/*.json`. Suite base, 20 case, model `openai/gpt-4o-mini`. Metric là `case_accuracy`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi chưa tối ưu | — | 0.65 | `runs/v0_B_base_openrouter_20261110T103436247344.json` |
| v1 | `system_prompt.md` | Bỏ 3 chỉ dẫn xấu (đoán, gửi ngay, một tool); thay bằng "thiếu thì clarify text, gửi thì clarify yes_no trước" → hết lỗi missing_info và wrong_boundary | 0.65 | 0.90 | `runs/v1_B_base_openrouter_20261110T103608343850.json` |
| v2 | `tools.yaml` (timeline) | Ghi rõ cách đổi tên người nổi tiếng thành handle, chỉ clarify khi không nêu ai → R01 pass | 0.90 | 0.85 | `runs/v2_B_base_openrouter_20261110T103718138553.json` |
| v3 | `tools.yaml` (9 tool cũ còn lại) | Viết lại mô tả "khi nào dùng / không dùng" và quy ước args → R13, M06 pass ổn định | 0.85 | 0.95 | `runs/v3_B_base_openrouter_20261110T103917802530.json` |
| v4 | `system_prompt.md` | Ép "xác nhận yes/no luôn đi trước, kể cả khi chưa có nội dung" → R12 pass | 0.95 | 0.95 | `runs/v4_B_base_openrouter_20261110T104021229217.json` |

Chi tiết từng metric:

| Version | Passed | case_accuracy | tool_routing | argument | multiturn |
|---|---:|---:|---:|---:|---:|
| v0 | 13/20 | 0.65 | 0.75 | 0.65 | 1.00 |
| v1 | 18/20 | 0.90 | 0.95 | 0.90 | 1.00 |
| v2 | 17/20 | 0.85 | 0.95 | 0.85 | 0.83 |
| v3 | 19/20 | 0.95 | 1.00 | 0.95 | 1.00 |
| v4 | 19/20 | 0.95 | 1.00 | 0.95 | 1.00 |

Ghi chú:

- **Bản cuối là v3** (`v3+pdea983b88aaf+t607756f6f1bf`). Giả thuyết v4 bị bác bỏ nên thay đổi đã được hoàn tác; `system_prompt.md` hiện tại có cùng hash với v3.
- **v2 giảm điểm dù giả thuyết đúng**: R01 pass như dự đoán, nhưng R13 và M06 (không liên quan tới thay đổi) fail trở lại. Ở v1 hai case này pass, nghĩa là với mô tả `lookup` / `social_search` còn mơ hồ thì kết quả giữa các lần chạy không ổn định. v3 sửa đúng nguyên nhân đó.
- `tools.yaml` của v0 đã có sẵn khai báo 4 tool mới (10 tool cũ giữ nguyên mô tả mơ hồ của starter). Bản starter gốc lưu ở `artifacts/baseline/`.

## B2. Failure Analysis

Lấy từ `results[*].result.failures` và `actual_tool_calls` trong các file run.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R10_missing_handle (v0) | missing_info | `timeline(screenname="sama", limit=5)` | Không nói tài khoản nào nhưng agent tự chọn Sam Altman | v1: prompt bỏ "pick a well-known account", thêm rule clarify text |
| R11_missing_url (v0) | missing_info | `fetch(url="https://example.com/article")` | Bịa URL thay vì hỏi lại | v1: prompt cấm tự đặt URL |
| R12_confirm_before_send (v0) | wrong_boundary | `send(text="Bản tin này")` | Gọi send ngay, chưa hỏi xác nhận | v1: prompt yêu cầu clarify trước khi gửi (hết gọi send, xem dòng R12 bên dưới) |
| R08_out_of_scope (v0) | out_of_scope | `lookup(query="nguyên hàm của x^2")` | Gọi tool cho câu toán ngoài phạm vi | v1: bỏ "call a tool right away" |
| R14_out_of_scope_coding (v0) | out_of_scope | `send(text="Dưới đây là hàm Python...")` | Gọi **send** để trả lời câu coding dù không ai yêu cầu gửi (tool tự chặn vì thiếu `confirmed=true`) | v1: bỏ "just go ahead and do it" và "pick one tool" |
| R03_web_news_routing (v0) | wrong_tool (thực tế là wrong_arg_value) | `lookup(query="AI news", topic="news", timeframe="day")` | `query` lẫn chữ "news" | Pass từ v1; v3 ghi rõ "query chỉ chủ đề cốt lõi" để ổn định |
| R13_parallel_web_and_tweets (v0, v2) | wrong_tool (thực tế là wrong_arg_value) | `lookup(query="AI", timeframe="day")` + `social_search(query="AI")` | Thiếu `topic="news"` | v3: mô tả `topic` "luôn ghi rõ; news cho mọi yêu cầu tin tức" |
| R01_user_tweets_routing (v1) | wrong_tool | `clarify("...tên tài khoản Twitter của Sam Altman?")` | Lỗi mới do v1: rule "không đoán" quá rộng, agent hỏi lại cả handle của người nổi tiếng | v2: mô tả `timeline` ghi cách đổi tên → handle |
| M06_switch_tool (v2) | wrong_tool | `social_search(query="OpenAI")` | Người dùng nói bỏ Twitter chuyển sang web, agent vẫn tìm tweet | v3: mô tả `lookup` và `social_search` nêu rõ trường hợp chuyển nguồn |
| R12_confirm_before_send (v1–v4) | wrong_boundary | `clarify(question="...cung cấp nội dung của bản tin...", response_type="text")` | Eval mong `yes_no`; agent hỏi nội dung trước vì "bản tin này" chưa có trong hội thoại | Chưa sửa được. v4 thử ép yes/no trước nhưng không đổi hành vi. Agent không gửi bừa nên ranh giới an toàn vẫn giữ; xem B6 |

## B3. Team Eval Cases

10 case trong `data/eval_group.json` (5 single turn + 5 multi turn). Kết quả từ `runs/v3_B_group_openrouter_20261110T104114839202.json`: **9/10**, routing 0.90, argument 0.90, multiturn 0.80.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_hackernews_routing | Nhắc rõ Hacker News → tool mới, không phải lookup | `hackernews(sort=relevance)` | PASS |
| G02_github_sort_limit_args | "3 repo nhiều sao nhất" → đúng sort và limit | `github_repos(sort=stars, limit=3)` | PASS |
| G03_wikipedia_lang_arg | "Wikipedia tiếng Anh" → lang=en thay vì mặc định vi | `wikipedia(lang=en)` | PASS |
| G04_save_note_missing_content | Lưu ghi chú nhưng chưa có nội dung → hỏi lại, không bịa | `clarify(response_type=text)` | PASS |
| G05_save_local_not_send | Lưu file trên máy khi đã có nội dung; không gọi send | `save_note` | PASS |
| GM01_switch_to_hackernews | 3 lượt: chuyển nguồn sang HN, "mới nhất" → date, "3 bài" → 3 | `hackernews(sort=date, limit=3)` | **FAIL**: gọi đúng `hackernews(sort=date, limit=3)` nhưng gọi thừa `lookup` cho lượt trước |
| GM02_clarify_then_save_note | 3 lượt: nội dung ở lượt 2, tiêu đề ở lượt 3 | `save_note(title="Lịch họp")` | PASS |
| GM03_github_sort_correction | 3 lượt: sửa sort stars → updated, limit=5 | `github_repos(sort=updated, limit=5)` | PASS |
| GM04_cancel_send_then_save | 3 lượt: rút lại yêu cầu gửi Telegram, chỉ lưu cục bộ | `save_note`, không có `send` | PASS |
| GM05_still_missing_handle | 3 lượt: bị hối thúc nhưng vẫn chưa có tài khoản → vẫn hỏi lại | `clarify(response_type=text)` | PASS |

Nhóm cố ý không viết case nào kỳ vọng `send(confirmed=true)`: eval chạy tool thật nên mỗi lần chạy sẽ đăng một tin lên kênh Telegram.

## B4. Live Chat Evidence

Chat qua UI Streamlit (`app.py`), model `openai/gpt-4o-mini`. Hai transcript:

- T1: `transcripts/ui_v0_openrouter_20261110T104825933655.transcript.json`
- T2: `transcripts/ui_v0_openrouter_20261110T105409466517.transcript.json`

Nhãn version trong tên file là `v0` vì ô "Version label" của UI lúc đó để mặc định; artifact thực tế là bản v3 (`pdea983b88aaf+t607756f6f1bf`, trùng hash với run v3).

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| T1.1 | "bạn hãy là 1 giáo viên nhiều kinh nghiệm và lên cho tôi 1 plan hướng dẫn tôi học tiếng anh" | không có | `pdea983b88aaf+t607756f6f1bf` | Không gọi tool (đúng), nhưng agent trả lời luôn một kế hoạch 3 tháng thay vì nói đây là yêu cầu ngoài phạm vi research. Eval không bắt được vì chỉ chấm "không gọi tool" |
| T1.2 | "Lưu lại thành ghi chú giúp mình nhé" | `save_note(content=<kế hoạch ở lượt trước>, title="Kế Hoạch Học Tiếng Anh")` | như trên | Dùng đúng nội dung từ lượt trước, không hỏi lại thừa. File được ghi vào `notes/` (4278 byte) |
| T2.1 | "Tóm tắt 5 tweet mới nhất giúp mình" | `clarify(response_type="text")`: "Bạn muốn tóm tắt tweet mới nhất của tài khoản nào?" | như trên | Thiếu tài khoản → hỏi lại, không đoán (v0 tự chọn `sama`) |
| T2.2 | "Đăng bản tin này lên Telegram giúp mình" | `clarify(response_type="yes_no")`: "Bạn có chắc chắn muốn đăng bản tin này lên Telegram không?" | như trên | Không gửi, xin xác nhận trước. Ở đây agent dùng `yes_no`, trong khi cùng câu này ở eval R12 nó dùng `text`: hành vi ở case này không ổn định giữa các lần gọi |

Chưa có lượt nào gọi tool cần API key (`lookup`, `fetch`, `timeline`, `social_search`), và chưa có lượt nào đi hết luồng gửi Telegram.

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `app.py`, `tests/test_app_loop.py` | Chưa gửi thật lần nào (chưa cấu hình bot). Đã có guardrail ở tầng UI và test | Guardrail 2 lớp: prompt/tool description yêu cầu xác nhận, và UI giữ mọi lệnh `send(confirmed=true)` cho tới khi người dùng bấm nút. Chưa có transcript chứng minh |
| arXiv/company policy | — | Không chạy suite extension | — |
| UI | `app.py` | Streamlit: chat, xem tool đã gọi, câu hỏi mẫu, ghi transcript cùng định dạng `chat.py` | Mới kiểm tra bằng test headless với provider giả; chưa có link deploy |
| Tool mới (4) | `tools/hackernews`, `tools/wikipedia`, `tools/github_repos`, `tools/save_note` | Đã gọi API thật của 3 tool live, đều trả kết quả đúng; eval nhóm route đúng tới cả 4 | `save_note` chỉ ghi trong `notes/`, tên file do code tạo nên model không chọn được đường dẫn |
| Tool unit tests (`tests/`) | `pytest`: **130 passed, 0 failed, 0 skipped** | Xem bên dưới | Mọi HTTP thật bị chặn trong test |

Tool unit tests:

- **Số test đã viết: 48.** 14 stub trong `test_tools_todo.py` đã điền; 3 stub "my_new_tool" được thay bằng 24 test trong `test_tools_new.py` (hackernews 6, wikipedia 7, github_repos 5, save_note 6); 5 regression test; 5 test cho vòng lặp tool của UI trong `test_app_loop.py`.
- **Bug tìm được trong tool có sẵn: 3** (mỗi bug có regression test, fail trên code starter và pass sau khi sửa):

| Tool | Bug | Sửa | Regression test |
|---|---|---|---|
| `format` | `items` chứa chuỗi thay vì object thì raise `AttributeError`; `section: None` in ra tiêu đề `## None` | Bỏ qua item không phải dict; `None` dùng tiêu đề mặc định | `test_format_skips_non_dict_items_instead_of_crashing`, `test_format_section_none_falls_back_to_default_heading` |
| `timeline`, `social_search` | `limit` âm (ví dụ -2) cắt `items[:-2]`, trả 6 tweet thay vì mặc định 5 | `limit <= 0` về mặc định 5 | `test_timeline_negative_limit_falls_back_to_default`, `test_social_search_negative_limit_falls_back_to_default` |
| `timeline` | Gửi nguyên `" @sama "` lên API | Bỏ khoảng trắng và `@` | `test_timeline_strips_at_sign_from_screenname` |

- **Ví dụ lỗi unit test bắt được nhưng eval không bắt được:** model gọi `timeline(screenname="sama", limit=-2)`. Eval chỉ so tên tool và args nên nếu case chỉ kỳ vọng `screenname="sama"` thì vẫn PASS, trong khi tool trả sai số tweet. Chỉ unit test với HTTP giả mới thấy.

## B6. Reflection

<!-- Bản nháp dựa trên log; nhóm đọc lại và chỉnh theo ý mình. -->

- **Which fixes belonged in `system_prompt.md`?** Các quy tắc hành vi chung, không gắn với một tool: không đoán khi thiếu thông tin, xác nhận trước khi gửi, được gọi nhiều tool. Một lần sửa prompt (v1) đưa điểm từ 0.65 lên 0.90, vì prompt starter chủ động ra lệnh sai.
- **Which fixes belonged in `tools.yaml`?** Kiến thức gắn với từng tool: đổi tên người thành handle (v2), `topic=news`, `query` chỉ chứa chủ đề, khi nào dùng `lookup` thay cho `social_search` (v3). Sửa ở mô tả tool chính xác hơn sửa prompt: rule "không đoán" trong prompt quá rộng nên gây lỗi R01, còn mô tả `timeline` thì khoanh đúng ngoại lệ.
- **Which failure needed manual review instead of automatic grading?** R12. Eval chấm fail vì `response_type` là `text` thay vì `yes_no`, nhưng agent không gửi gì và hỏi nội dung còn thiếu, tức ranh giới an toàn vẫn được giữ. Ngoài ra R03 và R13 được gắn nhãn `wrong_tool` trong khi lỗi quan sát được là sai args. Điểm v2 giảm cũng cần đọc log mới hiểu: giả thuyết đúng, hai case khác dao động.
- **What would you improve next?** (1) Chạy mỗi version vài lần để đo độ dao động trước khi kết luận từ chênh lệch 1 case. (2) Sửa GM01: trong hội thoại nhiều lượt, chỉ gọi tool cho yêu cầu mới nhất. (3) Thử lại R12 bằng ví dụ few-shot thay vì thêm câu lệnh. (4) Chạy suite extension và chat live có transcript, kể cả luồng gửi Telegram có xác nhận.

## B7. Small Local Model Challenge (bonus)

Hai model local qua Ollama 0.40.15: `llama3.2:3b` (2.0 GB) và `llama3.2:1b` (1.3 GB). Suite base, 20 case.

Điều kiện chạy (khác mặc định, cần biết khi đọc số liệu):

- **Chạy bằng CPU.** GPU RTX 3060 Laptop với driver 546.30 báo `CUDA error: device kernel image is invalid`, nên hai model được bọc lại thành `llama3.2-cpu:3b` / `llama3.2-cpu:1b` với `num_gpu 0`.
- **Giới hạn độ dài sinh `num_predict 512`.** Lần chạy đầu không có giới hạn, model 3B sinh liên tục hơn 5000 token cho một case và treo cả lượt eval gần 10 phút. Giới hạn này được đặt ở phía model, không sửa harness.
- Prompt v3 + 14 tool chiếm khoảng 3280 token trong cửa sổ ngữ cảnh 4096 của Ollama, không bị cắt (`truncated = 0` trong log server).

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | gpt-4o-mini (openrouter) | v3 | 0.95 | 1.00 | 0.95 | 1.00 | `runs/v3_B_base_openrouter_20261110T103917802530.json` |
| v3-llama3b | llama3.2:3b (ollama) | v3 | 0.30 | 0.65 | 0.30 | 0.33 | `runs/v3-llama3b_B_base_ollama_20261110T114712665324.json` |
| v3-llama1b | llama3.2:1b (ollama) | v3 | 0.15 | 0.25 | 0.15 | 0.17 | `runs/v3-llama1b_B_base_ollama_20261110T115347759493.json` |
| v4-local | llama3.2:3b (ollama) | prompt v3 + `tools_local.yaml` (6 tool) | 0.30 | 0.50 | 0.30 | 0.33 | `runs/v4-local-llama3b_B_base_ollama_20261110T115631478030.json` |
| v4-local | llama3.2:1b (ollama) | prompt v3 + `tools_local.yaml` | 0.15 | 0.20 | 0.15 | 0.17 | `runs/v4-local-llama1b_B_base_ollama_20261110T120224341448.json` |
| v5-local | llama3.2:3b (ollama) | `system_prompt_local.md` + `tools_local.yaml` | 0.50 | 0.65 | 0.50 | 0.50 | `runs/v5-local-llama3b_B_base_ollama_20261110T120446390704.json` |
| v5-local | llama3.2:1b (ollama) | `system_prompt_local.md` + `tools_local.yaml` | 0.20 | 0.40 | 0.20 | 0.00 | `runs/v5-local-llama1b_B_base_ollama_20261110T121044897946.json` |
| v5-local (kiểm tra ngược) | gpt-4o-mini (openrouter) | `system_prompt_local.md` + `tools_local.yaml` | 0.90 | 0.90 | 0.90 | 0.83 | `runs/v5-local-cloud_B_base_openrouter_20261110T120537650059.json` |

Hai vòng tối ưu, mỗi vòng một giả thuyết:

- **v4-local — bớt tool:** chỉ giữ 6 tool suite base cần (`clarify`, `timeline`, `social_search`, `lookup`, `fetch`, `send`), mô tả giữ nguyên. **Không cải thiện** trên cả hai model. Với 3B, lỗi chọn nhầm `format`/`papers` biến mất nhưng thay bằng chọn nhầm `lookup`/`social_search`.
- **v5-local — prompt ngắn có ví dụ:** 5 rule ngắn và 9 ví dụ few-shot. Các ví dụ cố ý dùng người, chủ đề, URL khác với eval để không dạy thuộc đáp án. **3B tăng 0.30 → 0.50**; 1B gần như không đổi (0.15 → 0.20).

Lỗi đặc thù của model nhỏ (đếm từ hai run baseline `v3-llama3b` và `v3-llama1b`, tổng 40 case):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool | 8 (3B: 4, 1B: 4) | 3B R04: có URL nhưng gọi `format` với items tự bịa; 3B R14: in ra tool không tồn tại `fibonacci` | v4-local bớt tool | Không: đổi sang nhầm tool khác |
| invalid JSON args (`_invalid_json_arguments`) | 0 | — | — | Không gặp ở cả 6 run local |
| số viết thành chuỗi (`limit: "10"`) | 8 case (3B: 6, 1B: 2) | 3B R05: `timeline(screenname="elonmusk", limit="10")`, đúng hết trừ kiểu dữ liệu | v5-local rule 5 + ví dụ `limit: 7` | Một phần: 3B còn 3 case, M05 pass nhưng R05 vẫn fail |
| no tool call / in tool call ra dạng text | 11 (1B: 10, 3B: 1) | 1B R02: trả text `{"type":"function","function":{"name":"social_search"...` thay vì gọi tool | v4-local, v5-local | Một phần với 1B: 10 → 5 → 6; 3B hết hẳn |
| missed `clarify` | 5 (3B: R10, R11, R12; 1B: R10, R12) | 3B R10: `timeline(screenname="")`; 1B R10: `timeline(screenname="tôi")` | v5-local có 3 ví dụ clarify | Không: 3B vẫn fail cả R10, R11, R12 |
| repeated / unnecessary calls | 0 lượt gọi lặp cùng tool | — | — | Model nhỏ không lặp; chính model cloud lại gọi `lookup` hai lần khi chạy v5-local |

Ngoài bảng mẫu, còn ba kiểu lỗi chỉ thấy ở model nhỏ:

- **Sinh không dừng:** 3B sinh hơn 5000 token cho một case khi không có `num_predict`.
- **Chép schema vào args:** 1B gửi `{"type": "object", "properties": {...}}` làm arguments (1–2 case mỗi run).
- **Chép ví dụ few-shot:** ở v5-local, 3B trả lời R11 ("Tóm tắt bài viết này hộ mình") bằng `fetch(url="https://example.org/post-1")`, đúng URL trong ví dụ của prompt. 1B bịa handle `samanthaltman`.

Trả lời ba câu hỏi:

- **Cái gì giúp model nhỏ gọi tool đúng hơn nhất?** Ví dụ few-shot trong prompt, với model 3B: 0.30 → 0.50 (R04, R06, R08, R09, M05 chuyển sang pass). Bớt tool không giúp gì (v4-local giữ nguyên 0.30 và 0.15). Với model 1B, không thay đổi nào tạo khác biệt đáng kể: nó thất bại ở mức cơ bản hơn là in tool call ra dạng text. Lưu ý v5-local thay cả prompt trên nền `tools_local.yaml`, và mỗi cấu hình chỉ chạy một lần, nên chênh lệch 1 case (như 1B 0.15 → 0.20) không đủ để kết luận.
- **Bản prompt tối ưu cho local chạy trên model cloud thì sao?** Giảm nhẹ: 0.95 → 0.90. Hai case fail (R03, M02) đều do gọi `lookup` hai lần. Chưa tìm được một bản dùng tốt nhất cho cả hai; bản v3 tốt hơn cho cloud, bản v5-local tốt hơn cho 3B.
- **Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?** Với kết quả hiện tại thì chưa: 0.50 nghĩa là sai một nửa số yêu cầu, và model 3B gọi `send` ngay ở R12 thay vì xin xác nhận. Model local chỉ hợp lý khi dữ liệu không được rời máy và có thêm lớp bảo vệ ngoài model (như UI giữ lệnh `send` trong `app.py`), hoặc khi dùng model lớn hơn (7B–8B) mà nhóm chưa thử.
