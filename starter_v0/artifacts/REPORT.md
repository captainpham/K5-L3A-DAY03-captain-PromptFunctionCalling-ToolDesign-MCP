# Day 03 Lab v2 Report — Captain Research Agent

## Team

- Team: captain
- Members: Phạm Cát Tân - 2A202603678, Trần Minh Nhật - 2A202603684, Nguyễn Văn Vinh - 2A202603672
- Provider/model: OpenRouter / `openai/gpt-4o-mini`
- UI: Streamlit; chia sẻ demo từ máy cá nhân qua Cloudflare Tunnel.

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Captain Research Agent tìm thông tin trên web, Hacker News, Wikipedia, GitHub và arXiv; đọc URL, tra policy nội bộ và tổng hợp thành bản tin. Agent có thể loại URL trùng, lưu ghi chú markdown trên máy chủ, hỏi lại khi thiếu thông tin và yêu cầu xác nhận trước khi gửi Telegram.

**Link demo tạm:** https://impressive-lamp-bracelet-basics.trycloudflare.com

UI được host local trên máy cá nhân. Link chỉ hoạt động khi máy có mạng và cả Streamlit lẫn tunnel đang chạy; push GitHub không tự tạo server. Chạy `uv run python -m streamlit run app.py`, mở `http://localhost:8501`. Xem [hướng dẫn UI](../UI-README.md).

## A2. Tool agent có

Tổng cộng **15 tool**, gồm 10 tool starter và **5 tool nhóm thêm**.

| Tool | Chức năng | Nguồn / yêu cầu |
|---|---|---|
| clarify | Hỏi bổ sung thông tin hoặc xác nhận | Starter |
| lookup | Tìm web, lọc news và timeframe | Starter; Tavily key |
| fetch | Đọc một URL | Starter; Firecrawl key |
| timeline | Lấy bài đăng một tài khoản Twitter/X | Starter; RapidAPI key |
| social_search | Tìm bài đăng Twitter/X theo chủ đề | Starter; RapidAPI key |
| format | Định dạng item đã có thành markdown digest | Starter; local |
| policy | Tra policy markdown nội bộ | Starter; local |
| papers | Tìm paper arXiv | Starter |
| paper_text | Tải và trích text PDF arXiv | Starter |
| send | Gửi Telegram sau xác nhận | Starter; bot token/chat ID |
| deduplicate | Loại URL trùng, giữ item đầu tiên; cảnh báo item thiếu URL | Nhóm; local |
| hackernews | Tìm story trên Hacker News | Nhóm; branch nguyenvinh |
| wikipedia | Tra Wikipedia tiếng Việt/Anh | Nhóm; branch nguyenvinh |
| github_repos | Tìm repository công khai trên GitHub | Nhóm; branch nguyenvinh |
| save_note | Lưu markdown vào notes/ trên máy chủ | Nhóm; branch nguyenvinh |

Ba tool tìm kiếm mới không bắt buộc key; GitHub có thể dùng GITHUB_TOKEN tùy chọn. `notes/` được gitignore. Các log hiện có chưa lấy tweet thật thành công do thiếu RAPIDAPI_KEY; chưa có bằng chứng gửi Telegram thật.

## A3. Câu hỏi mẫu để thử

1. Tìm 3 tin AI hôm nay trên web.
2. Tóm tắt https://www.python.org/about/
3. Tìm 2 story mới nhất trên Hacker News về AI agents.
4. Tìm 2 repository GitHub nhiều sao nhất với từ khóa llm agent framework.
5. Loại URL trùng: `[{"title":"A","url":"https://example.com/a"},{"title":"B","url":"https://example.com/a"}]`.

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Baseline và v1–v3 dùng cùng base suite 20 case, không sửa nội dung eval_base.json. Mỗi vòng tập trung một giả thuyết. Metric trước/sau là `summary.case_accuracy`, đo tool/arguments, không phải điểm chất lượng bài tổng hợp.

