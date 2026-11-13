# Báo cáo cá nhân — Day 6

**Họ và tên:** Bùi Nguyên Dũng  
**MSSV:** 2A202603587  
**Lớp:** L3A  
**Chủ đề:** Data Ingestion Engineering — Xây dựng pipeline truy xuất tài liệu học Python  
**Repository:** https://github.com/Nesto08/K5-L3A-DAY06-2A202603587-BuiNguyenDung-DataIngestionEngineering

---

## 1. Dữ liệu và pipeline

### 1.1. Chủ đề, nguồn/quyền, số trang và quy tắc tính trang

Bài thực hành tập trung vào việc xây dựng pipeline xử lý dữ liệu tài liệu PDF, chia nhỏ nội dung thành các chunk, chuyển đổi văn bản thành vector embedding và lưu trữ trong vector database để phục vụ truy xuất ngữ nghĩa.

Corpus được lựa chọn là tài liệu **Introduction to Python Programming** của OpenStax.

- **Nguồn:** https://openstax.org/details/books/introduction-python-programming
- **Loại dữ liệu:** PDF.
- **Nội dung sử dụng:** Hai chương đầu, *Statements* và *Expressions*.
- **Phạm vi:** 59 trang nội dung được lựa chọn trong khoảng trang vật lý PDF 17–76.
- **Nguồn và giấy phép:** Tài liệu giáo dục mở của OpenStax; thông tin nguồn và quyền sử dụng được khai báo trong `data/manifest.json`.

Quy tắc tính trang dựa trên số trang vật lý của PDF, không sử dụng số trang in trong sách làm định danh chính. Các trang bìa, trang trắng hoặc trang không chứa nội dung hữu ích không được tính vào corpus.

Thông tin về trang, chương và nguồn được lưu trong `manifest.json` để bảo đảm khả năng truy vết.

### 1.2. Chuẩn hóa, lỗi và giới hạn

Pipeline sử dụng thư viện PyMuPDF để đọc và trích xuất nội dung văn bản từ PDF.

Sau khi trích xuất, văn bản được xử lý qua các bước:

1. Chuẩn hóa Unicode theo NFC.
2. Chuẩn hóa ký tự xuống dòng và khoảng trắng.
3. Loại bỏ các dòng trống dư thừa.
4. Bỏ qua những trang không trích xuất được văn bản.
5. Gắn metadata cho từng trang trước khi chia chunk.

Trong quá trình chạy, chương trình ghi nhận cảnh báo trang PDF 1 và 2 không có văn bản trích xuất được. Chương trình tiếp tục xử lý mà không bị dừng.

**Giới hạn:** PDF có thể chứa ngắt dòng không tự nhiên, tiêu đề đầu trang, chân trang, bảng biểu hoặc đoạn văn bị phân tách. Những yếu tố này có thể làm giảm chất lượng chunking và khiến evidence bị chia sang nhiều chunk.

### 1.3. Embedding model, vector store, metric, lệnh chạy và chi phí

Các công nghệ được sử dụng:

| Thành phần | Cấu hình |
|---|---|
| Ngôn ngữ | Python |
| PDF parser | PyMuPDF |
| Embedding provider | OpenAI |
| Embedding model | `text-embedding-3-small` |
| Vector dimensions | 1536 |
| Vector database | ChromaDB |
| Storage | PersistentClient, lưu cục bộ |
| Similarity metric | Cosine similarity |
| Retrieval | Top-3 vector search |
| Web demo | Streamlit |

**Lệnh chạy pipeline:**

```powershell
cd starter
python -m src.run
```

**Lệnh chạy ứng dụng web:**

```powershell
python -m streamlit run app.py
```

Các vector được lưu trong thư mục `starter/chroma_db/`. Cơ sở dữ liệu này có thể được tạo lại bằng cách chạy pipeline.

**Chi phí:** Quá trình chạy sử dụng OpenAI Embedding API thật, số token tốn khá ít.

### 1.4. Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn

Các chunk được gắn các trường metadata:

