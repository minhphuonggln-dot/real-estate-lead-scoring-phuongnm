import streamlit as st
import pandas as pd
import json
import io
from openai import OpenAI

# ==========================================
# CẤU HÌNH TRANG STREAMLIT
# ==========================================
st.set_page_config(page_title="Lead Scoring Web App", page_icon="🎯", layout="wide")

st.title("🎯 AI Lead Scoring & Automation - Ngành Bất Động Sản")
st.markdown("""
Ứng dụng sử dụng AI để tự động đọc thông tin khách hàng từ Google Sheets, 
chấm điểm tiềm năng (Lead Scoring) dựa trên bộ quy tắc nghiệp vụ và cho phép kiểm duyệt trước khi xuất file.
""")

# ==========================================
# HÀM XỬ LÝ DỮ LIỆU & AI
# ==========================================
def get_sheet_csv_url(sheet_url):
    """Chuyển đổi link Google Sheet thông thường sang link tải CSV (yêu cầu Sheet được share Public)"""
    if "export?format=csv" in sheet_url:
        return sheet_url
    try:
        # Lấy ID của sheet
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        # Lấy gid nếu có
        gid = "0"
        if "gid=" in sheet_url:
            gid = sheet_url.split("gid=")[1].split("&")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    except Exception as e:
        return sheet_url

