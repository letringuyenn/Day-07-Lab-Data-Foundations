# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Lê Trí Nguyên  
**MSSV:** 2A202600651  
**Nhóm:** Nhóm 6 — AI/RAG Technical Documentation  
**Ngày:** 05/06/2026

### Thành Viên Nhóm

| # | Họ tên | MSSV |
|---|--------|------|
| 1 | Phạm Duy Thái | 2A202600860 |
| 2 | Phạm Văn Mạnh | 2A202600837 |
| 3 | **Lê Trí Nguyên** | **2A202600651** |
| 4 | Nguyễn Kim Hoàng | 2A202600987 |
| 5 | Nguyễn Thành Đạt | 2A202600831 |
| 6 | Đoàn Hải Phong | 2A202600577 |

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai text chunk có cosine similarity cao khi các vector embedding của chúng hướng gần giống nhau. Điều này thường cho thấy hai đoạn văn có nội dung, chủ đề hoặc ý nghĩa ngữ nghĩa tương đồng, ngay cả khi chúng không dùng chính xác cùng một từ.

**Ví dụ HIGH similarity:**
- Sentence A: "Vector database stores embeddings for semantic search."
- Sentence B: "A vector store keeps embedding vectors and retrieves semantically similar documents."
- Tại sao tương đồng: Cả hai câu đều mô tả chức năng lưu embedding và tìm kiếm theo độ tương đồng ngữ nghĩa của vector store.

**Ví dụ LOW similarity:**
- Sentence A: "Python is commonly used for data analysis."
- Sentence B: "The restaurant closes at ten o'clock tonight."
- Tại sao khác: Hai câu thuộc hai chủ đề không liên quan: một câu nói về ngôn ngữ lập trình, câu còn lại nói về giờ đóng cửa của nhà hàng.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity tập trung vào góc giữa hai vector, tức là hướng biểu diễn ngữ nghĩa, thay vì bị ảnh hưởng nhiều bởi độ lớn của vector. Vì vậy, nó phù hợp hơn khi cần so sánh ý nghĩa của văn bản, đặc biệt khi các embedding đã được chuẩn hóa.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: `ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = ceil(22.11)`.
>
> Đáp án: **23 chunks**.

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Khi `overlap=100`, số chunk là `ceil((10,000 - 100) / (500 - 100)) = ceil(9,900 / 400) = 25`, tức tăng từ 23 lên 25 chunks. Overlap lớn hơn giúp giữ lại ngữ cảnh nằm gần ranh giới giữa hai chunk, nhưng làm tăng số chunk, dung lượng lưu trữ và chi phí embedding/retrieval.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** AI/RAG Technical Documentation — tài liệu kỹ thuật về Python, vector store, RAG, customer support và chunking.