| Trường | Ý nghĩa | Nguồn giá trị |
|---|---|---|
| `document_id` | Mã định danh tài liệu | Manifest |
| `source` | Đường dẫn nguồn PDF | Manifest |
| `page` | Trang vật lý PDF | PDF parser |
| `chapter` | Chương tương ứng | Manifest |
| `chunk_type` | Phương pháp chia chunk | Chunking pipeline |

Trường `chapter` được lựa chọn làm metadata filter vì corpus gồm hai chương có nội dung phân biệt được.

Khi câu hỏi yêu cầu tìm trong một chương cụ thể, cấu hình C có thể giới hạn phạm vi tìm kiếm theo giá trị `chapter`.

Giá trị chương không được mô hình AI tự suy đoán mà được lấy từ dữ liệu khai báo trong manifest.

---

## 2. Cấu hình và benchmark

### 2.1. Ba chiến lược A/B/C

Ba chiến lược sử dụng chung corpus, embedding model, vector database, cosine similarity và bộ câu hỏi benchmark.

**Strategy A — Fixed-size Chunking**

- Chia theo 500 ký tự mỗi chunk.
- Overlap 50 ký tự.
- Không sử dụng metadata filter trong truy xuất.
- Số chunk tạo ra: 224.

Đây là cấu hình baseline để so sánh.

**Strategy B — Paragraph Chunking**

- Chia theo ranh giới đoạn văn.
- Kích thước tối đa 700 ký tự.
- Không sử dụng overlap.
- Không sử dụng metadata filter.
- Số chunk tạo ra: 161.

Mục đích là đánh giá sự thay đổi chất lượng retrieval và coherence khi chuyển từ fixed-size sang paragraph chunking.

**Strategy C — Paragraph Chunking + Metadata Filter**

- Giữ nguyên toàn bộ cách chia chunk của B.
- Kích thước tối đa 700 ký tự.
- Không sử dụng overlap.
- Bổ sung metadata filter theo `chapter` khi câu hỏi có yêu cầu.
- Số chunk tạo ra: 161.

**Khác biệt duy nhất giữa B và C là việc áp dụng metadata filter ở bước truy xuất.** Điều này cho phép đánh giá ảnh hưởng của filtering mà không thay đổi dữ liệu chunk hoặc embedding model.

### 2.2. Bộ câu hỏi benchmark

Benchmark được lưu tại `benchmark/questions.json`, gồm **20 câu hỏi**:

- Q01–Q15: 15 câu thuộc tập dev.
- Q16–Q20: 5 câu thuộc tập test.

Bộ câu hỏi bao gồm dạng trực tiếp, diễn đạt lại và câu hỏi sử dụng metadata filter.

Có 4 câu hỏi có filter:

| Question ID | Split | Filter |
|---|---|---|
| Q06 | Dev | chapter = 1 |
| Q14 | Dev | chapter = 2 |
| Q17 | Test | chapter = 2 |
| Q20 | Test | chapter = 2 |

Mỗi câu hỏi có `gold_answer` và `gold_evidence`, bao gồm mã nguồn, trang PDF, đoạn bằng chứng và evidence anchor.

Trước khi truy xuất, chương trình kiểm tra evidence anchor có tồn tại trong văn bản đã chuẩn hóa của trang PDF tham chiếu hay không.

Việc kiểm tra tự động này giúp phát hiện gold không tồn tại trong nguồn, nhưng chưa thay thế được bước xác minh thủ công về mức độ đầy đủ của bằng chứng.

Một hạn chế của bộ câu hỏi là filter Chương 1 ở Q06 chưa được thể hiện trực tiếp trong câu hỏi. Trong thí nghiệm, giá trị filter được khai báo trong benchmark; nếu sử dụng trong môi trường thực tế, cần bảo đảm giá trị này đến từ người dùng hoặc ngữ cảnh trước truy xuất.

### 2.3. Tiêu chí lựa chọn chiến lược

Các tiêu chí được sử dụng để phân tích gồm:

