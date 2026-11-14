# Báo cáo cá nhân — Day 6

**Họ và tên:** Bùi Nguyên Dũng  
**MSSV:** 2A202603587  
**Lớp:** L3A  
**Bài thực hành:** Data Ingestion Engineering  
**Repository:** https://github.com/Nesto08/K5-L3A-DAY06-2A202603587-BuiNguyenDung-DataIngestionEngineering

---

## 1. Dữ liệu và pipeline

### 1.1. Chủ đề, nguồn/quyền, số trang và quy tắc tính trang

Trong bài thực hành Day 6, tôi lựa chọn xây dựng hệ thống xử lý và truy xuất nội dung từ tài liệu học lập trình Python.

**Corpus được sử dụng:**

- **Tên tài liệu:** *Introduction to Python Programming*.
- **Nhà xuất bản:** OpenStax.
- **Nguồn:** https://openstax.org/details/books/introduction-python-programming
- **Định dạng:** PDF.
- **Nội dung:** Chương 1 — Statements và Chương 2 — Expressions.
- **Phạm vi:** 59 trang nội dung được lựa chọn trong khoảng trang vật lý PDF 17–76.
- **Quyền sử dụng:** Tài liệu giáo dục mở của OpenStax; thông tin nguồn và giấy phép được khai báo trong `data/manifest.json`.

Tôi sử dụng số trang vật lý của PDF để định danh dữ liệu, không dùng số trang in trong sách làm định danh chính.

Các trang bìa, trang trống hoặc trang không có nội dung hữu ích không được đưa vào tập dữ liệu dùng cho thí nghiệm. Manifest ghi lại thông tin nguồn, trang, chương và nội dung tương ứng để thuận tiện kiểm tra.

Tài liệu được chọn vì có cấu trúc theo chương rõ ràng, nội dung phù hợp để xây dựng câu hỏi benchmark và có thể kiểm tra trực tiếp evidence trong PDF.

### 1.2. Chuẩn hóa, lỗi và giới hạn

Pipeline sử dụng **PyMuPDF** để đọc và trích xuất văn bản từ PDF.

Quy trình xử lý gồm:

1. Đọc các trang PDF và trích xuất nội dung văn bản.
2. Chuẩn hóa Unicode về NFC.
3. Chuẩn hóa khoảng trắng và ký tự xuống dòng.
4. Loại bỏ các trang không trích xuất được văn bản.
5. Gắn metadata trước khi thực hiện chunking.

Trong quá trình chạy, hệ thống ghi nhận cảnh báo hai trang đầu không có nội dung văn bản trích xuất được. Chương trình bỏ qua các trang này và tiếp tục xử lý.

Một số giới hạn của phương pháp:

- PDF có thể chứa ngắt dòng không tự nhiên.
- Header, footer, bảng biểu và ví dụ mã nguồn có thể ảnh hưởng đến ranh giới đoạn.
- Chunking có thể cắt ngang câu hoặc làm mất một phần ngữ cảnh.
- Chưa áp dụng OCR cho các trang chỉ chứa hình ảnh.

Những yếu tố này có thể tác động trực tiếp đến chất lượng truy xuất.

### 1.3. Embedding model, vector store, metric, lệnh chạy và chi phí

Tôi sử dụng OpenAI Embedding API để chuyển các chunk thành vector và ChromaDB để lưu trữ, tìm kiếm.

| Thành phần | Cấu hình |
|---|---|
| Ngôn ngữ | Python |
| PDF parser | PyMuPDF |
| Embedding provider | OpenAI |
| Embedding model | `text-embedding-3-small` |
| Vector dimensions | 1536 |
| Vector store | ChromaDB PersistentClient |
| Similarity metric | Cosine similarity |
| Retrieval | Top-3 |
| Web demo | Streamlit |

Các vector được lưu trong thư mục `starter/chroma_db/`, cho phép tái sử dụng sau khi kết thúc chương trình.

**Lệnh chạy pipeline:**

```powershell
cd starter
python -m src.run
```

**Lệnh chạy web app:**

```powershell
python -m streamlit run app.py
```

Web app cho phép nhập câu hỏi, chọn chiến lược A/B/C, xem kết quả truy xuất và theo dõi nhật ký chạy.

**Phiên bản thư viện:** Chưa ghi lại đầy đủ phiên bản OpenAI SDK, ChromaDB và PyMuPDF tại thời điểm thực nghiệm. Có thể kiểm tra trong môi trường chạy bằng `python -m pip show openai chromadb pymupdf`.

