# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import io

# ==========================================
# CẤU HÌNH TRANG STREAMLIT
# ==========================================
st.set_page_config(page_title="Lead Scoring", page_icon="🎯", layout="wide")

st.title("🎯 LEAD SCORING AUTOMATION")
st.markdown("""
Hệ thống chấm điểm khách hàng tự động. **Hot Leads** sẽ được đánh dấu màu đỏ để ưu tiên chăm sóc.
""")

# ==========================================
# HÀM XỬ LÝ & CHẤM ĐIỂM
# ==========================================
def get_sheet_csv_url(sheet_url):
    try:
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        gid = "0"
        if "gid=" in sheet_url: gid = sheet_url.split("gid=")[1].split("&")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    except:
        return sheet_url

def score_lead_logic(nhu_cau):
    if not nhu_cau or pd.isna(nhu_cau):
        return 0, "WARM", "Không có dữ liệu"
        
    text = str(nhu_cau).lower()
    score = 0
    reasons = []
    
    # VIP Keywords
    vip_keywords = ["20 tỷ", "tài chính mạnh", "không thành vấn đề", "biệt thự", "penthouse", "shophouse", "đất công nghiệp", "sàn văn phòng", "quận 1", "ven sông", "vinhomes", "phú mỹ hưng", "chủ doanh nghiệp", "nhà đầu tư", "mua sỉ", "pháp lý chuẩn", "sổ hồng riêng"]
    found_vip = [kw for kw in vip_keywords if kw in text]
    if found_vip:
        score += 50
        reasons.append(f"VIP: {', '.join(found_vip)}")

    # Junk Keywords
    junk_keywords = ["nhầm số", "không có nhu cầu", "dữ liệu cũ", "nhầm ngành", "hỏi giá cho vui", "chưa có ý định mua", "bảo hiểm", "vay vốn", "thuê bao", "không bắt máy"]
    found_junk = [kw for kw in junk_keywords if kw in text]
    if found_junk:
        score -= 50
        reasons.append(f"JUNK: {', '.join(found_junk)}")
        
    if score == 0:
        score = 10
        reasons.append("Tiềm năng nhẹ")

    category = "WARM"
    if score >= 50: category = "HOT"
    elif score < 0: category = "JUNK"
    
    return score, category, " | ".join(reasons)

def highlight_hot(row):
    """Tô màu đỏ cho các dòng là HOT lead"""
    return ['background-color: #ffcccc' if row['Phân Loại'] == 'HOT' else '' for _ in row]

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.header("⚙️ Cấu Hình")
    sheet_link = st.text_input("Link Google Sheet", value="https://docs.google.com/spreadsheets/d/1shHeQX2HyHIo8VDgtS7ac3hpvzaIV9xLxDDaV3yLoxQ/edit?gid=0#gid=0")
    col_name = st.text_input("Tên cột Nhu cầu", value="nhu_cau_mo_ta")
    load_btn = st.button("📥 Tải Dữ Liệu")

# ==========================================
# APP CHÍNH
# ==========================================
if "df" not in st.session_state:
    st.session_state.df = None

if load_btn:
    try:
        csv_url = get_sheet_csv_url(sheet_link)
        st.session_state.df = pd.read_csv(csv_url)
        st.success("Tải dữ liệu thành công!")
    except Exception as e:
        st.error(f"Lỗi: {e}")

if st.session_state.df is not None:
    df = st.session_state.df
    
    st.subheader("📊 Dữ liệu gốc")
    st.dataframe(df.head(10))
    
    if st.button("🚀 CHẠY CHẤM ĐIỂM", type="primary"):
        if col_name not in df.columns:
            st.error(f"Không tìm thấy cột '{col_name}'")
        else:
            results = [score_lead_logic(val) for val in df[col_name]]
            df['Điểm Số'], df['Phân Loại'], df['Lý Do'] = zip(*results)
            st.session_state.df = df
            st.success("Đã chấm điểm xong!")

    if 'Phân Loại' in df.columns:
        # --- BỘ LỌC ---
        st.divider()
        st.subheader("🔍 Bộ lọc & Kết quả")
        
        # Thống kê nhanh
        col1, col2, col3 = st.columns(3)
        col1.metric("🔥 HOT", len(df[df['Phân Loại'] == 'HOT']))
        col2.metric("⚖️ WARM", len(df[df['Phân Loại'] == 'WARM']))
        col3.metric("🗑️ JUNK", len(df[df['Phân Loại'] == 'JUNK']))
        
        # Filter UI
        filter_cat = st.multiselect("Lọc theo trạng thái:", options=["HOT", "WARM", "JUNK"], default=["HOT", "WARM", "JUNK"])
        
        filtered_df = df[df['Phân Loại'].isin(filter_cat)]
        
        # Hiển thị bảng có màu sắc
        st.markdown("**Bảng kết quả (Dòng màu đỏ là HOT Lead):**")
        styled_df = filtered_df.style.apply(highlight_hot, axis=1)
        st.dataframe(styled_df, use_container_width=True)
        
        # Kiểm duyệt & Sửa
        with st.expander("✏️ Chỉnh sửa thủ công & Xuất file"):
            edited_df = st.data_editor(df, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                edited_df.to_excel(writer, index=False)
            
            st.download_button("⬇️ Tải file Excel", data=output.getvalue(), file_name="lead_scoring_results.xlsx")