1. **Retrieval Accuracy:** Hit@1 và Evidence Hit@3.
2. **Chunk Coherence:** Mức độ trọn ý và dễ hiểu của chunk.
3. **Metadata Usefulness:** Tính chính xác và khả năng lọc.
4. **Grounding Quality:** Mức độ đầy đủ của bằng chứng truy xuất.
5. **Data Strategy Impact:** Ảnh hưởng đến số chunk, thời gian và chi phí.

Ưu tiên phân tích là khả năng truy xuất evidence chính xác, tiếp theo là chất lượng chunk và metadata.

Tuy nhiên, chưa có bản ghi độc lập xác nhận tiêu chí lựa chọn cuối cùng đã được chốt trước khi xem tập test. Đây là hạn chế về quy trình thí nghiệm, cần được lưu ý khi diễn giải kết quả.

---

## 3. Kết quả

### 3.1. Retrieval Accuracy

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian ingest | Chi phí |
|---|---|---|---|---|---|---|
| A | Dev | 6/15 (40%) | 13/15 (86,67%) | 224 | 2,04s | Chưa ghi |
| A | Test | 2/5 (40%) | 4/5 (80%) | 224 | 2,04s | Chưa ghi |
| B | Dev | 7/15 (46,67%) | 10/15 (66,67%) | 161 | 1,74s | Chưa ghi |
| B | Test | 1/5 (20%) | 4/5 (80%) | 161 | 1,74s | Chưa ghi |
| C | Dev | 7/15 (46,67%) | 10/15 (66,67%) | 161 | 2,15s | Chưa ghi |
| C | Test | 1/5 (20%) | 4/5 (80%) | 161 | 2,15s | Chưa ghi |

**Nhận xét:**

- A có Evidence Hit@3 trên dev cao nhất, đạt 86,67%.
- B và C có Hit@1 dev cao hơn A một chút.
- Trên tập test, cả ba cấu hình có Evidence Hit@3 bằng 80%.
- B và C có kết quả retrieval tổng hợp giống nhau.
- Chưa có bằng chứng cho thấy metadata filter cải thiện Hit@3 trong thí nghiệm này.

Thời gian trong bảng là thời gian ingest được ghi nhận, không phải thời gian trả lời từng truy vấn.

### 3.2. Chunk count và tài nguyên

| Strategy | Số chunk | Tổng ký tự trong chunk | Ingest |
|---|---:|---:|---:|
| A | 224 | 98.531 | 2,04s |
| B | 161 | 90.229 | 1,74s |
| C | 161 | 90.229 | 2,15s |

So với A, B và C giảm 63 chunk, tương đương khoảng 28,1%.

Sự khác biệt về tổng ký tự một phần đến từ việc A sử dụng overlap, khiến văn bản giữa các chunk có thể bị lặp lại.

### 3.3. Manual Audit

Phần đánh giá thủ công được tổ chức trong `results/manual_audit.csv`.

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng (n/N) | Filter tuân thủ | Grounding 0/1/2 và trung bình /2 |
|---|---|---|---|---|
| A | Chưa chốt (10 mẫu) | Chưa xác minh (15 bản ghi) | 3/4 phù hợp tự nhiên | Chưa chốt (5 câu) |
| B | Chưa chốt (10 mẫu) | Chưa xác minh (15 bản ghi) | 2/4 phù hợp tự nhiên | Chưa chốt (5 câu) |
| C | Chưa chốt (10 mẫu) | Chưa xác minh (15 bản ghi) | 4/4 | Chưa chốt (5 câu) |

Các kết quả filter trên được đối chiếu từ trace.

A và B không áp dụng metadata filter, nên tỷ lệ tương ứng chỉ phản ánh việc kết quả tự nhiên nằm đúng chương được yêu cầu. C thực sự thực thi điều kiện lọc.

**Quy trình audit thủ công:**