**Tại sao nhóm chọn domain này?**
> Domain này bám sát mục tiêu của lab và mô phỏng một knowledge assistant dành cho đội kỹ thuật. Bộ tài liệu có nhiều dạng cấu trúc như Markdown heading, paragraph, danh sách và văn bản hướng dẫn, nhờ đó nhóm có thể quan sát rõ ảnh hưởng của từng chunking strategy. Các tài liệu cũng chứa những câu trả lời có thể kiểm chứng về retrieval, metadata, escalation và đánh giá query thất bại.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | `python_intro.txt` | Local course data | 1,944 | `category=python`, `language=en` |
| 2 | `vector_store_notes.md` | Local course data | 2,123 | `category=vector_db`, `language=en` |
| 3 | `rag_system_design.md` | Local course data | 2,391 | `category=rag`, `language=en` |
| 4 | `customer_support_playbook.txt` | Local course data | 1,692 | `category=support`, `language=en` |
| 5 | `chunking_experiment_report.md` | Local course data | 1,987 | `category=chunking`, `language=en` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `source` | string | `rag_system_design.md` | Truy vết tài liệu gốc và hỗ trợ kiểm chứng câu trả lời |
| `category` | string | `rag`, `support`, `chunking` | Thu hẹp search space theo chủ đề trước khi similarity search |
| `language` | string | `en`, `vi` | Tránh trộn kết quả khác ngôn ngữ |
| `doc_id` | string | `rag_system_design-3` | Xác định và xóa tất cả record thuộc một tài liệu |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| `rag_system_design.md` | FixedSize (`fixed_size`) | 12 | 199.2 | Kém: có thể cắt giữa câu |
| `rag_system_design.md` | Sentence (`by_sentences`) | 5 | 476.0 | Tốt: giữ câu hoàn chỉnh |
| `rag_system_design.md` | Recursive (`recursive`) | 20 | 117.7 | Tốt về cấu trúc nhưng khá nhỏ |
| `customer_support_playbook.txt` | FixedSize (`fixed_size`) | 9 | 188.0 | Kém: có thể cắt hướng dẫn |
| `customer_support_playbook.txt` | Sentence (`by_sentences`) | 4 | 421.0 | Tốt: giữ trọn ý |
| `customer_support_playbook.txt` | Recursive (`recursive`) | 14 | 119.1 | Khá tốt, nhiều chunk nhỏ |
| `python_intro.txt` | FixedSize (`fixed_size`) | 10 | 194.4 | Trung bình |
| `python_intro.txt` | Sentence (`by_sentences`) | 5 | 387.0 | Tốt |
| `python_intro.txt` | Recursive (`recursive`) | 14 | 136.9 | Tốt về ranh giới tự nhiên |

### Strategy Của Tôi

**Loại:** `RecursiveChunker(chunk_size=400)`

**Mô tả cách hoạt động:**
> Strategy của tôi thử tách văn bản theo thứ tự `"\n\n"` → `"\n"` → `". "` → `" "` → ký tự. Nó ưu tiên paragraph và dòng trước để giữ cấu trúc tài liệu kỹ thuật; chỉ khi một phần vẫn vượt 400 ký tự mới tiếp tục dùng separator nhỏ hơn. Nếu không còn separator phù hợp, hệ thống fallback sang fixed-size slicing. Trên 5 tài liệu của nhóm, cấu hình này tạo **36 chunks**, độ dài trung bình **279.9 ký tự**.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Các file Markdown và technical notes thường tổ chức thông tin theo heading, paragraph và danh sách. Recursive chunking khai thác trực tiếp các ranh giới này nên ít cắt vỡ một luận điểm hơn fixed-size, đồng thời kiểm soát kích thước tốt hơn sentence chunking khi có câu hoặc section dài.

