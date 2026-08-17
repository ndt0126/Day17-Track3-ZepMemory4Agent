# Báo Cáo Thu Hoạch Lab 17 — Multi-Memory Agent

## 1. Ba Câu Hỏi Thực Hành (Reflection)

1. **Tầng bộ nhớ quan trọng nhất:** **Long-term Memory** (minh họa: E02, E03, E08, E09). Đây là "trí nhớ dài hạn" giúp AI nhớ sở thích, việc dang dở, cách ly người dùng (Minh vs Lan) và tự cập nhật khi người dùng đổi ý.
2. **Đánh đổi giữa Zep Cloud và Tự dựng (Redis + Qdrant):**
   - *Zep Cloud:* Tự xâu chuỗi dữ liệu thành đồ thị, tự xử lý tin mới/cũ, nhưng phụ thuộc mạng và cloud API.
   - *Tự dựng:* Toàn quyền bảo mật, truy xuất tức thì, nhưng phải tự code logic đồ thị và xung đột phức tạp.
3. **Chống nhiễm độc bộ nhớ (Memory Poisoning):**
   - Chỉ lưu khi có sự đồng ý (Opt-in Consent).
   - Tự động ẩn thông tin nhạy cảm (PII: email, SĐT).
   - Đánh dấu câu hỏi truy vấn (`ignore_roles`) tránh biến câu hỏi tạm thời thành sự thật dài hạn.

---

## 2. Bốn Câu Phân Tích Benchmark & So Sánh

1. **Tầng có Hit Rate thấp nhất:** Ở bản No-memory, mọi tầng ngoài Short-term đều đạt **0%**. Khi bật Zep, toàn bộ đạt **100% (11/11 case PASS)**.
2. **Truy vấn tốn token nhất:** Case **E07 (Mixed)** và **E06 (Semantic)** do cần tải các quy tắc nghiệp vụ chi tiết.
3. **Cơ chế hoạt động Case E07 (Mixed):** Kết hợp giữa **Long-term** (Minh thích Python) và **Semantic** (quy định `Idempotency-Key`). Thiếu 1 vế sẽ rớt bài test.
4. **Ý nghĩa Giảm tải Token (Token Reduction):** No-memory giảm 100% token vì không tìm thấy gì (trả rỗng). Tiết kiệm token chỉ có giá trị khi vừa nén gọn vừa **tìm trúng bằng chứng (Hit Rate cao)**.

---

## 3. Phân Tích Recency (E08) & Compaction (E10)

- **E08 (Recency - Tin mới thắng):** Khi Minh yêu cầu dự án `BLUEBIRD-42` bắt buộc dùng `TypeScript`, AI ưu tiên thông tin mới này thay vì sở thích `Python` trước đó.
- **E10 (Compaction - Nén thông minh):** Khi hội thoại dài, AI thu gọn lời thoại thừa nhưng vẫn giữ hạn chót `REVIEW-DEADLINE-1600 (Friday 16:00)` nhờ Ghi chú bền vững (Durable Notes).