- **Chunk Coherence:** Chọn 10 vị trí nội dung nguồn cố định và so sánh trên A/B/C, chấm 0–2 kèm lý do.
- **Metadata Correctness:** Kiểm tra top-3 của 5 câu test trên mỗi chiến lược, đối chiếu `source`, `page` và `chapter` với nguồn.
- **Grounding Quality:** Đọc top-3 cho 5 câu test ở từng chiến lược và chấm 0–2 theo độ đủ của bằng chứng.

Các điểm chưa được xác minh không được sử dụng để tính giá trị trung bình.

### 3.4. Đường dẫn trace, nhãn và cách chọn mẫu

| Minh chứng | Đường dẫn |
|---|---|
| Benchmark | `benchmark/questions.json` |
| Experiment log | `artifacts/experiment_log.csv` |
| Metrics | `results/metrics.json` |
| Top-3 traces | `results/traces.json` |
| Ingestion statistics | `results/ingestion_stats.json` |
| Manual audit | `results/manual_audit.csv` |

Đối với coherence, cùng 10 vị trí nguồn được lựa chọn để so sánh ba chiến lược. Đối với metadata và grounding, sử dụng toàn bộ 5 câu thuộc tập test.

Việc chọn mẫu theo cùng vị trí nguồn giúp giảm sai lệch khi so sánh các cấu hình chunking khác nhau.

---

## 4. Phân tích và kết luận

### 4.1. So sánh A–B

A sử dụng fixed-size chunking với overlap 50 ký tự, trong khi B chia theo đoạn văn với giới hạn 700 ký tự.

Kết quả cho thấy A tạo nhiều chunk hơn, nhưng có Evidence Hit@3 trên tập dev cao hơn B: **86,67% so với 66,67%**.

Điều này cho thấy fixed-size chunking đang hoạt động tốt hơn theo chỉ số retrieval top-3 trên tập dev hiện tại.

Tuy nhiên, A có nhược điểm là số chunk nhiều hơn và có nội dung lặp do overlap. Điều này có thể làm tăng khối lượng embedding và lưu trữ.

B giảm số chunk và thời gian ingest ghi nhận, nhưng chưa chứng minh được chất lượng retrieval tốt hơn A.

### 4.2. So sánh B–C

B và C sử dụng cùng phương pháp chia đoạn và số chunk.

Khác biệt duy nhất là C áp dụng metadata filtering khi truy vấn có điều kiện về chương.

Trong bốn câu có filter, C trả về các kết quả tuân thủ điều kiện chương ở toàn bộ top-3.

Tuy nhiên, các chỉ số Hit@1 và Evidence Hit@3 tổng hợp của B và C không thay đổi.

Như vậy, metadata filtering có tác dụng bảo đảm phạm vi tìm kiếm, nhưng trên bộ benchmark này chưa chứng minh được cải thiện độ chính xác retrieval.

### 4.3. Hai ví dụ truy xuất thất bại

**Ví dụ 1 — Q03: Tham số `end` của `print()`**

- **Câu hỏi:** How do you prevent print() from automatically starting a new line?
- **Nguồn tham chiếu:** OpenStax, trang vật lý PDF 21, Chương 1.
- **Đáp án kỳ vọng:** Sử dụng tham số `end`.
- **Kết quả:** A/B/C đều không tìm được gold evidence trong top-3 theo phép kiểm tra tự động.

Các kết quả truy xuất có nội dung liên quan đến hàm `print()`, nhưng không tìm được đoạn evidence tham chiếu đủ để hệ thống đánh dấu đúng.

Điều này thể hiện hạn chế khi các chunk cùng chủ đề được xếp hạng cao hơn đoạn chứa bằng chứng cần tìm.

**Ví dụ 2 — Q08: Định nghĩa Python string**

- **Câu hỏi:** How does the book define a Python string?
- **Nguồn tham chiếu:** OpenStax, trang vật lý PDF 26, Chương 1.
- **Đáp án kỳ vọng:** Chuỗi là dãy ký tự được bao bởi dấu nháy đơn hoặc nháy kép phù hợp.
- **Kết quả:** A/B/C đều không đạt Evidence Hit@3 theo kiểm tra tự động.

