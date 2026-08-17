# Báo Cáo Tiến Độ Thực Hiện Lab 17 — Multi-Memory Agent với Zep

**Thời gian cập nhật:** 17/08/2026  
**Trạng thái:** Đã hoàn thành toàn bộ khối Core Implementation & Auto Benchmark (Đạt **11/11 PASS - 100% Hit Rate**)

---

## 1. Tổng Quan Kết Quả Đạt Được

| Hạng mục | Mục tiêu | Kết quả thực tế | Trạng thái |
| :--- | :---: | :---: | :---: |
| **Môi trường & Seed** | Seed Zep Cloud | Khởi tạo thành công 2 user + 1 shared graph | ✅ Hoàn thành |
| **Unit Tests (`pytest`)** | Khóa contract | 11 passed, 1 skipped (golden) | ✅ 100% Pass |
| **No-Memory Baseline** | Đánh giá đối chứng | 2/11 cases PASS (E01, E10) | ✅ Đúng thiết kế |
| **4 Hàm Student Retrieval** | `memory_student.py` | Hoàn thiện cả 4/4 TODOs | ✅ Hoàn thành |
| **Student Benchmark** | Đạt ≥ 9/11 (80%) | **11/11 cases PASS (100% Hit Rate)** | 🏆 Xuất sắc (56/56đ) |
| **Comparison Report** | So sánh Memory vs No-Memory | Sinh file `reports/comparison.md` | ✅ Hoàn thành |

---

## 2. Chi Tiết Các Bước Đã Thực Hiện

### Bước 1: Thiết lập môi trường thực thi (Local Virtual Environment)
- **Phương án lựa chọn:** Khởi tạo môi trường ảo Python 3.12 (`.venv`) và cài đặt trực tiếp dependencies từ `requirements.txt` thay vì chạy qua Docker container theo yêu cầu của học viên.
- Cài đặt thành công các thư viện trọng tâm: `zep-cloud==3.28.0`, `langgraph`, `pytest`, `streamlit`, `pydantic`,...

### Bước 2: Smoke Test & Seed Dữ Liệu Zep Cloud
- **Smoke test:** Xác thực tính hợp lệ của `data/sessions.json` (11 evaluation cases) và sự hiện diện của `ZEP_API_KEY`.
- **Seed Cloud:** Chạy `python -m src.seed` thực hiện:
  1. Reset và tạo 2 synthetic users: `minh-lab17` và `lan-lab17`.
  2. Tạo standalone semantic knowledge graph: `vinuni-lab17-domain-kb`.
  3. Ingest hội thoại theo 3 stage và chờ Zep index hoàn tất.

### Bước 3: Chạy Baseline Đối Chứng
- **Pytest:** Đạt **11 passed, 1 skipped** (`tests/test_short_term.py`, `tests/test_context_budget.py`, `tests/test_privacy_guard.py`,...).
- **No-memory baseline:** Chạy `python -m src.evaluate --impl no_memory`:
  - Đạt **2/11 PASS** (Chỉ E01 và E10 pass nhờ short-term memory đệm tại chỗ).
  - 9 case còn lại (Long-term, Episodic, Semantic, Mixed) đều fail do không có cơ chế truy xuất bộ nhớ bền vững.
  - Sinh báo cáo `reports/benchmark_no_memory.json` và `reports/benchmark_no_memory.md`.

---

## 3. Chi Tiết Kỹ Thuật 4 TODOs Trong `src/memory_student.py`

Đã hoàn thiện 4 phương thức trong lớp `StudentMemory`:

### 🔹 TODO 1/4: `retrieve_long_term` (Xử lý Cross-Session, Preference & Recency)
- **Mục đích:** Lấy Context Block đã được Zep tổng hợp xuyên suốt các phiên chat của user.
- **Triển khai:**
  ```python
  def retrieve_long_term(self, user_id: str, thread_id: str, query: str) -> str:
      prime_eval_thread(self.client, user_id, thread_id, query)
      context = self.client.thread.get_user_context(thread_id=thread_id)
      return context.context or ""
  ```
- **Điểm mấu chốt:** Gọi `prime_eval_thread` để đưa query vào thread kiểm thử (với `ignore_roles=["user"]` để không làm ô nhiễm bộ nhớ thật), sau đó lấy thuộc tính `.context` dạng chuỗi.
- **Cases giải quyết:** E02 (Python preference), E03 (Open loop/deadline), E08 (Recency - TypeScript ghi đè preference cũ), E09 (User isolation - Lan không thấy fact của Minh).

### 🔹 TODO 2/4: `retrieve_episodic` (Khai thác Trajectory, Outcome & Reflection)
- **Mục đích:** Tìm kiếm các episode/sự kiện cụ thể trong lịch sử của từng user.
- **Triển khai:**
  ```python
  def retrieve_episodic(self, user_id: str, query: str) -> str:
      results = self.client.graph.search(
          user_id=user_id,
          query=cap_query(query),
          scope="episodes",
          limit=5,
      )
      return render_graph_search(results, episode_char_cap=1500)
  ```
- **Điểm mấu chốt:** 
  - Tìm kiếm scoped theo `user_id` (không nhầm sang `graph_id`).
  - Dùng `cap_query(query)` để tránh lỗi Zep từ chối query > 400 ký tự.
  - Đặt `episode_char_cap=1500` để tránh 1 episode quá dài chiếm hết budget khiến reflection bị cắt bỏ.
- **Cases giải quyết:** E04 (Trajectory fix async HTTP), E05 (Reflection về connection churn).