| Version / suite | Thay đổi | Giả thuyết | Trước | Sau | Bằng chứng |
|---|---|---|---:|---:|---|
| v0 / base | baseline | Đo chất lượng prompt và tool ban đầu | N/A | 65.0% | [JSON](../runs/v0_B_base_openrouter_20261110T102626808616.json) |
| v1 / base | system_prompt.md | Yêu cầu gọi clarify khi thiếu nguồn sẽ giảm lỗi missing tool call clarify | 65.0% | 90.0% | [JSON](../runs/v1_B_base_openrouter_20261110T104401190528.json) |
| v2 / base | system_prompt.md | Làm rõ thứ tự ưu tiên xác nhận gửi sẽ sửa R12 mà giữ các hành vi của v1 | 90.0% | 90.0% | [JSON](../runs/v2_B_base_openrouter_20261110T112443039224.json) |
| v3 / base | system_prompt.md | Làm rõ routing tin web theo ngữ cảnh sẽ sửa R13 và M06 | 90.0% | 100.0% | [JSON](../runs/v3_B_base_openrouter_20261110T113508701978.json) |
| v3-deduplicate / group | tools.yaml + tools/deduplicate + run_eval.py | Mô tả tool loại URL trùng giúp agent dùng dữ liệu đã có thay vì tìm kiếm hoặc tự loại input trước khi gọi tool | N/A | 100.0% | [JSON](../runs/v3-deduplicate_B_group_openrouter_20261110T114020068953.json) |
| v4-integrated / base | tools.yaml + tools + tests + eval_group.json | Tool declaration riêng biệt cho phép mở rộng nguồn mà giữ routing base; cần đo lại ảnh hưởng tới policy extension | 100.0% | 100.0% | [JSON](../runs/v4-integrated_B_base_openrouter_20261110T183128554593.json) |

- **v0:** 13/20 pass. Prompt starter khuyến khích đoán nguồn, gửi ngay và làm một bước.
- **v1:** sửa quy tắc thiếu tài khoản/URL thành hỏi lại; 18/20 pass, R10 và R11 chuyển sang pass. Chưa đủ bằng chứng để gán toàn bộ cải thiện khác cho cùng quy tắc chỉ từ một lần chạy.
- **v2:** làm rõ ưu tiên xác nhận yes/no trước khi gửi; vẫn 18/20. R12 pass nhưng M06 chuyển sang fail; tổng điểm không tăng.
- **v3:** làm rõ routing nguồn và giữ ngữ cảnh khi chuyển Twitter sang web, khai báo topic=news; 20/20 pass, gồm R13 và M06.
- **v3-deduplicate:** thêm tool loại trùng, sửa lỗi bộ chấm; group mở rộng 11/11. Không coi bộ group 10 và 11 case là cùng dataset.
- **v4-integrated:** thêm bốn tool thành viên và test, giữ prompt tại thời điểm tích hợp; base 20/20, group 15/15, extension 4/10.

### Ba suite sau tích hợp

| Suite | Pass / tổng | Case accuracy | Routing | Arguments | Multi-turn | Provider errors | Log |
|---|---:|---:|---:|---:|---:|---:|---|
| base | 20/20 | 100.0% | 100.0% | 100.0% | 100.0% | 0 | [JSON](../runs/v4-integrated_B_base_openrouter_20261110T183128554593.json) |
| group | 15/15 | 100.0% | 100.0% | 100.0% | 100.0% | 0 | [JSON](../runs/v4-integrated_B_group_openrouter_20261110T183125214532.json) |
| extension | 4/10 | 40.0% | 90.0% | 40.0% | N/A | 0 | [JSON](../runs/v4-integrated_B_extension_openrouter_20261110T183112461397.json) |

Định danh từng run được lưu tại [version_log.csv](version_log.csv) và JSON gốc. Run v4-integrated dùng prompt hash `71f5408b5109681ef3970eabe89fc5d19574b11a48a7a1c416b7942cb69b3379` và tools hash `ba63774d1665f2d994652ae4fa985eb377be2cc6ee9659541740688b792f0450`.