Một số đoạn truy xuất thuộc chủ đề Python string hoặc cú pháp, nhưng không chứa đoạn định nghĩa tham chiếu.

Trường hợp này cho thấy semantic similarity không phải lúc nào cũng xếp đoạn định nghĩa chính xác lên top-3.

### 4.4. Chiến lược lựa chọn, đánh đổi và điều kiện áp dụng

Từ các kết quả hiện có:

- **A** phù hợp hơn khi ưu tiên Evidence Hit@3 trên tập dev và chấp nhận số chunk lớn hơn.
- **B** có ưu điểm giảm số chunk, phù hợp khi ưu tiên dữ liệu gọn hơn và cần tiếp tục kiểm tra coherence.
- **C** phù hợp khi câu hỏi yêu cầu giới hạn tìm kiếm theo chương hoặc metadata đáng tin cậy.

Nếu cần chọn một cấu hình theo kết quả retrieval dev hiện tại, **A là ứng viên được ưu tiên**.

Tuy nhiên, lựa chọn này chỉ mang tính kết luận trong phạm vi benchmark hiện có, chưa phải kết luận về chất lượng toàn diện. Kết quả audit thủ công và phép đo chi phí cần được bổ sung trước khi chốt lựa chọn cuối cùng.

### 4.5. Hạn chế

Thí nghiệm còn một số hạn chế:

1. Corpus chỉ gồm hai chương của một tài liệu, chưa đại diện cho dữ liệu đa nguồn.
2. Tập test có 5 câu, nên một câu đúng hoặc sai đã làm thay đổi tỷ lệ 20 điểm phần trăm.
3. Một số evidence anchor không bao quát toàn bộ thông tin của đáp án kỳ vọng.
4. PDF parsing có thể làm mất ranh giới đoạn hoặc cắt ngang ngữ cảnh.
5. Manual audit chưa được hoàn thiện và xác nhận đầy đủ.
6. Chưa đo chính xác embedding tokens, chi phí API và thời gian retrieval riêng biệt.
7. Chưa có bằng chứng độc lập về việc khóa tiêu chí chọn chiến lược trước khi xem kết quả test.

Do những hạn chế trên, cần thận trọng khi khái quát kết quả.

### 4.6. Hướng cải tiến

Nếu tiếp tục phát triển bài thực hành, các hướng cải tiến gồm:

1. Làm sạch header, footer và ranh giới đoạn PDF trước khi chunking.
2. Thử nghiệm sentence-aware hoặc section-aware chunking.
3. Bổ sung kiểm tra các evidence tương đương thay vì chỉ đối sánh một anchor.
4. Hoàn thiện audit thủ công và mở rộng bộ test.
5. Ghi log số token, chi phí API và thời gian retrieval.
6. Bổ sung kiểm tra tự động tính đúng đắn của metadata và gold evidence.
7. Phát triển web app Streamlit để hỗ trợ kiểm thử truy xuất và xem nhật ký chạy trực tiếp.

### 4.7. Kết luận

Bài thực hành đã xây dựng được một pipeline xử lý dữ liệu PDF và truy xuất vector sử dụng **PyMuPDF, OpenAI Embedding và ChromaDB**.

Ba chiến lược A/B/C đã được chạy trên cùng corpus và bộ benchmark 20 câu hỏi.

Kết quả cho thấy fixed-size chunking của A đạt Evidence Hit@3 trên tập dev cao nhất, trong khi paragraph chunking giảm số lượng chunk. Metadata filtering ở cấu hình C giúp bảo đảm giới hạn phạm vi truy xuất theo chương nhưng chưa cải thiện các chỉ số retrieval tổng hợp.

Qua thí nghiệm, bài học chính là chất lượng hệ thống truy xuất không chỉ phụ thuộc vào embedding model, mà còn chịu ảnh hưởng từ phương pháp xử lý tài liệu, cách chia chunk, metadata và chất lượng bộ đánh giá.

Cần tiếp tục hoàn thiện manual audit và đo chi phí để đưa ra kết luận lựa chọn chiến lược có độ tin cậy cao hơn.
