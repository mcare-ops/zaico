import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, timezone

# --- 基本設定 ---
DATA_FILE = "crab_stock_web.csv"
BACKUP_DIR = "backups"
JST = timezone(timedelta(hours=+9), 'JST')

def get_device_info():
    try:
        headers = st.context.headers
        user_agent = headers.get("User-Agent", "Unknown")
        ip = headers.get("X-Forwarded-For", "Unknown").split(",")[0]
        return f"{user_agent.split(' ')[0]} ({ip})"
    except: return "Unknown"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, header=1, index_col=0)
            return df.to_dict()['在庫数']
        except: pass
    return {"ズワイガニ800g": 0, "ズワイガニ1kg": 0, "イカ": 0}

def save_data(data, info):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    now_jst = datetime.now(JST) 
    timestamp_str = now_jst.strftime('%Y/%m/%d %H:%M:%S')
    file_timestamp = now_jst.strftime('%Y%m%d_%H%M%S')
    df = pd.DataFrame(list(data.items()), columns=['品目', '在庫数']).set_index('品目')
    for path in [DATA_FILE, f"{BACKUP_DIR}/stock_{file_timestamp}.csv"]:
        with open(path, 'w', encoding='utf-8-sig') as f:
            f.write(f"記録日時(JST)：,{timestamp_str}, 更新端末：,{info}\n")
            df.to_csv(f)

# アプリ設定
st.set_page_config(page_title="かに大将 在庫管理", layout="wide", initial_sidebar_state="expanded")

# --- 【超強力】CSS：あらゆる状態の開閉ボタンを強制的に改造 ---
st.markdown("""
    <style>
    /* 1. 全てのサイドバー開閉ボタン（開く・閉じる両方）を対象に */
    button[kind="headerNoPadding"] {
        background-color: #FF4B4B !important;
        color: white !important;
        width: 75px !important;
        height: 75px !important;
        border-radius: 50% !important;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.4) !important;
        transition: all 0.3s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: 2px solid white !important;
    }

    /* 2. ボタンを画面の目立つ位置に固定（閉じている時） */
    [data-testid="stSidebarCollapseButton"] {
        left: 20px !important;
        top: 20px !important;
        position: fixed !important;
        z-index: 9999999 !important;
    }

    /* 3. アイコン（>> や ×）の色とサイズを強制上書き */
    button[kind="headerNoPadding"] svg {
        fill: white !important;
        width: 45px !important;
        height: 45px !important;
        stroke: white !important;
    }

    /* 4. サイドバーが開いている時の「閉じる」ボタンを目立たせる */
    section[data-testid="stSidebar"] button[kind="headerNoPadding"] {
        position: absolute !important;
        right: -37px !important; /* サイドバーの少し外側へ */
        top: 20px !important;
        background-color: #333 !important; /* 開いている時は黒系 */
    }

    /* 余白の調整：ボタンがタイトルに被らないように */
    .main .block-container {
        padding-top: 100px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# セッション初期化
if 'stock' not in st.session_state:
    st.session_state.stock = load_data()
if 'needs_save' not in st.session_state:
    st.session_state.needs_save = False

st.title("🦀 かに大将 在庫管理ボード")

# --- リアルタイム反映 ---
@st.fragment(run_every="10s")
def sync_data():
    current_info = get_device_info()
    if not st.session_state.needs_save:
        new_data = load_data()
        if new_data != st.session_state.stock:
            st.session_state.stock = new_data
            st.rerun()

    if st.session_state.needs_save:
        save_data(st.session_state.stock, current_info)
        st.session_state.needs_save = False
        st.toast("在庫を保存しました")

    cols = st.columns(3)
    items = list(st.session_state.stock.items())
    for i, (item, count) in enumerate(items):
        with cols[i % 3]:
            with st.container(border=True):
                st.write(f"**{item}**")
                color = "red" if count <= 5 else "black"
                st.markdown(f"<h2 style='color:{color};'>{count}</h2>", unsafe_allow_html=True)
                new_val = st.number_input("数", min_value=0, value=int(count), key=f"in_{item}", label_visibility="collapsed")
                if new_val != count:
                    st.session_state.stock[item] = new_val
                    st.session_state.needs_save = True
                    st.rerun()

sync_data()

# --- サイドバー ---
with st.sidebar:
    st.header("⚙️ 管理メニュー")
    st.divider()
    
    with st.expander("➕ 品目の追加・削除"):
        name = st.text_input("新しい品目")
        if st.button("追加"):
            if name and name not in st.session_state.stock:
                st.session_state.stock[name] = 0
                st.session_state.needs_save = True
                st.rerun()
        st.divider()
        target = st.selectbox("削除する品目", [""] + list(st.session_state.stock.keys()))
        if st.button("削除"):
            if target:
                del st.session_state.stock[target]
                st.session_state.needs_save = True
                st.rerun()

    with st.expander("🔄 CSVから復元"):
        up = st.file_uploader("CSVを選択", type="csv")
        if up:
            try:
                df_p = pd.read_csv(up, header=1, index_col=0)
                st.dataframe(df_p)
                if st.button("復元を実行"):
                    st.session_state.stock = df_p.to_dict()['在庫数']
                    st.session_state.needs_save = True
                    st.rerun()
            except: st.error("形式不備")

    st.divider()
    st.subheader("📊 履歴の保存")
    if os.path.exists(BACKUP_DIR):
        files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.csv')], reverse=True)[:5]
        if files:
            selected = st.selectbox("過去データ", files)
            with open(f"{BACKUP_DIR}/{selected}", "rb") as f:
                st.download_button("📥 ダウンロード", f, file_name=selected)