**Chi phí:** Pipeline sử dụng embedding model thật thông qua API. Tuy nhiên, chương trình chưa ghi nhận tổng số token và chi phí API chính xác nên không đưa ra một giá trị chi phí giả định.

### 1.4. Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn

Mỗi chunk lưu các metadata sau:

| Metadata | Ý nghĩa | Nguồn |
|---|---|---|
| `document_id` | Mã tài liệu | Manifest |
| `source` | Nguồn tài liệu | Manifest |
| `page` | Trang PDF | PDF parser |
| `chapter` | Chương của tài liệu | Manifest |
| `chunk_type` | Phương pháp chunking | Pipeline |

Tôi chọn `chapter` làm trường lọc bổ sung do corpus gồm hai chương có nội dung phân biệt rõ.

Khi câu hỏi yêu cầu nội dung thuộc chương cụ thể, metadata filter giúp giới hạn phạm vi tìm kiếm.

Giá trị `chapter` được lấy từ manifest, không phải do mô hình tự suy đoán. Điều này giúp việc lọc và truy vết có cơ sở rõ ràng.

---

## 2. Cấu hình và benchmark

### 2.1. Ba chiến lược A/B/C

Tôi triển khai ba chiến lược trên cùng corpus, embedding model, vector database và bộ câu hỏi.

| Tham số | Strategy A | Strategy B | Strategy C |
|---|---|---|---|
| Chunking | Fixed-size | Paragraph | Paragraph |
| Chunk size | 500 ký tự | Tối đa 700 ký tự | Tối đa 700 ký tự |
| Overlap | 50 | 0 | 0 |
| Metadata | Có | Có | Có |
| Metadata filter | Không | Không | Có khi được yêu cầu |
| Embedding model | `text-embedding-3-small` | Giống A | Giống A |
| Vector store | ChromaDB | ChromaDB | ChromaDB |
| Số chunk | 224 | 161 | 161 |

**Strategy A — Fixed-size Chunking**

Chia nội dung thành các đoạn 500 ký tự, với overlap 50 ký tự giữa những chunk liên tiếp.

Ưu điểm là đơn giản, dễ kiểm soát kích thước và overlap có thể giúp giữ lại một phần ngữ cảnh.

Hạn chế là chunk có thể kết thúc giữa câu hoặc giữa một đoạn giải thích.

**Strategy B — Paragraph Chunking**

Chia tài liệu theo đoạn văn, giới hạn tối đa 700 ký tự mỗi chunk.

Mục tiêu là giữ nội dung trong các đoạn có liên quan với nhau, hạn chế việc cắt ngang ý so với fixed-size chunking.

Tuy nhiên, hiệu quả phụ thuộc vào việc PDF có giữ được ranh giới đoạn văn chính xác hay không.

**Strategy C — Paragraph Chunking + Metadata Filter**

Sử dụng cùng phương pháp chunking với Strategy B nhưng bổ sung metadata filtering theo `chapter` khi câu hỏi có điều kiện.

**Khác biệt duy nhất giữa B và C là việc sử dụng metadata filter ở bước truy xuất.**

Nhờ đó, phép so sánh B–C có thể tập trung vào ảnh hưởng của metadata filtering mà không thay đổi các tham số chunking.

### 2.2. Bộ câu hỏi benchmark

Tôi xây dựng bộ benchmark gồm **20 câu hỏi**, lưu tại `benchmark/questions.json`.

Bộ câu hỏi được chia thành:

- **Dev:** Q01–Q15, gồm 15 câu.
- **Test:** Q16–Q20, gồm 5 câu.

Các câu hỏi bao gồm dạng hỏi trực tiếp, diễn đạt lại và câu hỏi có điều kiện metadata.

Có bốn câu sử dụng filter:

| Question ID | Split | Filter |
|---|---|---|
| Q06 | Dev | `chapter = "1"` |
| Q14 | Dev | `chapter = "2"` |
| Q17 | Test | `chapter = "2"` |
| Q20 | Test | `chapter = "2"` |

Mỗi câu lưu các thông tin:

- Mã câu hỏi và split.
- Nội dung câu hỏi.
- Đáp án kỳ vọng (`gold_answer`).
- Nguồn và trang chứa evidence.
- Đoạn evidence tham chiếu.
- Evidence anchor.
- Metadata filter nếu có.

Trong quá trình chạy, chương trình kiểm tra sự tồn tại của evidence anchor trong văn bản trang PDF đã chuẩn hóa.

