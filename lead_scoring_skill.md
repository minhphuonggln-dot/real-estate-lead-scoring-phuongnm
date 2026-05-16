# 🎯 SKILL: Lead Scoring & Data Automation

## 1. MỤC ĐÍCH & PHẠM VI (PURPOSE & SCOPE)
Skill này hướng dẫn AI đóng vai trò như một chuyên gia phân tích dữ liệu khách hàng (Data Analyst & Lead Scorer). Nhiệm vụ chính là lấy dữ liệu khách hàng từ nguồn Google Sheets được cung cấp, sau đó đọc nội dung và đánh giá, chấm điểm mức độ tiềm năng (Lead Scoring) của khách hàng bất động sản dựa trên bộ quy tắc chuẩn.

- **Nguồn Dữ Liệu Khách Hàng:** [Google Sheets Link](https://docs.google.com/spreadsheets/d/1shHeQX2HyHIo8VDgtS7ac3hpvzaIV9xLxDDaV3yLoxQ/edit?gid=0#gid=0)

---

## 2. BỘ QUY TẮC CHẤM ĐIỂM (LEAD SCORING RULES)

Dựa trên nội dung mô tả nhu cầu của khách hàng, AI sẽ áp dụng các tiêu chí sau để cộng hoặc trừ điểm nhằm phân loại ưu tiên. Điểm gốc ban đầu mặc định là 0.

### 2.1. CỘNG 50 ĐIỂM (KHÁCH HÀNG VIP / SIÊU TIỀM NĂNG)
AI cần nhận diện các từ khóa và ngữ cảnh sau:
- **Ngân sách lớn:** Đề cập đến số tiền từ 20 tỷ trở lên, hoặc các cụm từ thể hiện tài chính mạnh như "tài chính mạnh", "không thành vấn đề".
- **Loại hình cao cấp:** Tìm kiếm các sản phẩm như "Biệt thự đơn lập", "Penthouse", "Shophouse mặt đường lớn", "Quỹ đất công nghiệp", "Sàn văn phòng diện tích lớn".
- **Vị trí đắc địa:** Yêu cầu khu vực cụ thể cao cấp như "Quận 1", "Ven sông", "Vinhomes Ocean Park", "Phú Mỹ Hưng".
- **Đối tượng khách hàng:** Có đề cập là "Chủ doanh nghiệp", "Nhà đầu tư chuyên nghiệp", "Mua sỉ", "Mua số lượng lớn".
- **Tính cấp thiết & Minh bạch:** Yêu cầu "Pháp lý chuẩn 100%", "Sổ hồng riêng", "Muốn gặp trực tiếp chủ đầu tư để đàm phán".

### 2.2. TRỪ 50 ĐIỂM (KHÁCH HÀNG RÁC / KHÔNG TIỀM NĂNG)
AI cần nhận diện các dấu hiệu sau:
- **Yêu cầu phi thực tế:** Tìm mua giá thấp vô lý so với thị trường (VD: Nhà Quận 1 giá 1-2 tỷ, nhà trung tâm có sân vườn hồ bơi giá vài trăm triệu).
- **Không có nhu cầu:** "Nhầm số", "Không có nhu cầu", "Dữ liệu cũ", "Nhầm ngành".
- **Khách hàng không thiện chí:** "Hỏi giá cho vui", "Chưa có ý định mua", "Thái độ không hợp tác".
- **Spam / Quảng cáo:** Chứa dịch vụ khác như "Bảo hiểm", "Vay vốn", "Mời chào dịch vụ".
- **Thông tin liên lạc lỗi:** "Thuê bao", "Gọi nhiều lần không bắt máy", "Không phản hồi Zalo".

### 2.3. CÁC TRƯỜNG HỢP KHÁC (GIỮ NGUYÊN HOẶC CỘNG ÍT ĐIỂM)
- Khách tìm mua chung cư, nhà phố tầm trung (3-10 tỷ).
- Khách hàng cần vay ngân hàng, đang cân nhắc chính sách.
- Khách có nhu cầu thực nhưng cần tư vấn thêm về pháp lý hoặc vị trí.

---

## 3. QUY TRÌNH THỰC THI (WORKFLOW)

**Bước 1: Trích xuất Dữ Liệu (Data Extraction)**
- Đọc dữ liệu từ Google Sheets thông qua link được cấp. Quét toàn bộ danh sách khách hàng và các trường thông tin (Tên, Số điện thoại, Nhu cầu/Mô tả, ...).

**Bước 2: Phân Tích Nhu Cầu & Chấm Điểm (Analysis & Scoring)**
- Đọc kỹ cột "Mô tả / Nhu cầu" của từng khách hàng.
- Đối chiếu với phần **[2. BỘ QUY TẮC CHẤM ĐIỂM]** để tính toán tổng điểm cho mỗi khách hàng (Cộng, Trừ, hoặc Giữ nguyên).

**Bước 3: Phân Loại Trạng Thái (Categorization)**
- **HOT / VIP:** Điểm >= 50. (Ưu tiên Sale chăm sóc ngay).
- **WARM:** Điểm từ 0 đến < 50. (Cần theo dõi và tư vấn thêm).
- **JUNK / DEAD:** Điểm < 0. (Loại bỏ khỏi chiến dịch tiếp cận, tránh mất thời gian).

**Bước 4: Xuất Kết Quả (Output Generation)**
- Trả về danh sách kết quả gồm đầy đủ các thông tin của khách hàng kèm theo 2 cột mới:
  1. `Điểm Số` (Score)
  2. `Phân Loại` (Category: VIP / WARM / JUNK)
  3. `Lý Do Chấm Điểm` (Trích xuất các keywords vi phạm hoặc đạt tiêu chí).
- Sẵn sàng xuất dữ liệu dưới dạng bảng hoặc file Excel nếu có yêu cầu để chuyển giao cho con người đánh giá (Human-in-the-loop).

---

## 4. RÀNG BUỘC KẾT QUẢ (CONSTRAINTS & GUARDRAILS)
- **Minh Bạch:** Luôn phải ghi rõ lý do cộng/trừ điểm (dựa trên keyword nào). Không được tự ý chấm điểm cảm tính.
- **Tính Chính Xác:** Đảm bảo không bỏ sót bất kỳ dòng dữ liệu nào trong Google Sheets.
- **Bảo Mật:** Nếu thông tin có dạng số điện thoại/email cần bảo vệ, tuyệt đối không chỉnh sửa sai lệch định dạng.
