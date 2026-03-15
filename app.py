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

# アプリ設定：サイドバーを最初から「開く」に固定
st.set_page_config(page_title="かに大将 在庫管理", layout="wide", initial_sidebar_state="expanded")

# サイドバー開閉ボタン(>)を劇的に見やすくするCSS
st.markdown("""
    <style>
    /* 左上のサイドバー開閉ボタン(>)を大きく、赤く、丸くする */
    [data-testid="stSidebarCollapseButton"] {
        background-color: #ff4b4b !important;
        color: white !important;
        width: 60px !important;
        height: 60px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3) !important;
    }
    [data-testid="stSidebarCollapseButton"] svg {
        width: 35px !important;
        height: 35px !important;
    }
    /* 在庫カードのスタイル調整 */
    [data-testid="stMetric"] {
        background-color: #f8f9fb;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# セッション初期化
if 'stock' not in st.session_state:
    st.session_state.stock = load_data()
if 'needs_save' not in st.session_state:
    st.session_state.needs_save = False

st.title("かに大将 在庫管理ボード")

# --- リアルタイム反映ロジック ---
@st.fragment(run_every="10s")
def sync_data():
    current_device = get_device_info()
    
    # 自分が編集中でなければ最新データを読み込む
    if not st.session_state.needs_save:
        new_data = load_data()
        if new_data != st.session_state.stock:
            st.session_state.stock = new_data
            st.rerun()

    # 変更があれば保存
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
    
    # 【修正箇所】閉じカッコと引用符を正しく修正
    st.subheader("📊 履歴(CSV)の保存")
    if os.path.exists(BACKUP_DIR):
        files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.csv')], reverse=True)[:5]
        if files:
            selected = st.selectbox("過去データを選択", files)
            with open(f"{BACKUP_DIR}/{selected}", "rb") as f:
                st.download_button("📥 ダウンロード", f, file_name=selected, key="dl_btn")
