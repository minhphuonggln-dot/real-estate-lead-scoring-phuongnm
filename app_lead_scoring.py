# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import gspread
# pyrefly: ignore [missing-import]
from google.oauth2.service_account import Credentials
import io
import time

# ==========================================
# 1. CẤU HÌNH TRANG & GIAO DIỆN (UI/UX)
# ==========================================
st.set_page_config(page_title="MindX AI Lead Scoring", page_icon="🎯", layout="wide")

# Custom CSS cho giao diện chuyên nghiệp (Branding MindX)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #ed1c24; /* Màu đỏ MindX */
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #333;
    }
    .vip-row {
        background-color: #ffebee !important;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ed1c24;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# SIDEBAR: Logo & Thông tin
with st.sidebar:
    # Logo MindX (Sử dụng URL placeholder nếu không có file local)
    st.image("https://mindx.edu.vn/images/logo.png", width=200)
    st.divider()
    st.header("⚙️ Cấu Hình Hệ Thống")
    
    # Link Sheet - Chuyển sang nhập Spreadsheet Name hoặc ID vì dùng Service Account
    sheet_name = st.text_input("Tên/ID Spreadsheet", value="Lead Scoring Data")
    col_name = st.text_input("Tên cột Nhu cầu", value="nhu_cau_mo_ta")
    
    st.info("💡 Sheet đã được share quyền cho: `lead-scoring-robot-phuongnm@neat-element-496514-c8.iam.gserviceaccount.com`")
    
    load_btn = st.button("📥 TẢI DỮ LIỆU")

# ==========================================
# 2. XỬ LÝ DỮ LIỆU & GOOGLE SHEETS API
# ==========================================
def connect_to_gsheet(sheet_id_or_name):
    """Kết nối với Google Sheets qua Service Account"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        # Load credentials từ file local
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        client = gspread.authorize(creds)
        
        # Mở bằng ID hoặc Tên
        try:
            sh = client.open_by_key(sheet_id_or_name)
        except:
            sh = client.open(sheet_id_or_name)
            
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets: {e}")
        return None

def score_lead_logic(nhu_cau):
    """Logic chấm điểm chuẩn nghiệp vụ BĐS & Spa"""
    if not nhu_cau or pd.isna(nhu_cau):
        return 0, "WARM", "Trống"
        
    text = str(nhu_cau).lower()
    score = 0
    reasons = []
    
    # VIP Keywords (+50đ)
    vip_keywords = ["20 tỷ", "tài chính mạnh", "biệt thự", "penthouse", "shophouse", "quận 1", "ven sông", "vinhomes", "phú mỹ hưng", "mua sỉ", "sổ hồng riêng"]
    found_vip = [kw for kw in vip_keywords if kw in text]
    if found_vip:
        score += 50
        reasons.append(f"🏠 VIP: {', '.join(found_vip)}")

    # Junk Keywords (-50đ)
    junk_keywords = ["nhầm số", "không nhu cầu", "dữ liệu cũ", "hỏi giá cho vui", "bảo hiểm", "vay vốn", "thuê bao", "không bắt máy"]
    found_junk = [kw for kw in junk_keywords if kw in text]
    if found_junk:
        score -= 50
        reasons.append(f"🗑️ JUNK: {', '.join(found_junk)}")
        
    if score == 0:
        score = 10
        reasons.append("⚖️ Tiềm năng trung bình")

    category = "WARM"
    if score >= 50: category = "VIP"
    elif score < 0: category = "JUNK"
    
    return score, category, " | ".join(reasons)

def highlight_rows(row):
    """Tô màu cho bảng: VIP - Đỏ nhạt, JUNK - Xám nhẹ"""
    if row['Phân Loại'] == 'VIP':
        return ['background-color: #ffcccc'] * len(row)
    elif row['Phân Loại'] == 'JUNK':
        return ['background-color: #f0f0f0'] * len(row)
    return [''] * len(row)

# ==========================================
# 3. LUỒNG THỰC THI CHÍNH (MAIN WORKFLOW)
# ==========================================
st.title("🚀 AI LEAD SCORING & AUDIT DASHBOARD")
st.markdown("Hệ thống kiểm soát chất lượng Lead tự động - MindX Technology School")
st.divider()

if "df" not in st.session_state:
    st.session_state.df = None

# --- BƯỚC 1: LOAD DỮ LIỆU ---
if load_btn:
    with st.spinner("Đang kết nối Secure Google Sheets..."):
        df = connect_to_gsheet(sheet_name)
        if df is not None:
            st.session_state.df = df
            st.success("✅ Đã kết nối dữ liệu bảo mật thành công!")

# --- BƯỚC 2: HIỂN THỊ & XỬ LÝ ---
if st.session_state.df is not None:
    df = st.session_state.df
    
    # Hiển thị Metrics Dashboard như trong ảnh hướng dẫn
    st.subheader("📋 Dashboard Metrics")
    m1, m2, m3 = st.columns(3)
    
    # Giả lập hoặc tính toán số liệu nếu đã chấm điểm
    total = len(df)
    m1.metric("Tổng khách hàng 👥", f"{total:,}")
    
    if 'Phân Loại' in df.columns:
        vips = len(df[df['Phân Loại'] == 'VIP'])
        junks = len(df[df['Phân Loại'] == 'JUNK'])
        m2.metric("Khách VIP (+50đ) 🌟", f"{vips:,}", delta=vips, delta_color="normal")
        m3.metric("Khách Rác (-50đ) 🗑️", f"{junks:,}", delta=-junks, delta_color="inverse")
    else:
        m2.metric("Khách VIP (+50đ) 🌟", "0")
        m3.metric("Khách Rác (-50đ) 🗑️", "0")

    st.divider()

    # Nút bấm trung tâm
    col_run, col_empty = st.columns([1, 2])
    with col_run:
        run_btn = st.button("🔥 CHẠY AI AGENT CHẤM ĐIỂM")

    if run_btn:
        if col_name not in df.columns:
            st.error(f"❌ Không tìm thấy cột '{col_name}'")
        else:
            with st.status("AI Agent đang quét mô tả khách hàng..."):
                results = [score_lead_logic(val) for val in df[col_name]]
                df['Điểm Số'], df['Phân Loại'], df['Lý Do'] = zip(*results)
                time.sleep(1) # Tạo hiệu ứng xử lý
                st.session_state.df = df
            st.rerun()

    # --- BƯỚC 3: BẢNG TỔNG KẾT KIỂM TRA (AUDIT) ---
    if 'Phân Loại' in df.columns:
        st.subheader("📑 Bảng Tổng kết Kiểm tra (Audit)")
        
        # Bộ lọc trạng thái
        filter_cat = st.multiselect("Bộ lọc nhanh:", options=["VIP", "WARM", "JUNK"], default=["VIP", "WARM", "JUNK"])
        
        # Áp dụng màu sắc & Hiển thị
        display_df = df[df['Phân Loại'].isin(filter_cat)]
        styled_df = display_df.style.apply(highlight_rows, axis=1)
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        st.info("💡 **Gợi ý**: Bạn có thể click vào tên cột để sắp xếp hoặc dùng ô search ở góc phải bảng.")

        # --- BƯỚC 4: HUMAN-IN-THE-LOOP & EXPORT ---
        st.divider()
        st.subheader("📥 Workflow: Người duyệt ➔ Excel")
        
        with st.expander("Mở trình chỉnh sửa cuối cùng & Xuất file"):
            final_df = st.data_editor(df, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False, sheet_name="Lead_Scoring")
            
            st.download_button(
                label="💾 TẢI FILE EXCEL BÀN GIAO",
                data=output.getvalue(),
                file_name="MindX_Lead_Scoring_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.warning("👈 Vui lòng nhấn 'Tải Dữ Liệu' ở Sidebar để bắt đầu.")
    # Hiển thị bảng hướng dẫn (Audit Table) như trong ảnh nếu chưa có dữ liệu
    st.image("https://i.imgur.com/your_guideline_image_placeholder.png", caption="Bảng Tổng kết Kiểm tra (Audit) - Yêu cầu hoàn thành bài tập")