def score_lead_with_ai(client, nhu_cau):
    """Gọi OpenAI API để chấm điểm lead dựa trên rule"""
    prompt = f"""
    Bạn là một chuyên gia Data Analyst & Lead Scorer trong ngành Bất Động Sản.
    Nhiệm vụ: Chấm điểm khách hàng tiềm năng dựa trên thông tin "Nhu cầu" của họ. Điểm gốc là 0.

    QUY TẮC CHẤM ĐIỂM:
    1. CỘNG 50 ĐIỂM (KHÁCH VIP): 
       - Ngân sách >= 20 tỷ, tài chính mạnh, không thành vấn đề.
       - Tìm: Biệt thự đơn lập, Penthouse, Shophouse mặt đường lớn, Quỹ đất công nghiệp, Sàn văn phòng diện tích lớn.
       - Vị trí: Quận 1, Ven sông, Vinhomes Ocean Park, Phú Mỹ Hưng.
       - Khách là: Chủ doanh nghiệp, Nhà đầu tư chuyên nghiệp, Mua sỉ, Mua số lượng lớn.
       - Yêu cầu: Pháp lý chuẩn 100%, Sổ hồng riêng, Muốn gặp trực tiếp chủ đầu tư để đàm phán.
    
    2. TRỪ 50 ĐIỂM (KHÁCH RÁC):
       - Yêu cầu phi thực tế (VD: Nhà Quận 1 giá 1-2 tỷ, biệt thự trung tâm vài trăm triệu).
       - Không có nhu cầu (Nhầm số, dữ liệu cũ, nhầm ngành).
       - Không thiện chí (Hỏi giá cho vui, chưa có ý định mua, thái độ không hợp tác).
       - Spam/Quảng cáo (Bảo hiểm, Vay vốn, Mời chào dịch vụ).
       - Liên lạc lỗi (Thuê bao, không bắt máy, không phản hồi Zalo).
    
    3. GIỮ NGUYÊN HOẶC CỘNG ÍT ĐIỂM (Các trường hợp khác):
       - Khách tìm chung cư, nhà phố 3-10 tỷ (Cộng 10 điểm).
       - Khách cần vay ngân hàng (Cộng 5 điểm).
       - Nhu cầu thực nhưng cần tư vấn thêm (Cộng 5 điểm).

    PHÂN LOẠI:
    - HOT / VIP: Điểm >= 50
    - WARM: Điểm từ 0 đến < 50
    - JUNK / DEAD: Điểm < 0

    Nhu cầu của khách hàng hiện tại: "{nhu_cau}"

    Trả về định dạng JSON thuần túy (không bọc trong markdown) với cấu trúc sau:
    {{
        "score": (số nguyên),
        "category": "VIP" hoặc "WARM" hoặc "JUNK",
        "reason": "Lý do cộng/trừ điểm chi tiết dựa trên từ khóa nào"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Hoặc gpt-4o
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={ "type": "json_object" }
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("score", 0), result.get("category", "WARM"), result.get("reason", "Không xác định")
    except Exception as e:
        return 0, "ERROR", str(e)


# ==========================================
# SIDEBAR: CẤU HÌNH
# ==========================================
with st.sidebar:
    st.header("⚙️ Cấu Hình Hệ Thống")
    api_key = st.text_input("OpenAI API Key", type="password", help="Nhập API key của OpenAI để sử dụng AI")
    
    default_sheet = "https://docs.google.com/spreadsheets/d/1shHeQX2HyHIo8VDgtS7ac3hpvzaIV9xLxDDaV3yLoxQ/edit?gid=0#gid=0"
    sheet_link = st.text_input("Google Sheet Link (Public)", value=default_sheet)
    
    col_name = st.text_input("Tên cột chứa Nhu cầu/Mô tả", value="Nhu cầu")
    
    load_btn = st.button("📥 Tải Dữ Liệu")

# ==========================================
# MAIN APP
# ==========================================
if "df" not in st.session_state:
    st.session_state.df = None

# 1. Tải Dữ Liệu
if load_btn:
    if not sheet_link:
        st.error("Vui lòng nhập link Google Sheet.")
    else:
        try:
            csv_url = get_sheet_csv_url(sheet_link)
            df = pd.read_csv(csv_url)
            st.session_state.df = df
            st.success("✅ Tải dữ liệu thành công!")
        except Exception as e:
            st.error(f"Lỗi tải dữ liệu: Đảm bảo link sheet là Public (Bất kỳ ai có đường liên kết đều có thể xem). Chi tiết lỗi: {e}")

# 2. Hiển thị & Chấm điểm
if st.session_state.df is not None:
    df = st.session_state.df
    
    st.subheader("📊 Dữ liệu khách hàng")
    st.dataframe(df.head(10)) # Hiển thị một số dòng đầu
    
    if st.button("🚀 Chạy AI Lead Scoring", type="primary"):
        if not api_key:
            st.warning("Vui lòng nhập OpenAI API Key ở Sidebar trước khi chạy AI.")
        elif col_name not in df.columns:
            st.error(f"Không tìm thấy cột '{col_name}' trong dữ liệu. Các cột hiện có: {', '.join(df.columns)}")
        else:
            client = OpenAI(api_key=api_key)
            
            # Khởi tạo cột mới nếu chưa có
            if 'Điểm Số' not in df.columns:
                df['Điểm Số'] = 0
                df['Phân Loại'] = ""
                df['Lý Do Chấm Điểm'] = ""
            
            progress_text = "Đang phân tích và chấm điểm..."
            my_bar = st.progress(0, text=progress_text)
            
            total_rows = len(df)
            
            for index, row in df.iterrows():
                nhu_cau = str(row[col_name])
                if pd.notna(nhu_cau) and nhu_cau.strip() != "":
                    score, category, reason = score_lead_with_ai(client, nhu_cau)
                    df.at[index, 'Điểm Số'] = score
                    df.at[index, 'Phân Loại'] = category
                    df.at[index, 'Lý Do Chấm Điểm'] = reason
                
                # Cập nhật thanh tiến trình
                progress = (index + 1) / total_rows
                my_bar.progress(progress, text=f"{progress_text} ({index + 1}/{total_rows})")
            
            st.session_state.df = df
            st.success("✨ Đã hoàn thành chấm điểm AI!")

# 3. Human-in-the-loop: Kiểm duyệt và Chỉnh sửa
if st.session_state.df is not None and 'Điểm Số' in st.session_state.df.columns:
    st.subheader("🕵️ Kiểm duyệt kết quả (Human-in-the-loop)")
    st.markdown("Bạn có thể chỉnh sửa trực tiếp trên bảng dữ liệu bên dưới trước khi xuất file.")
    
    # Cho phép chỉnh sửa bảng dữ liệu trực tiếp
    edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
    
    # Cập nhật lại session_state với dữ liệu đã sửa
    st.session_state.df = edited_df

    # 4. Xuất Excel
    st.subheader("📥 Xuất dữ liệu bàn giao")
    
    # Tạo in-memory buffer cho file Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        edited_df.to_excel(writer, index=False, sheet_name='Lead Scoring Results')
    excel_data = output.getvalue()
    
    st.download_button(
        label="⬇️ Tải xuống File Excel",
        data=excel_data,
        file_name='Lead_Scoring_Ket_Qua.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        type="primary"
    )