Tuy nhiên, việc xác minh tự động chỉ chứng minh anchor có trong nguồn, chưa bảo đảm đoạn bằng chứng chứa đầy đủ mọi điều kiện của đáp án. Vì vậy cần kết hợp đánh giá thủ công.

Một điểm hạn chế là câu Q06 có filter theo chương 1 nhưng nội dung câu hỏi chưa chỉ rõ chương. Trong ứng dụng thực tế, filter cần được cung cấp từ câu hỏi hoặc ngữ cảnh trước khi truy xuất.

### 2.3. Tiêu chí chọn chiến lược

Năm tiêu chí được sử dụng trong benchmark gồm:

1. **Retrieval Accuracy:** Hit@1 và Evidence Hit@3.
2. **Chunk Coherence:** Mức độ trọn ý của chunk.
3. **Metadata Usefulness:** Tính đầy đủ, chính xác và khả năng lọc.
4. **Grounding Quality:** Mức độ đầy đủ của bằng chứng truy xuất.
5. **Data Strategy Impact:** Ảnh hưởng đến chất lượng, số chunk, thời gian và chi phí.

Các tiêu chí giúp so sánh chiến lược trên cả chất lượng truy xuất và tài nguyên sử dụng.

Bộ câu hỏi ghi rõ quy tắc chia dev/test. Tuy nhiên, chưa có minh chứng độc lập về thời điểm chốt tiêu chí lựa chọn trước khi xem kết quả test. Vì vậy, kết luận được xem là đánh giá trên bộ benchmark hiện có, không phải bằng chứng tối ưu hóa trên một tập test hoàn toàn chưa từng được xem.

---

## 3. Kết quả

### 3.1. Retrieval Accuracy

Kết quả chạy ba chiến lược:

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian ingest |
|---|---|---|---|---|---|---|
| A | Dev | 6/15 (40%) | 13/15 (86,67%) | 224 | 2,04s |
| A | Test | 2/5 (40%) | 4/5 (80%) | 224 | 2,04s |
| B | Dev | 7/15 (46,67%) | 10/15 (66,67%) | 161 | 1,74s |
| B | Test | 1/5 (20%) | 4/5 (80%) | 161 | 1,74s |
| C | Dev | 7/15 (46,67%) | 10/15 (66,67%) | 161 | 2,15s |
| C | Test | 1/5 (20%) | 4/5 (80%) | 161 | 2,15s |

**Nhận xét:**

- Strategy A có Evidence Hit@3 cao nhất trên dev, đạt 86,67%.
- Strategy B và C có Hit@1 dev cao hơn A một chút.
- Trên test, cả ba đạt Evidence Hit@3 là 80%.
- Kết quả retrieval tổng hợp của B và C giống nhau.

Số liệu trên được tính bằng cách kiểm tra nguồn, trang và evidence anchor của các chunk truy xuất. Đây chưa phải kết quả chấm thủ công về độ đủ của bằng chứng.

Thời gian trong bảng là thời gian ingest của từng cấu hình, được lặp lại trên dev và test; không phải hai lần ingest riêng biệt.

### 3.2. Chunk count và thời gian

| Strategy | Chunk count | Tổng ký tự chunk | Ingest time |
|---|---:|---:|---:|
| A | 224 | 98.531 | 2,04s |
| B | 161 | 90.229 | 1,74s |
| C | 161 | 90.229 | 2,15s |

So với A, Strategy B và C giảm 63 chunk, tương đương khoảng 28,1%.

A có tổng số ký tự trong các chunk lớn hơn do sử dụng overlap.

B và C có cùng số chunk và tổng ký tự, phù hợp với thiết kế chỉ thay đổi metadata filtering giữa hai cấu hình.

Thời gian ingest đo được khá gần nhau, nên chưa đủ cơ sở để khẳng định cấu hình nào luôn nhanh nhất trong các lần chạy khác nhau.

### 3.3. Manual Audit

Manual audit được tổ chức trong một file duy nhất:

`results/manual_audit.csv`

File gồm ba nhóm đánh giá:

- **Coherence:** 30 dòng, tương ứng 10 vị trí nguồn × 3 chiến lược.
- **Metadata:** 45 dòng, tương ứng top-3 của 5 câu test × 3 chiến lược.
- **Grounding:** 15 dòng, tương ứng 5 câu test × 3 chiến lược.