**Thay đổi sau eval:** thêm quy tắc trả lời theo ngôn ngữ câu hỏi. Prompt hiện tại có hash `62ad0e91d9637cd15ff5279621167b9eb484dd267733dae4e181f31d8773a86c`; tools hash `ba63774d1665f2d994652ae4fa985eb377be2cc6ee9659541740688b792f0450`. Chưa chạy lại ba suite với prompt mới, nên không gán điểm v4-integrated cho toàn bộ cấu hình hiện tại. B4 có một quan sát live tiếng Việt sau sửa; chưa có bài kiểm chứng riêng cho chuyển qua lại Việt–Anh hoặc yêu cầu ghi đè ngôn ngữ.

CSV: [base](../analysis/base_runs.csv), [group](../analysis/group_runs.csv), [extension](../analysis/extension_runs.csv). Mỗi CSV chứa nhiều lần chạy; lọc run_id để so sánh đúng run. JSON gốc được giữ để truy vết.

## B2. Failure Analysis

Đọc observed_mismatch, failures và actual_tool_calls. Failure_type của dataset mô tả mục tiêu case, không luôn trùng nguyên nhân thực tế: tool có thể đúng nhưng argument sai.

| Case / version | Lỗi quan sát | Tool thực tế | Điều chỉnh / nguyên nhân | Kết quả |
|---|---|---|---|---|
| R10 / v0 | Thiếu clarify, thừa timeline | timeline, tự chọn sama | v1 hỏi tài khoản khi thiếu thay vì đoán | Pass từ v1 |
| R11 / v0 | Thiếu clarify, thừa fetch | fetch, tự chọn URL | v1 cấm bịa URL, kiểm tra ngữ cảnh rồi hỏi | Pass từ v1 |
| R08, R14 / v0 | Expected no tool call | send | Dùng công cụ gửi làm kênh trả lời câu toán/code | Pass các lần v1–v4 đã lưu; chưa xác định riêng nguyên nhân cải thiện |
| R12 / v1 | Thiếu clarify, thừa send | send | v2 yêu cầu xác nhận yes/no trước gửi | Pass v2, v3, v4-integrated |
| R13 / v1–v2 | Thiếu topic=news | lookup + social_search | v3 yêu cầu news tường minh | Pass v3 và v4-integrated |
| M06 / v2 | Thiếu lookup, thừa social_search | social_search | v3 ưu tiên nguồn mới nhất trong hội thoại | Pass v3 và v4-integrated |
| E01_company_source_policy / v4-integrated | policy_area: expected 'source_citation', got 'all' | policy | Chưa sửa: policy_area / lookup | FAIL |
| E02_company_data_privacy / v4-integrated | policy_area: expected 'data_privacy', got 'external_publishing' | policy | Chưa sửa: policy_area / lookup | FAIL |
| E03_company_telegram_approval / v4-integrated | policy_area: expected 'external_publishing', got None | policy | Chưa sửa: policy_area / lookup | FAIL |
| E06_briefing_live_plus_style / v4-integrated | missing tool call lookup; policy_area: expected 'source_citation', got None | policy | Chưa sửa: policy_area / lookup | FAIL |
| E07_paper_scan_template_plus_arxiv / v4-integrated | policy_area: expected 'source_citation', got None | papers, policy | Chưa sửa: policy_area / lookup | FAIL |
| E08_specific_url_not_arxiv / v4-integrated | policy_area: expected 'ai_research', got None | fetch, policy | Chưa sửa: policy_area / lookup | FAIL |

Extension giảm **7/10 ở v3 → 4/10 sau tích hợp**. Một lần chạy chưa đủ kết luận thêm tool là nguyên nhân duy nhất. Mô tả policy còn chung chung, chưa ánh xạ chủ đề rõ sang policy_area. E06 còn có yêu cầu tuần tự “kiểm tra policy trước”, trong khi evaluator kỳ vọng cả lookup và policy trong cùng lượt chọn tool; cần review ngữ nghĩa task cùng log.