**Code snippet:**
```python
from src import RecursiveChunker

chunker = RecursiveChunker(chunk_size=400)
chunks = chunker.chunk(document.content)
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| `rag_system_design.md` | Sentence baseline | 5 | 476.0 | Coherent nhưng chunk khá dài |
| `rag_system_design.md` | **Recursive(400) của tôi** | 8 | 297.1 | Cân bằng hơn giữa cấu trúc và kích thước |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy thử nghiệm | Tổng chunks | Điểm mạnh | Điểm yếu |
|-----------|----------------------|-------------|-----------|----------|
| Phạm Duy Thái | Sentence(3) | 27 | Chunk hoàn chỉnh, dễ đọc | Kích thước không đều |
| Phạm Văn Mạnh | FixedSize(300, overlap=50) | 42 | Kích thước ổn định, có overlap | Có thể cắt giữa câu |
| **Lê Trí Nguyên** | **Recursive(400)** | **36** | Tôn trọng paragraph và sentence | Một số chunk còn nhỏ |
| Nguyễn Kim Hoàng | Sentence(2) | 42 | Context tập trung hơn Sentence(3) | Dễ thiếu ngữ cảnh liên câu |
| Nguyễn Thành Đạt | FixedSize(500, overlap=100) | 26 | Giữ nhiều context tại ranh giới | Chunk lớn dễ chứa nhiễu |
| Đoàn Hải Phong | Recursive(600) | 25 | Ít chunk, giữ section dài | Embedding có thể bị pha loãng |

> Bảng trên là kịch bản A/B test chung: cùng 5 tài liệu, cùng `_mock_embed` và cùng 5 benchmark queries. Mỗi cấu hình được chạy bằng package cá nhân của tôi để tạo cơ sở thảo luận; đây không phải tuyên bố thay cho kết quả code riêng của từng thành viên.

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Không có strategy thắng tuyệt đối. Với bộ technical documentation này, `RecursiveChunker(400)` là lựa chọn cân bằng vì giữ được ranh giới paragraph/câu nhưng không tạo chunk quá dài. Tuy nhiên, kết quả benchmark cho thấy chất lượng `_mock_embed` có ảnh hưởng lớn hơn chênh lệch nhỏ giữa các strategy, nên kết luận cuối cùng cần được kiểm tra lại bằng embedding model ngữ nghĩa.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\r?\n+)` để tìm ranh giới sau các dấu `.`, `!`, `?` khi phía sau là khoảng trắng hoặc xuống dòng. Văn bản được `strip()` trước khi tách, các câu rỗng bị loại bỏ và những câu liên tiếp được ghép theo `max_sentences_per_chunk`. Constructor cũng kiểm tra tham số phải lớn hơn 0 và văn bản rỗng trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán thử separator theo thứ tự ưu tiên `"\n\n"`, `"\n"`, `". "`, `" "` và cuối cùng là `""`, nhờ đó ưu tiên giữ nguyên đoạn văn và câu trước khi phải cắt theo ký tự. Base case là khi đoạn hiện tại không vượt quá `chunk_size`; nếu không còn separator phù hợp thì thuật toán fallback sang `FixedSizeChunker` không overlap. Các phần nhỏ được ghép lại cho đến khi thêm phần tiếp theo sẽ vượt kích thước, còn phần quá dài tiếp tục được tách đệ quy.

**`compute_similarity` + `ChunkingStrategyComparator`** — approach:
> `compute_similarity` tính dot product rồi chia cho tích độ lớn của hai vector, trả về `0.0` nếu vector rỗng hoặc có độ lớn bằng 0 và báo lỗi nếu hai vector khác chiều. Comparator chạy ba strategy `fixed_size`, `by_sentences` và `recursive`, sau đó trả về số chunk, độ dài trung bình và danh sách chunk để thuận tiện so sánh.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Tôi triển khai store dạng in-memory. Mỗi `Document` được chuyển thành record gồm ID nội bộ, `doc_id`, content, bản sao metadata và embedding sinh bởi embedding backend đã inject. Khi search, query được embed một lần, sau đó tính dot product với từng document embedding, sắp xếp score giảm dần và lấy tối đa `top_k`; với các backend hiện tại vector đã chuẩn hóa nên dot product tương đương cosine similarity.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` lọc record theo tất cả cặp key-value trong metadata trước, rồi mới tính similarity trên tập ứng viên còn lại; cách này tránh đưa tài liệu sai điều kiện vào ranking. `delete_document` tạo lại danh sách store sau khi loại mọi record có `metadata["doc_id"]` trùng với ID cần xóa và trả về `True` nếu kích thước store thực sự giảm.

### KnowledgeBaseAgent

**`answer`** — approach:
> Agent gọi `store.search(question, top_k)` để lấy các tài liệu liên quan, đánh số từng kết quả dưới dạng `[Source n]` rồi ghép content thành phần context. Prompt yêu cầu LLM chỉ trả lời dựa trên context và phải nói rõ khi không đủ thông tin, sau đó chèn câu hỏi và gọi `llm_fn`. Nếu store không trả về kết quả, prompt sử dụng thông báo không tìm thấy context thay vì để trống.

### Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0
collected 42 items

tests/test_solution.py ..........................................        [100%]

============================= 42 passed in 0.21s ==============================
```

