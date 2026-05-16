# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import gspread
# pyrefly: ignore [missing-import]
from google.oauth2.service_account import Credentials
import io
import time
import json

# ==========================================
# 1. CẤU HÌNH TRANG & GIAO DIỆN (UI/UX)
# ==========================================
st.set_page_config(page_title="MindX AI Lead Scoring", page_icon="🎯", layout="wide")

# Custom CSS cho giao diện chuyên nghiệp
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: white; padding: 20px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #ed1c24;
    }
    .vip-row { background-color: #ffebee !important; }
    .stButton>button {
        width: 100%; border-radius: 5px; height: 3em;
        background-color: #ed1c24; color: white; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# SIDEBAR: Logo & Thông tin
with st.sidebar:
    st.image("https://mindx.edu.vn/images/logo.png", width=200)
    st.divider()
    st.header("⚙️ Cấu Hình Hệ Thống")
    
    sheet_name = st.text_input("Tên/ID Spreadsheet", value="Lead Scoring Data")
    col_name = st.text_input("Tên cột Nhu cầu", value="nhu_cau_mo_ta")
    
    st.info("💡 Sheet đã được share quyền cho: `lead-scoring-robot-phuongnm@neat-element-496514-c8.iam.gserviceaccount.com`")
    
    # Khu vực dán JSON thủ công nếu file bị lỗi
    with st.expander("🛠️ Cấu hình nâng cao (Dán JSON)"):
        manual_json = st.text_area("Nếu báo lỗi JWT, hãy dán nội dung file credentials.json vào đây:", height=200)

    load_btn = st.button("📥 TẢI DỮ LIỆU")

# ==========================================
# 2. XỬ LÝ DỮ LIỆU & GOOGLE SHEETS API
# ==========================================
def clean_private_key(pk):
    """Làm sạch Private Key từ mọi nguồn (file, secrets, manual)"""
    if not pk: return pk
    pk = pk.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")
    pk = pk.replace("\\n", "").replace("\n", "").replace("\r", "").replace(" ", "")
    return "-----BEGIN PRIVATE KEY-----\n" + pk + "\n-----END PRIVATE KEY-----\n"

def get_creds():
    """Lấy credentials từ Secrets, File hoặc Manual Paste"""
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # 1. Thử lấy từ Manual Paste (Ưu tiên cao nhất để debug)
    if manual_json:
        try:
            info = json.loads(manual_json)
            info["private_key"] = clean_private_key(info.get("private_key", ""))
            return Credentials.from_service_account_info(info, scopes=scopes)
        except:
            st.warning("⚠️ Nội dung JSON dán thủ công không hợp lệ.")

    # 2. Thử lấy từ st.secrets (Chuẩn Streamlit)
    if "gcp_service_account" in st.secrets:
        try:
            info = dict(st.secrets["gcp_service_account"])
            info["private_key"] = clean_private_key(info.get("private_key", ""))
            return Credentials.from_service_account_info(info, scopes=scopes)
        except:
            pass

    # 3. Thử lấy từ file credentials.json
    try:
        with open("credentials.json", "r") as f:
            info = json.load(f)
        info["private_key"] = clean_private_key(info.get("private_key", ""))
        return Credentials.from_service_account_info(info, scopes=scopes)
    except:
        return None

def connect_to_gsheet(sheet_id_or_name):
    try:
        creds = get_creds()
        if not creds:
            st.error("❌ Không tìm thấy thông tin xác thực (JSON).")
            return None
            
        client = gspread.authorize(creds)
        
        if "docs.google.com/spreadsheets/d/" in sheet_id_or_name:
            sheet_id_or_name = sheet_id_or_name.split("/d/")[1].split("/")[0]

        try:
            sh = client.open_by_key(sheet_id_or_name)
        except:
            sh = client.open(sheet_id_or_name)
            
        worksheet = sh.get_worksheet(0)
        return pd.DataFrame(worksheet.get_all_records())
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets: {e}")
        return None

def score_lead_logic(nhu_cau):
    if not nhu_cau or pd.isna(nhu_cau): return 0, "WARM", "Trống"
    text = str(nhu_cau).lower()
    score = 0
    reasons = []
    
    # VIP Keywords
    vip_keywords = ["20 tỷ", "tài chính mạnh", "biệt thự", "penthouse", "shophouse", "quận 1", "ven sông", "vinhomes", "phú mỹ hưng", "mua sỉ", "sổ hồng riêng"]
    found_vip = [kw for kw in vip_keywords if kw in text]
    if found_vip:
        score += 50
        reasons.append(f"🏠 VIP: {', '.join(found_vip)}")

    # Junk Keywords
    junk_keywords = ["nhầm số", "không nhu cầu", "dữ liệu cũ", "hỏi giá cho vui", "bảo hiểm", "vay vốn", "thuê bao", "không bắt máy"]
    found_junk = [kw for kw in junk_keywords if kw in text]
    if found_junk:
        score -= 50
        reasons.append(f"🗑️ JUNK: {', '.join(found_junk)}")
        
    if score == 0:
        score = 10
        reasons.append("⚖️ Tiềm năng")

    category = "WARM"
    if score >= 50: category = "VIP"
    elif score < 0: category = "JUNK"
    return score, category, " | ".join(reasons)

def highlight_rows(row):
    if row['Phân Loại'] == 'VIP': return ['background-color: #ffcccc'] * len(row)
    elif row['Phân Loại'] == 'JUNK': return ['background-color: #f0f0f0'] * len(row)
    return [''] * len(row)

# ==========================================
# 3. LUỒNG THỰC THI CHÍNH
# ==========================================
st.title("🚀 AI LEAD SCORING & AUDIT DASHBOARD")
st.divider()

if "df" not in st.session_state: st.session_state.df = None

if load_btn:
    with st.spinner("Đang kết nối Secure Google Sheets..."):
        df = connect_to_gsheet(sheet_name)
        if df is not None:
            st.session_state.df = df
            st.success("✅ Đã kết nối dữ liệu thành công!")

if st.session_state.df is not None:
    df = st.session_state.df
    st.subheader("📋 Dashboard Metrics")
    m1, m2, m3 = st.columns(3)
    total = len(df)
    m1.metric("Tổng khách hàng 👥", f"{total:,}")
    
    if 'Phân Loại' in df.columns:
        vips = len(df[df['Phân Loại'] == 'VIP'])
        junks = len(df[df['Phân Loại'] == 'JUNK'])
        m2.metric("Khách VIP (+50đ) 🌟", f"{vips:,}")
        m3.metric("Khách Rác (-50đ) 🗑️", f"{junks:,}")
    
    if st.button("🔥 CHẠY AI AGENT CHẤM ĐIỂM"):
        if col_name not in df.columns:
            st.error(f"❌ Không tìm thấy cột '{col_name}'")
        else:
            results = [score_lead_logic(val) for val in df[col_name]]
            df['Điểm Số'], df['Phân Loại'], df['Lý Do'] = zip(*results)
            st.session_state.df = df
            st.rerun()

    if 'Phân Loại' in df.columns:
        st.subheader("📑 Bảng Tổng kết Kiểm tra (Audit)")
        filter_cat = st.multiselect("Bộ lọc nhanh:", options=["VIP", "WARM", "JUNK"], default=["VIP", "WARM", "JUNK"])
        display_df = df[df['Phân Loại'].isin(filter_cat)]
        st.dataframe(display_df.style.apply(highlight_rows, axis=1), use_container_width=True)

        st.divider()
        with st.expander("📥 Xuất file Excel bàn giao"):
            final_df = st.data_editor(df, use_container_width=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False)
            st.download_button("💾 TẢI FILE EXCEL", data=output.getvalue(), file_name="MindX_Report.xlsx")
else:
    st.warning("👈 Vui lòng nhấn 'Tải Dữ Liệu' ở Sidebar để bắt đầu.")