**Tách routing khỏi thực thi:** v4-integrated có 8 lần gọi Twitter trong base và 4 trong group trả `Missing RAPIDAPI_KEY env var`. Case vẫn có thể pass vì bộ chấm chỉ kiểm tra tool/arguments. Không coi điểm 100% là 100% tác vụ nghiên cứu thành công.

**Lỗi bộ chấm đã sửa:** normalize_value dùng sorted() trên list dictionary gây `TypeError: '<' not supported between instances of 'dict' and 'dict'`, bị ghi thành provider_error. Đã chuẩn hóa dictionary đệ quy và dùng JSON làm khóa sắp xếp; giữ quy ước không xét thứ tự list, vẫn kiểm tra số item lặp. Có 3 test hồi quy ở tests/test_eval_args.py.

[Run trước sửa](../runs/v3-deduplicate_B_group_openrouter_20261110T113938443315.json) có 10 measured, 1 provider_error. Summary 100% chỉ tính measured cases, không phải 11/11 pass. [Run sau sửa](../runs/v3-deduplicate_B_group_openrouter_20261110T114020068953.json) mới có 11/11, 0 provider_error.

## B3. Team Eval Cases

[Dataset nhóm](../data/eval_group.json) có **15 case: 10 single-turn và 5 multi-turn**. Ban đầu có 5 single + 5 multi; sau đó thêm deduplicate và bốn case tool thành viên. Mỗi case có ID, phase B, query/turns, failure_type, expect và metadata.what_it_tests. Multi-turn chỉ chấm hành động cho lượt cuối, dùng các lượt trước làm ngữ cảnh.

| Case ID | Loại | Hành vi được kiểm tra | Tool / arguments kỳ vọng | v4-integrated |
|---|---|---|---|---|
| CAP_S01_account_count | Single | Bỏ dấu @ khỏi handle và giữ đúng số lượng bài người dùng yêu cầu. | timeline {"screenname": "NASA", "limit": 3} | PASS |
| CAP_S02_weekly_web_news | Single | Tách chủ đề tìm kiếm khỏi bộ lọc news/week và giữ số lượng kết quả. | lookup {"query": "năng lượng tái tạo", "topic": "news", "timeframe": "week", "max_results": 4} | PASS |
| CAP_S03_missing_article_url | Single | Hỏi URL khi người dùng chưa cung cấp bài viết, không tự đoán nguồn. | clarify {"response_type": "text"} | PASS |
| CAP_S04_capabilities_without_tools | Single | Giới thiệu khả năng trực tiếp, không gọi công cụ khi chưa có yêu cầu thực hiện nghiên cứu. | no_tool | PASS |
| CAP_S05_popular_social_posts | Single | Chọn tìm kiếm bài đăng theo chủ đề, phân biệt Top với Latest và timeline tài khoản. | social_search {"query": "climate tech", "search_type": "Top", "limit": 4} | PASS |
| CAP_M01_supply_missing_handle | Multi | Dùng tài khoản vừa được bổ sung và giữ số lượng từ lượt trước, không hỏi lại. | timeline {"screenname": "NASA", "limit": 4} | PASS |
| CAP_M02_correct_count | Multi | Ưu tiên số lượng được sửa ở lượt cuối và giữ nguyên tài khoản đã xác định. | timeline {"screenname": "ESA", "limit": 2} | PASS |
| CAP_M03_switch_social_to_web | Multi | Tôn trọng việc chuyển nguồn từ Twitter sang web, giữ bộ lọc tin hôm nay ở lượt bổ sung chủ đề. | lookup {"query": "fusion energy", "topic": "news", "timeframe": "day", "max_results": 3} | PASS |
| CAP_M04_change_topic_keep_timeframe | Multi | Chỉ thay chủ đề được sửa, giữ nguồn tin web cùng timeframe và số lượng từ ngữ cảnh. | lookup {"query": "wind power", "topic": "news", "timeframe": "month", "max_results": 3} | PASS |
| CAP_M05_supply_missing_url | Multi | Tiếp tục yêu cầu đọc bài bằng URL vừa được bổ sung, không tìm nguồn khác hoặc hỏi lại. | fetch {"url": "https://www.python.org/about/"} | PASS |
| CAP_S06_deduplicate_collected_items | Single | Chọn tool mới để loại URL trùng từ dữ liệu đã có, truyền toàn bộ input gồm cả bản trùng thay vì tự loại trước hoặc gọi tìm kiếm. | deduplicate items=<original list including duplicates> | PASS |
| CAP_S07_hackernews_recent | Single | Chọn Hacker News thay vì tìm web chung; dùng sort=date và đúng số lượng. | hackernews {"query": "AI agents", "sort": "date", "limit": 2} | PASS |
| CAP_S08_wikipedia_english | Single | Chọn Wikipedia cho kiến thức nền khi nguồn được chỉ rõ, truyền ngôn ngữ en. | wikipedia {"query": "Python (programming language)", "lang": "en", "limit": 1} | PASS |
| CAP_S09_github_public_repos | Single | Chọn tìm repo GitHub thay vì paper/web chung, sắp xếp theo stars. | github_repos {"query": "llm agent framework", "sort": "stars", "limit": 2} | PASS |
| CAP_S10_save_local_note | Single | Phân biệt lưu local và gửi ra ngoài; dùng nguyên nội dung có sẵn, không gọi send. | save_note {"title": "Captain integration check", "content": "Tool integration verification note."} | PASS |