**Số tests pass:** **42 / 42**

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | A vector store saves embeddings for similarity search. | A vector database stores embeddings and retrieves similar documents. | High | -0.324310 | Không |
| 2 | Python is widely used for data analysis. | Python is a popular language for analyzing data. | High | 0.013057 | Không |
| 3 | Metadata filtering narrows the retrieval candidates. | Filtering by metadata removes documents that do not match the conditions. | High | 0.054929 | Không |
| 4 | Recursive chunking preserves paragraph and sentence boundaries. | The restaurant closes at ten o'clock tonight. | Low | 0.295556 | Không |
| 5 | A vector database stores numerical embeddings. | Bananas are yellow tropical fruits. | Low | 0.061724 | Có |

Các điểm trên được tính bằng `compute_similarity(_mock_embed(sentence_a), _mock_embed(sentence_b))`, đúng với embedding backend mặc định của project. Tôi đưa ra dự đoán dựa trên mức độ tương đồng ngữ nghĩa trước khi chạy phép tính.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 1 bất ngờ nhất vì hai câu gần như diễn đạt cùng một ý nhưng score lại là `-0.324310`, trong khi Pair 4 không liên quan lại có score cao nhất là `0.295556`. Nguyên nhân là `_mock_embed` tạo vector xác định từ MD5 hash để phục vụ test, chứ không phải mô hình đã học ngữ nghĩa của ngôn ngữ. Thí nghiệm cho thấy pipeline có thể chạy đúng về mặt kỹ thuật nhưng retrieval quality vẫn phụ thuộc mạnh vào chất lượng embedding; khi đánh giá thực tế nên thử `all-MiniLM-L6-v2` hoặc một embedding model phù hợp hơn.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

**Cấu hình cá nhân:** `RecursiveChunker(chunk_size=400)`, `_mock_embed`, 36 chunks từ 5 tài liệu, `top_k=3`. Q5 sử dụng metadata pre-filter `{"category": "chunking"}`.

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer | Filter |
|---|-------|-------------|--------|
| 1 | What is the purpose of chunk overlap? | Chia sẻ nội dung giữa các chunk liên tiếp để giữ ngữ cảnh tại ranh giới và hạn chế cắt mất ý | Không |
| 2 | What metadata should support documents have? | Phân biệt customer-facing articles, internal support-only notes và engineering-only incident documents | Không |
| 3 | What happens when no document answers the query? | Hệ thống nên thừa nhận không đủ dữ liệu và recommend escalation thay vì bịa câu trả lời | Không |
| 4 | How often should failed queries be reviewed? | Support operations team nên review failed queries mỗi tuần | Không |
| 5 | What chunking strategy is recommended for mixed technical docs? | Recursive chunking là strong default, nhưng vẫn cần validate bằng query thực tế | `category=chunking` |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Purpose of chunk overlap | Support assistant phải nhận biết retrieval không đủ và escalation | 0.242267 | Không | Context không nói về overlap nên không thể trả lời đúng |
| 2 | Metadata for support documents | Python ecosystem giúp chuyển từ thử nghiệm sang deployment | 0.273824 | Không | Context sai domain; gold answer nằm trong support playbook nhưng không vào top-3 |
| 3 | No document answers the query | Khi evidence yếu hoặc mâu thuẫn, assistant phải nói rõ thay vì giả vờ câu trả lời đầy đủ | 0.228365 | Có một phần | Có thể trả lời đúng nguyên tắc “không bịa”, nhưng thiếu chi tiết escalation |
| 4 | Failed query review frequency | Quy trình vector search: chunk, embed, store metadata | 0.353386 | Không | Score cao nhất nhưng không chứa thông tin “every week” |
| 5 | Recommended strategy for mixed technical docs | Recursive chunking giữ cấu trúc lớn trước rồi fallback sang separator nhỏ | 0.151831 | Có | Trả lời được recursive chunking là strong default và cần validation |

**Bao nhiêu queries trả về chunk relevant trong top-3?** **2 / 5** — Q3 có evidence gần nghĩa và Q5 có evidence trực tiếp.

### So Sánh Kịch Bản 6 Thành Viên

