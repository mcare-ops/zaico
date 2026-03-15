import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, timezone

# データの保存場所
DATA_FILE = "crab_stock_web.csv"
BACKUP_DIR = "backups"
JST = timezone(timedelta(hours=+9), 'JST')

def get_device_info():
    try:
        headers = st.context.headers
        user_agent = headers.get("User-Agent", "Unknown")
        ip = headers.get("X-Forwarded-For", "Unknown").split(",")[0]
        device = "iPhone" if "iPhone" in user_agent else "Android" if "Android" in user_agent else "PC"
        return f"{device} ({ip})"
    except:
        return "Unknown Device"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, header=1, index_col=0)
            return df.to_dict()['在庫数']
        except:
            pass
    return {"800g (Man)": 0, "1kg (新)": 0}

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

# --- 管理メニューボタン(左上の > )を圧倒的に見やすくするCSS ---
st.markdown("""
    <style>
    /* 1. 開閉ボタン本体の改造 */
    [data-testid="stSidebarCollapseButton"] {
        background-color: #ff4b4b !important; /* 鮮やかな赤 */
        color: white !important;
        width: 70px !important;
        height: 70px !important;
        border-radius: 15px !important; /* 少し角丸の四角 */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0px 4px 15px rgba(255, 75, 75, 0.5) !important;
        border: 2px solid white !important;
        transition: all 0.3s ease !important;
        left: 15px !important;
        top: 15px !important;
        position: fixed !important;
        z-index: 1000002 !important;
    }

    /* 2. ボタンの中のアイコン(> )を大きく */
    [data-testid="stSidebarCollapseButton"] svg {
        width: 40px !important;
        height: 40px !important;
        fill: white !important;
    }

    /* 3. ボタンにホバー（またはタッチ）した時の反応 */
    [data-testid="stSidebarCollapseButton"]:hover {
        transform: scale(1.1) !important;
        background-color: #ff0000 !important;
    }

    /* 4. サイドバーが開いている時の「閉じるボタン」も同様に装飾 */
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {
        background-color: #333 !important; /* 開いている時は落ち着いた色に */
        width: 50px !important;
        height: 50px !important;
        left: auto !important;
        right: 10px !important;
        top: 10px !important;
    }
    
    /* タイトルの位置をボタンと被らないように調整 */
    .main .block-container {
        padding-top: 80px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# セッション初期化
if 'stock' not in st.session_state:
    st.session_state.stock = load_data()
if 'needs_save' not in st.session_state:
    st.session_state.needs_save = False

st.title("🦀 かに大将 在庫管理ボード")

# --- リアルタイム反映ロジック ---
@st.fragment(run_every="10s")
def sync_data():
    current_device = get_device_info()
    
    if not st.session_state.needs_save:
        new_data = load_data()
        if new_data != st.session_state.stock:
            st.session_state.stock = new_data
            st.rerun()

    if st.session_state.needs_save:
        save_data(st.session_state.stock, current_device)
        st.session_state.needs_save = False
        st.toast(f"保存完了 ({current_device})")

    cols = st.columns(3)
    items = list(st.session_state.stock.items())

    for i, (item, count) in enumerate(items):
        with cols[i % 3]:
            with st.container(border=True):
                st.write(f"**{item}**")
                if count <= 5: st.markdown(f"## :red[{count}]")
                else: st.markdown(f"## {count}")
                
                new_val = st.number_input("数", min_value=0, value=int(count), key=f"input_{item}", label_visibility="collapsed")
                if new_val != count:
                    st.session_state.stock[item] = new_val
                    st.session_state.needs_save = True
                    st.rerun()

sync_data()

# --- サイドバー ---
with st.sidebar:
    st.header("⚙️ 管理メニュー")
    st.write(f"📱 識別: `{get_device_info()}`")
    st.divider()

    with st.expander("➕ 品目の追加・削除", expanded=True):
        new_name = st.text_input("新しい品目名")
        if st.button("✨ 品目を追加"):
            if new_name and new_name not in st.session_state.stock:
                st.session_state.stock[new_name] = 0
                st.session_state.needs_save = True
                st.rerun()
        
        st.divider()
        del_target = st.selectbox("削除する品目", [""] + list(st.session_state.stock.keys()))
        if st.button("🗑️ 選択した品目を削除"):
            if del_target:
                del st.session_state.stock[del_target]
                st.session_state.needs_save = True
                st.rerun()

    with st.expander("🔄 CSVから復元"):
        uploaded_file = st.file_uploader("CSVを選択", type="csv")
        if uploaded_file:
            try:
                df_p = pd.read_csv(uploaded_file, header=1, index_col=0)
                st.dataframe(df_p)
                if st.button("✅ データを復元実行"):
                    st.session_state.stock = df_p.to_dict()['在庫数']
                    st.session_state.needs_save = True
                    st.rerun()
            except: 
                st.error("CSV形式が正しくありません")

    st.divider()
    st.subheader("📊 履歴(CSV)の保存")
    if os.path.exists(BACKUP_DIR):
        files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.csv')], reverse=True)[:5]
        if files:
            selected = st.selectbox("過去データを選択", files)
            with open(f"{BACKUP_DIR}/{selected}", "rb") as f:
                st.download_button("📥 ダウンロード", f, file_name=selected, key="dl_btn")