Các case yêu cầu query khớp từ khóa đã ghi rõ từ khóa trong input. Eval chấm routing/arguments; unit test kiểm tra code và nhánh lỗi. Không chép ID hoặc đáp án từng case vào system prompt.

## B4. Live Chat Evidence

Model thật: OpenRouter / openai/gpt-4o-mini. Transcript lưu từng lượt, arguments, kết quả tool, trạng thái và hash. Phiên CLI dưới đây có **3 lượt liên tiếp**, đáp ứng yêu cầu tối thiểu.

| Phiên / lượt | Yêu cầu | Tool calls | Quan sát / kết quả |
|---|---|---|---|
| [CLI](../transcripts/v3-deduplicate_openrouter_20261110T120635116373.transcript.json) / 1 | Tóm tắt bài viết này giúp mình | Không gọi tool | Hỏi URL bằng văn bản; đúng mục đích hỏi lại nhưng chưa gọi clarify như hợp đồng eval |
| Cùng phiên / 2 | https://www.python.org/about/ | fetch | Đọc URL vừa bổ sung và tóm tắt bằng tiếng Việt, không báo lỗi tool |
| Cùng phiên / 3 | Loại hai item trùng https://example.com/a | deduplicate | Truyền đủ cả hai item, giữ A và loại B trùng URL |

Quan sát bổ sung cần review thủ công:

- [Tìm tin rồi đọc bài](../transcripts/v3-deduplicate_openrouter_20261110T120434764824.transcript.json): lookup trả ba bài; câu “Tóm tắt bài viết này” khiến agent fetch bài đầu tiên. URL có trong lịch sử nhưng tham chiếu giữa ba bài mơ hồ; nên hỏi chọn bài. Không coi đây là bịa URL, cũng không coi là hành vi hoàn hảo.
- [UI trước sửa ngôn ngữ](../transcripts/ui_v3-deduplicate_openrouter_01b6d177198a411d95c54080de1f47d5.transcript.json): hỏi tiếng Việt về repo ConVL, trả lời tiếng Anh.
- [UI sau sửa ngôn ngữ](../transcripts/ui_v3-deduplicate_openrouter_fe4a54c71ecf431abd7afadc76820b3a.transcript.json): hỏi tiếng Việt về ConVL, gọi fetch và trả lời tiếng Việt; prompt_hash trùng file hiện tại. Đây là quan sát một trường hợp, chưa thay cho kiểm chứng đầy đủ Việt–Anh.
- UI vẫn ghi nhãn v3-deduplicate theo cấu hình app; hash mới xác định chính xác nội dung prompt/tools. Routing eval không chấm độ chính xác của phần tóm tắt cuối.