Bảng tổng hợp:

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N) | Grounding 0/1/2 và trung bình /2 |
|---|---|---|---|---|
| A | Chưa chốt (10 mẫu) | Chưa xác minh (15 bản ghi) | 3/4 phù hợp tự nhiên | Chưa chốt (5 câu) |
| B | Chưa chốt (10 mẫu) | Chưa xác minh (15 bản ghi) | 2/4 phù hợp tự nhiên | Chưa chốt (5 câu) |
| C | Chưa chốt (10 mẫu) | Chưa xác minh (15 bản ghi) | 4/4 tuân thủ | Chưa chốt (5 câu) |

**Chunk Coherence:** Được đánh giá trên cùng 10 vị trí nội dung nguồn. Mỗi chunk được chấm từ 0 đến 2 dựa trên mức độ giữ trọn ý và ngữ cảnh.

**Metadata Correctness:** Đối chiếu metadata của top-3 kết quả test với nguồn PDF và manifest.

**Grounding Quality:** Đọc các chunk top-3 và chấm 0–2 theo mức độ đủ bằng chứng để trả lời câu hỏi, không đánh giá độ chính xác của câu trả lời do LLM sinh ra.

Cấu hình C tuân thủ điều kiện chapter ở cả 4 câu hỏi có filter. Với A và B, các tỷ lệ tương ứng chỉ thể hiện việc kết quả tình cờ nằm đúng chương vì hai cấu hình này không thực thi filter.

Các trường điểm và xác minh thủ công chưa được hoàn thiện không được tính thành kết quả audit chính thức.

### 3.4. Đường dẫn minh chứng

| Nội dung | Đường dẫn trong repository |
|---|---|
| Corpus manifest | [data/manifest.json](../../data/manifest.json) |
| Benchmark questions | [benchmark/questions.json](../../benchmark/questions.json) |
| Experiment log | [artifacts/experiment_log.csv](../../artifacts/experiment_log.csv) |
| Retrieval metrics | [results/metrics.json](../../results/metrics.json) |
| Top-3 traces | [results/traces.json](../../results/traces.json) |
| Ingestion statistics | [results/ingestion_stats.json](../../results/ingestion_stats.json) |
| Manual audit | [results/manual_audit.csv](../../results/manual_audit.csv) |
| Pipeline code | [starter/src/](../../starter/src/) |

Đối với coherence, mẫu được tổ chức theo 10 vị trí nguồn cố định để so sánh A/B/C. Đối với metadata và grounding, sử dụng cả 5 câu test.

---

## 4. Phân tích và kết luận

### 4.1. So sánh A–B

A sử dụng fixed-size chunking với overlap, còn B chia theo đoạn văn.

A tạo nhiều chunk hơn nhưng có Evidence Hit@3 trên dev đạt **86,67%**, cao hơn mức **66,67%** của B.

Điều này cho thấy trong thí nghiệm hiện tại, fixed-size chunking với overlap có lợi thế về khả năng đưa gold evidence vào top-3.

Tuy nhiên, A làm tăng số chunk và lượng văn bản phải embedding, từ đó có thể tăng tài nguyên lưu trữ và chi phí.

B giúp giảm số chunk và tổng ký tự, nhưng trên bộ benchmark hiện tại chưa cải thiện Evidence Hit@3 so với A.

### 4.2. So sánh B–C

B và C giữ nguyên phương pháp chunking và sử dụng cùng embedding model.

C bổ sung metadata filtering ở bước truy xuất.

Kết quả cho thấy C bảo đảm top-3 nằm trong chương được yêu cầu ở các câu có filter.

Tuy nhiên, Hit@1 và Evidence Hit@3 tổng hợp không tăng so với B.

Do đó, metadata filtering có ích trong việc giới hạn phạm vi truy xuất, nhưng chưa chứng minh được cải thiện retrieval accuracy trên bộ dữ liệu này.

### 4.3. Hai ví dụ truy xuất thất bại

**Ví dụ 1: Q03 — Tham số `end` trong hàm `print()`**

- **Question ID:** Q03.
- **Câu hỏi:** How do you prevent print() from automatically starting a new line?
- **Gold source:** OpenStax, trang vật lý PDF 21, Chương 1.
- **Đáp án kỳ vọng:** Sử dụng tham số `end` để tiếp tục in trên cùng một dòng.

Cả ba chiến lược đều không đạt Evidence Hit@3 theo cách kiểm tra gold anchor hiện tại.

Một số chunk tìm được liên quan đến `print()`, nhưng không chứa đúng đoạn evidence tham chiếu.

Trường hợp này cho thấy hệ thống có thể tìm các đoạn cùng chủ đề nhưng không tìm được bằng chứng cần thiết trong top-3.

