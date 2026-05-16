# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import json
import io

# ==========================================
# CẤU HÌNH TRANG STREAMLIT
# ==========================================
st.set_page_config(page_title="Lead Scoring Web App", page_icon="🎯", layout="wide")

st.title("🎯 LEAD SCORING AUTOMATION (PYTHON ONLY)")
st.markdown("""
Ứng dụng sử dụng **Quy tắc Python** để tự động đọc thông tin khách hàng từ Google Sheets, 
chấm điểm tiềm năng (Lead Scoring) dựa trên bộ quy tắc nghiệp vụ. 
**Không yêu cầu OpenAI API Key.**
""")

# ==========================================
# HÀM XỬ LÝ DỮ LIỆU & CHẤM ĐIỂM (PYTHON RULES)
# ==========================================
def get_sheet_csv_url(sheet_url):
    """Chuyển đổi link Google Sheet thông thường sang link tải CSV (yêu cầu Sheet được share Public)"""
    if "export?format=csv" in sheet_url:
        return sheet_url
    try:
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        gid = "0"
        if "gid=" in sheet_url:
            gid = sheet_url.split("gid=")[1].split("&")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    except Exception as e:
        return sheet_url

def score_lead_rule_based(nhu_cau):
    """Chấm điểm lead dựa trên bộ quy tắc nghiệp vụ (Python logic)"""
    if not nhu_cau or pd.isna(nhu_cau):
        return 0, "WARM", "Không có dữ liệu nhu cầu"
        
    nhu_cau_lower = str(nhu_cau).lower()
    score = 0
    reasons = []
    
    # 1. TIÊU CHÍ CỘNG 50 ĐIỂM (KHÁCH VIP)
    vip_keywords = [
        "20 tỷ", "tài chính mạnh", "không thành vấn đề", 
        "biệt thự đơn lập", "penthouse", "shophouse mặt đường", "đất công nghiệp", "sàn văn phòng",
        "quận 1", "ven sông", "vinhomes ocean park", "phú mỹ hưng",
        "chủ doanh nghiệp", "nhà đầu tư chuyên nghiệp", "mua sỉ", "mua số lượng lớn",
        "pháp lý chuẩn", "sổ hồng riêng", "gặp trực tiếp chủ đầu tư"
    ]
    
    found_vip = [kw for kw in vip_keywords if kw in nhu_cau_lower]
    if found_vip:
        score += 50
        reasons.append(f"VIP: {', '.join(found_vip)}")

    # 2. TIÊU CHÍ TRỪ 50 ĐIỂM (KHÁCH RÁC)
    junk_keywords = [
        "nhầm số", "không có nhu cầu", "dữ liệu cũ", "nhầm ngành", 
        "hỏi giá cho vui", "chưa có ý định mua", "thái độ không hợp tác",
        "bảo hiểm", "vay vốn", "mời chào dịch vụ",
        "thuê bao", "không bắt máy", "không phản hồi zalo"
    ]
    
    # Kiểm tra yêu cầu phi thực tế (VD: Quận 1 giá rẻ)
    unrealistic = False
    if ("quận 1" in nhu_cau_lower or "q1" in nhu_cau_lower) and ("1 tỷ" in nhu_cau_lower or "2 tỷ" in nhu_cau_lower or "vài trăm triệu" in nhu_cau_lower):
        unrealistic = True
        reasons.append("Yêu cầu phi thực tế (Q1 giá rẻ)")

    found_junk = [kw for kw in junk_keywords if kw in nhu_cau_lower]
    if found_junk or unrealistic:
        score -= 50
        if found_junk:
            reasons.append(f"JUNK: {', '.join(found_junk)}")
        
    # 3. TRƯỜNG HỢP KHÁC
    if score == 0:
        warm_keywords = ["chung cư", "nhà phố", "3-10 tỷ", "vay ngân hàng", "tư vấn"]
        found_warm = [kw for kw in warm_keywords if kw in nhu_cau_lower]
        if found_warm:
            score += 10
            reasons.append(f"Tiềm năng: {', '.join(found_warm)}")
        else:
            reasons.append("Nhu cầu thông thường")

    # Phân loại
    category = "WARM"
    if score >= 50:
        category = "VIP"
    elif score < 0:
        category = "JUNK"
        
    return score, category, " | ".join(reasons)


# ==========================================
# SIDEBAR: CẤU HÌNH
# ==========================================
with st.sidebar:
    st.header("⚙️ Cấu Hình")
    st.success("Hệ thống đang chạy bằng quy tắc Python trực tiếp.")
    
    default_sheet = "https://docs.google.com/spreadsheets/d/1shHeQX2HyHIo8VDgtS7ac3hpvzaIV9xLxDDaV3yLoxQ/edit?gid=0#gid=0"
    sheet_link = st.text_input("Google Sheet Link (Public)", value=default_sheet)
    
    # Tự động gợi ý tên cột nhu_cau_mo_ta từ screenshot
    col_name = st.text_input("Tên cột chứa Nhu cầu", value="nhu_cau_mo_ta")
    
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
            st.error(f"Lỗi tải dữ liệu: Đảm bảo link sheet là Public. Chi tiết lỗi: {e}")

# 2. Hiển thị & Chấm điểm
if st.session_state.df is not None:
    df = st.session_state.df
    
    st.subheader("📊 Dữ liệu khách hàng")
    st.dataframe(df)
    
    if st.button("🚀 Bắt đầu Chấm Điểm", type="primary"):
        if col_name not in df.columns:
            st.error(f"Không tìm thấy cột '{col_name}' trong dữ liệu. Các cột hiện có: {', '.join(df.columns)}. Vui lòng nhập đúng tên cột vào Sidebar.")
        else:
            # Khởi tạo cột mới nếu chưa có
            if 'Điểm Số' not in df.columns:
                df['Điểm Số'] = 0
                df['Phân Loại'] = ""
                df['Lý Do Chấm Điểm'] = ""
            
            progress_text = "Đang phân tích..."
            my_bar = st.progress(0, text=progress_text)
            
            total_rows = len(df)
            
            for index, row in df.iterrows():
                nhu_cau = row[col_name]
                score, category, reason = score_lead_rule_based(nhu_cau)
                df.at[index, 'Điểm Số'] = score
                df.at[index, 'Phân Loại'] = category
                df.at[index, 'Lý Do Chấm Điểm'] = reason
                
                # Cập nhật thanh tiến trình
                progress = (index + 1) / total_rows
                my_bar.progress(progress, text=f"{progress_text} ({index + 1}/{total_rows})")
            
            st.session_state.df = df
            st.success("✨ Đã hoàn thành chấm điểm!")

# 3. Human-in-the-loop: Kiểm duyệt và Chỉnh sửa
if st.session_state.df is not None and 'Điểm Số' in st.session_state.df.columns:
    st.subheader("🕵️ Kiểm duyệt kết quả")
    
    # Cho phép chỉnh sửa bảng dữ liệu trực tiếp
    edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
    st.session_state.df = edited_df

    # 4. Xuất Excel
    st.subheader("📥 Xuất dữ liệu")
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        edited_df.to_excel(writer, index=False, sheet_name='Results')
    excel_data = output.getvalue()
    
    st.download_button(
        label="⬇️ Tải xuống File Excel",
        data=excel_data,
        file_name='Ket_Qua_Lead_Scoring.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        type="primary"
    )