## B5. Bonus Evidence và kiểm chứng tool

| Hạng mục | Bằng chứng | Kết quả | Giới hạn |
|---|---|---|---|
| UI Streamlit | [app.py](../app.py), [test_app.py](../tests/test_app.py), [hướng dẫn](../UI-README.md), transcript B4 | Chat, lịch sử, xem tool, lưu/tải JSON; 3 test UI pass; đã kiểm tra HTTP 200 lúc dựng UI | Link tunnel tạm, dùng credit máy chủ; chưa có test hình ảnh browser tự động |
| Unit/contract/UI tests | tests/; `uv run python -m pytest -q` | 149 pass, 0 failed, 0 skipped | Offline, mock HTTP; không tự chứng minh dịch vụ live hoạt động |
| Bốn tool thành viên | [smoke script](../scripts/smoke_team_tools.py), [kết quả live](../analysis/live_tools_20261110T113042Z.json) | Hacker News, Wikipedia, GitHub trả item có URL; save_note tạo file đúng và được đọc lại; 4/4 pass | Một happy path mỗi tool; API công khai có hạn mức |
| arXiv / policy | Run extension ở B1 | E04, E05, E09, E10 pass; 6 case policy/kết hợp fail | E09 là đọc hai URL; không coi đã hoàn thiện extension |
| Gửi Telegram | tests/test_tools_examples.py, tests/test_tools_todo.py; R12 | Guardrail và POST được kiểm tra bằng mock; R12 pass | Chưa gửi Telegram thật/chưa có transcript xác nhận rồi gửi; không nhận bonus action hoàn chỉnh |

### Unit test và tool mới

- `deduplicate`: **14 trường hợp** trong tests/test_deduplicate.py, thêm 3 trong tests/test_tools_todo.py. Kiểm tra giữ item đầu tiên/thứ tự/metadata, không sửa input, empty/null input, URL thiếu/khác nhau, input sai kiểu và warnings theo vị trí input.
- `hackernews`, `wikipedia`, `github_repos`, `save_note`: **24 trường hợp** trong tests/test_tools_new.py; mỗi tool ít nhất 3 test, gồm happy path, input không hợp lệ và lỗi. HTTP được mock; kiểm tra cả request và output. save_note kiểm tra nội dung, đường dẫn an toàn, giới hạn độ dài và lỗi thư mục.
- tests/test_tools_todo.py: 17 stub đã được thay bằng **18 trường hợp** (Top và Latest tạo hai trường hợp). Policy test dùng tài liệu tạm và kiểm tra instruction được tách khỏi facts.
- tests/test_eval_args.py: **3 test** hồi quy cho list dictionary, phát hiện URL thay đổi và item lặp bị mất.
- tests/test_app.py: **3 test** cho hỏi lại/giữ lịch sử/lưu transcript, reset phiên và lỗi provider không lộ nội dung exception.
- Phần còn lại: **80 contract test và 7 example test**. Tổng cộng **149**.

Ví dụ unit test kiểm tra điều eval routing không đo: item thiếu URL phải được giữ riêng và có warnings; URL sai kiểu phải trả error dict. Một tool call đúng tên không chứng minh các nhánh code này đúng. Đợt này sửa **1 lỗi bộ chấm**, không tuyên bố đã sửa lỗi trong tool starter khi chưa có bằng chứng.

### Nguồn tích hợp

Giữ prompt/UI/bằng chứng của captain; không merge nguyên prompt/report thành viên. Lấy bốn tool và unit test từ branch `nguyenvinh`, commit `5b5054e8da21eb63c26450acd7cf94429314858d`. Tên branch là định danh nguồn Git; tên thành viên giữ theo thông tin nhóm cung cấp.