**Ví dụ 2: Q08 — Định nghĩa Python string**

- **Question ID:** Q08.
- **Câu hỏi:** How does the book define a Python string?
- **Gold source:** OpenStax, trang vật lý PDF 26, Chương 1.
- **Đáp án kỳ vọng:** Một chuỗi ký tự nằm giữa cặp dấu nháy đơn hoặc nháy kép phù hợp.

Cả A, B và C đều không đạt Evidence Hit@3 theo kiểm tra tự động.

Các chunk được truy xuất có liên quan đến chủ đề Python nhưng không chứa đoạn định nghĩa gold.

Điều này cho thấy độ tương đồng vector không phải lúc nào cũng ưu tiên đúng đoạn định nghĩa mà câu hỏi yêu cầu.

### 4.4. Chiến lược lựa chọn, đánh đổi và điều kiện áp dụng

Dựa trên các chỉ số đã đo:

**Strategy A** là ứng viên được ưu tiên khi mục tiêu là nâng cao Evidence Hit@3 trên tập dev.

**Strategy B** giảm số chunk, có thể phù hợp khi muốn giảm lượng dữ liệu embedding và lưu trữ, nhưng cần bổ sung đánh giá coherence để xác nhận lợi ích chất lượng.

**Strategy C** phù hợp khi ứng dụng yêu cầu lọc tài liệu theo chương hoặc metadata có nguồn xác định.

Nếu cần lựa chọn theo kết quả retrieval dev hiện tại, tôi nghiêng về **Strategy A**.

Tuy nhiên, đây là kết luận có điều kiện. Điểm coherence, grounding và chi phí thực tế chưa đầy đủ nên chưa thể khẳng định A là chiến lược tốt nhất theo toàn bộ năm tiêu chí.

### 4.5. Hạn chế

Thí nghiệm có những hạn chế chính:

1. Corpus chỉ sử dụng hai chương của một tài liệu, chưa đánh giá trên nhiều nguồn.
2. Bộ test chỉ gồm 5 câu, nên kết quả dễ thay đổi theo từng câu.
3. Một số evidence anchor chưa thể hiện đầy đủ tất cả điều kiện trong đáp án kỳ vọng.
4. PDF parsing có thể tạo ngắt dòng không tự nhiên và ảnh hưởng đến chunking.
5. Manual audit chưa được xác minh và chấm đầy đủ.
6. Chưa đo đầy đủ thời gian truy xuất, số token và chi phí API.
7. Chưa có bằng chứng độc lập chứng minh tiêu chí lựa chọn chiến lược đã được khóa trước khi xem test.

### 4.6. Hướng cải tiến

Nếu tiếp tục phát triển, tôi sẽ ưu tiên:

- Cải thiện trích xuất và làm sạch văn bản PDF.
- Thử nghiệm sentence-aware hoặc section-aware chunking.
- Loại bỏ header/footer và những phần nội dung lặp không cần thiết.
- Bổ sung kiểm tra evidence tương đương thay vì chỉ đối sánh anchor.
- Mở rộng bộ benchmark với nhiều câu hỏi hơn.
- Ghi nhận token, chi phí và thời gian truy xuất.
- Hoàn thiện audit thủ công và tự động tổng hợp bảng đánh giá.
- Phát triển giao diện Streamlit để hỗ trợ kiểm tra retrieval, metadata và nhật ký chạy trực tiếp.

### 4.7. Kết luận

Qua bài thực hành Day 6, tôi đã xây dựng và chạy thành công pipeline gồm các bước: trích xuất PDF, chuẩn hóa văn bản, chunking, tạo embedding, lưu ChromaDB và truy xuất top-3.

Ba chiến lược A/B/C đã được thử nghiệm trên cùng corpus và bộ benchmark 20 câu hỏi.

Kết quả cho thấy fixed-size chunking của A có Evidence Hit@3 trên dev cao nhất, trong khi paragraph chunking giảm số lượng chunk. Metadata filtering trong C giúp giới hạn phạm vi truy xuất nhưng không làm tăng các chỉ số retrieval tổng hợp trong thí nghiệm hiện tại.

Bài thực hành giúp tôi hiểu rằng chất lượng của hệ thống truy xuất không chỉ phụ thuộc vào embedding model mà còn chịu ảnh hưởng trực tiếp từ chất lượng corpus, cách chia chunk, metadata và phương pháp đánh giá.

Các bước tiếp theo là hoàn thiện manual audit, ghi nhận chi phí và mở rộng benchmark để có kết luận đáng tin cậy hơn.