### 🔹 TODO 3/4: `retrieve_semantic` (Truy xuất Tri thức Domain Dùng Chung)
- **Mục đích:** Tìm kiếm tài liệu nghiệp vụ, quy tắc hệ thống trên graph dùng chung.
- **Triển khai:**
  ```python
  def retrieve_semantic(self, graph_id: str, query: str) -> str:
      try:
          results = self.client.graph.search(
              graph_id=graph_id,
              query=cap_query(query),
              scope="episodes",
              limit=8,
          )
          text = render_graph_search(results)
          if text.strip():
              return text
      except Exception:
          pass
      # Fallback sang scope="nodes"
      results = self.client.graph.search(
          graph_id=graph_id,
          query=cap_query(query),
          scope="nodes",
          limit=8,
      )
      return render_graph_search(results)
  ```
- **Điểm mấu chốt:**
  - Search theo `graph_id` thay vì `user_id` (tránh rò rỉ hoặc phân mảnh tri thức domain).
  - Sử dụng `scope="episodes"` giúp giữ nguyên vẹn các literal markers (như `PAYMENT-RULE-3`, `CONN-POOL-FIRST`).
  - Có cơ chế fallback sang `scope="nodes"` để tăng độ tin cậy.
- **Cases giải quyết:** E06 (Quy tắc retry POST payment), E11 (Incident playbook connection pooling).

### 🔹 TODO 4/4: `assemble_context` (Quản lý Token Budget & Priority Layer)
- **Mục đích:** Cắt tỉa và ghép nối các layer theo tỷ lệ ngân sách 10/4/3/3.
- **Triển khai:**
  ```python
  def assemble_context(self, layers: dict[str, str]) -> tuple[str, dict[str, dict[str, int]]]:
      return self.budget.assemble(layers)
  ```
- **Điểm mấu chốt:** Áp dụng thứ tự ưu tiên `short_term (10%) -> long_term (4%) -> episodic (3%) -> semantic (3%)` và trả về cấu trúc `(merged_text, breakdown)` chuẩn contract.
- **Cases giải quyết:** E07 (Mixed query kết hợp cả Long-term preference Python và Semantic rule Idempotency-Key).

---

## 4. Bảng Kết Quả Benchmark Chi Tiết (Student Implementation)

Lệnh thực thi: `python -m src.evaluate --impl student --reuse-seeded`

| Case | Layer | Truy Vấn / Nội Dung | Bắt Buộc Có (Ground Truth) | Kết Quả | Latency | Điểm |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: |
| **E01** | short_term | Tên dự án cá nhân vừa nhắc | `ORCHID-27` | **PASS** | 0.0 ms | 3đ |
| **E02** | long_term | Ngôn ngữ ưu tiên demo Minh | `Python` | **PASS** | 1514.4 ms | 5đ |
| **E03** | long_term | Open loop / deadline của Minh | `benchmark report`, `16:00` | **PASS** | 1433.1 ms | 5đ |
| **E04** | episodic | Cách fix async HTTP timeout | `ClientSession`, `concurrency=20`, `ASYNC-FIX-20` | **PASS** | 271.8 ms | 6đ |
| **E05** | episodic | Reflection về sự cố async | `connection churn`, `timeout threshold` | **PASS** | 269.0 ms | 4đ |
| **E06** | semantic | Quy tắc retry POST payment | `Idempotency-Key`, `max-3-retries`, `exponential-backoff` | **PASS** | 564.8 ms | 6đ |
| **E07** | mixed | Hướng dẫn code payment + preference | `Python`, `Idempotency-Key` | **PASS** | 1791.1 ms | 6đ |
| **E08** | long_term | Stack backend BLUEBIRD-42 (Recency) | `BLUEBIRD-42`, `TypeScript`, `NestJS` | **PASS** | 1639.4 ms | 5đ |
| **E09** | long_term | Stack LOTUS-88 của Lan (Isolation) | `LOTUS-88`, `Java`, `Spring Boot` *(Cấm `ORCHID-27`)* | **PASS** | 1248.0 ms | 5đ |
| **E10** | short_term | Deadline review cũ sau compaction | `REVIEW-DEADLINE-1600`, `Friday`, `16:00` | **PASS** | 0.4 ms | 6đ |
| **E11** | semantic | Incident playbook trước khi tăng timeout | `connection pooling`, `CONN-POOL-FIRST` | **PASS** | 254.7 ms | 5đ |
| **TỔNG**| | **11/11 Cases PASS (Hit Rate 100%)** | | **PASS** | | **56 / 56đ** |

---

## 5. Các Bước Kế Tiếp Cần Làm Để Hoàn Thiện Điểm Số (80đ + 20đ Thưởng)

1. **Privacy Drill (6 điểm):**
   - Chạy lệnh xóa user `minh-lab17`: `python -m src.forget --user-id minh-lab17`
   - Xác minh: `python -m src.forget --user-id minh-lab17 --verify-only` (In ra `Zep user absent: True`).
   - Seed lại Zep (`python -m src.seed`) để chuẩn bị cho Golden set.

2. **Soạn Thảo `README_submission.md` (12 điểm):**
   - 3 câu hỏi reflection (Layer quan trọng nhất, Trade-off Zep vs Redis/Qdrant, Memory poisoning guardrail).
   - 4 câu phân tích benchmark & so sánh (`comparison.md`).
   - Phân tích ngắn về Recency (E08) và Compaction (E10).

3. **Golden Set (Điểm thưởng +10):**
   - Chờ giảng viên cung cấp file `data/golden_eval.json`.
   - Chạy: `python -m src.evaluate --impl student --reuse-seeded --golden` để đạt 20/20 PASS.

4. **Demo Mini-Product UI (Điểm thưởng +10):**
   - Hoàn thiện hàm `retrieve_for_case` trong `src/demo_ui.py`.
   - Chạy giao diện Streamlit: `streamlit run src/demo_ui.py`.