Từ branch `03684-tranminhnhat`, commit `babfe1bf26134f59ea9db8a642eb22d59a6c5210`, chọn test URL có khoảng trắng và container sai kiểu. Không đăng ký deduplicate_sources thứ hai vì trùng chức năng và khác quy ước thiếu URL. Tool hiện tại giữ item thiếu URL riêng, trả warnings kèm vị trí input.

Chỉ thêm khai báo tool mới vào YAML/registry, không ghi đè mô tả tool cũ. GITHUB_TOKEN được xóa trong fixture test, chỉ dùng token giả khi kiểm tra header. `.env`, API key và notes/ không đưa vào bài nộp.

## B6. Reflection

**Thuộc system prompt:** hỏi lại thay vì đoán, xác nhận trước khi gửi, ưu tiên nguồn mới nhất, giữ timeframe và chọn ngôn ngữ trả lời. Đây là hành vi chung xuyên suốt nhiều tool.

**Thuộc tools.yaml:** mô tả khi dùng/không dùng, enum, convention arguments và output. Với extension, cần làm rõ policy_area: source_citation cho nguồn/trích dẫn, data_privacy cho secrets, external_publishing cho đăng ngoài, ai_research cho workflow. Đây là hướng sửa tiếp, chưa áp dụng rồi báo điểm mới.

**Cần đánh giá thủ công:** tool call đúng nhưng API lỗi; nhiều URL chưa chọn rõ; hỏi lại bằng text thay vì clarify; TypeError bộ chấm bị gán provider_error; yêu cầu nhiều bước có thứ tự ở E06. Điểm routing không bao quát chất lượng câu trả lời cuối.

**Bài học:** v2 sửa được xác nhận nhưng tổng điểm không tăng, một case multi-turn lại fail. Thêm tool giữ base 100% nhưng extension giảm. Cần ghi cả kết quả xấu, tránh suy luận nhân quả từ một run và ghi rõ group thay đổi 10 → 11 → 15 case. Hash cần thiết vì nhãn phiên có thể giữ nguyên khi prompt đổi.

**Ưu tiên cải thiện tiếp:** kiểm chứng Việt/Anh và chuyển ngôn ngữ; chạy lại ba suite sau chỉnh prompt; làm rõ policy_area; bổ sung case nhiều URL mơ hồ và nhiều bước tuần tự; cấu hình RapidAPI để lấy tweet thật. Nếu nhận bonus Telegram cần phiên xác nhận và gửi thật được cho phép. Hosting lâu dài cần dịch vụ riêng thay vì tunnel từ máy cá nhân.

## B7. Small Local Model Challenge (bonus)

**Không nhận bonus local model trong bản tích hợp này.** Gói bằng chứng hiện tại chưa có run Ollama cho ít nhất hai model local, hai vòng tối ưu local và kiểm tra ngược cloud theo README. Không dùng điểm cloud thay cho kết quả local chưa có trong gói nộp, không điền số liệu hoặc kết luận giả.

Nếu mở rộng sau: chạy hai model ≤8B, phân loại lỗi routing/JSON/tool lặp, tối ưu từng giả thuyết và kiểm tra lại trên cloud. Report hiện tại chỉ kết luận trên model cloud đã có log.

## Chạy lại và kiểm tra bài nộp

Từ thư mục starter_v0:

```powershell
uv pip install -r requirements.txt
uv run python -m pytest
uv run python chat.py --provider openrouter --version v4-integrated
uv run python -m streamlit run app.py
```

Mở phiên CLI/UI mới để nhận prompt mới. Nhãn version chỉ phục vụ ghi log, không khôi phục file prompt cũ; dùng nhãn mới khi chạy eval sau quy tắc ngôn ngữ.

Nộp code, artifacts, data/eval_group.json, tests, runs, analysis và transcript phù hợp. Không đưa `.env`, API key, `.venv` hoặc ghi chú riêng vào Git. Link A1 là demo tạm; push repository không phải deploy.