Tất cả cấu hình dưới đây được chạy trên cùng dữ liệu, queries và `_mock_embed` để tạo một thí nghiệm có kiểm soát:

| Thành viên | Strategy | Chunks | Avg length | Quan sát nổi bật |
|-----------|----------|--------|------------|------------------|
| Phạm Duy Thái | Sentence(3) | 27 | 373.6 | Q3 và Q5 tìm được evidence liên quan |
| Phạm Văn Mạnh | FixedSize(300, overlap=50) | 42 | 285.4 | Q5 top-1 chứa mô tả recursive chunking |
| **Lê Trí Nguyên** | **Recursive(400)** | **36** | **279.9** | Q3 gần đúng; Q5 đúng trực tiếp |
| Nguyễn Kim Hoàng | Sentence(2) | 42 | 239.8 | Chunk tập trung nhưng ranking vẫn nhiễu do mock embedding |
| Nguyễn Thành Đạt | FixedSize(500, overlap=100) | 26 | 470.7 | Ít chunk hơn, context dài hơn; Q5 tìm đúng conclusion |
| Đoàn Hải Phong | Recursive(600) | 25 | 403.9 | Giữ section dài nhưng dễ pha loãng nội dung |

**Nhận xét cross-strategy:**

- Q5 là query ổn định nhất vì metadata filter giảm search space chỉ còn tài liệu `category=chunking`.
- Q4 là failure case rõ nhất: Recursive(400) trả score `0.353386` cho một chunk về vector workflow nhưng bỏ lỡ câu “review failed queries every week” trong support playbook.
- Score cao không đồng nghĩa với relevance khi dùng `_mock_embed`; score chỉ phản ánh vector hash ngẫu nhiên có tính xác định.
- Strategy thay đổi độ coherent và số lượng chunk, nhưng không thể bù hoàn toàn cho embedding không có semantic understanding.

### Failure Analysis

> Q4 thất bại dù gold answer tồn tại nguyên văn trong dữ liệu. Nguyên nhân chính là `_mock_embed` tạo vector từ hash nên không hiểu quan hệ giữa “how often”, “reviewed” và “every week”. Ngoài ra, việc không filter theo `category=support` khiến toàn bộ 36 chunks cùng cạnh tranh. Cải thiện đề xuất là dùng semantic embedding như `all-MiniLM-L6-v2`, bổ sung metadata `topic=failed_query_review`, và áp dụng filter support khi query thuộc quy trình vận hành.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Cấu hình Sentence(3) của Phạm Duy Thái cho thấy giữ nguyên câu giúp Q3 tìm được đoạn evidence tương đối đầy đủ, trong khi FixedSize có nguy cơ cắt mất vế quan trọng. Ngược lại, cấu hình FixedSize(500, overlap=100) của Nguyễn Thành Đạt cho thấy overlap có thể giữ nhiều context hơn nhưng làm chunk dài và dễ chứa nội dung nhiễu. Việc so sánh sáu cấu hình giúp tôi hiểu rằng chunk count thấp không tự động đồng nghĩa với retrieval tốt.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Phần này cần cập nhật sau buổi demo liên nhóm vì repository clone không chứa kết quả hoặc ghi chú của nhóm khác. Tôi sẽ chỉ ghi nhận xét sau khi quan sát strategy và dữ liệu thật của nhóm bạn, tránh tự tạo kết luận không có bằng chứng.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ bổ sung metadata chi tiết hơn như `audience`, `document_type` và `topic`, sau đó map query sang filter phù hợp trước similarity search. Tôi cũng sẽ thay `_mock_embed` bằng một semantic embedding model và đánh giá lại cùng 5 queries. Riêng Q1 cần bổ sung một tài liệu giải thích trực tiếp chunk overlap vì bộ 5 tài liệu hiện tại không cung cấp gold answer đủ rõ.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 9 / 10 |
| Chunking strategy | Nhóm | 13 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 7 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | Chờ demo / 5 |
| **Tạm tính trước demo** | | **74 / 95** |
