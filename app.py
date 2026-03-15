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
            return {index: row['在庫数'] for index, row in df.iterrows()}
        except: pass
    return {"ズワイガニ (800g)": 0, "ズワイガニ (1kg)": 0, "イカ": 0}

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
st.set_page_config(page_title="かに大将 在庫管理", layout="wide", initial_sidebar_state="collapsed")

# セッション初期化
if 'stock' not in st.session_state: st.session_state.stock = load_data()
if 'needs_save' not in st.session_state: st.session_state.needs_save = False
if 'sort_mode' not in st.session_state: st.session_state.sort_mode = False

# --- UIデザイン ---
st.markdown("""
    <style>
    .stButton button { width: 100% !important; font-weight: bold !important; }
    .sort-mode-active button { border: 3px solid #FF4B4B !important; background-color: #FFF5F5 !important; height: 60px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("かに大将 在庫管理")

# --- 並べ替えモード切替 ---
mode_btn_text = "🔄 並べ替えを終了" if st.session_state.sort_mode else "↕️ 品目を並べ替える"
if st.button(mode_btn_text):
    st.session_state.sort_mode = not st.session_state.sort_mode
    st.rerun()

# --- メイン表示エリア ---
items_list = list(st.session_state.stock.items())

if st.session_state.sort_mode:
    # 並べ替えモード（▲▼ボタンで移動）
    st.info("「▲」「▼」で順番を入れ替えられます")
    for i, (item, count) in enumerate(items_list):
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1: st.write(f"### {item}")
            with c2:
                if i > 0 and st.button("▲", key=f"up_{item}"):
                    items_list[i], items_list[i-1] = items_list[i-1], items_list[i]
                    st.session_state.stock = dict(items_list)
                    st.session_state.needs_save = True
                    st.rerun()
            with c3:
                if i < len(items_list) - 1 and st.button("▼", key=f"down_{item}"):
                    items_list[i], items_list[i+1] = items_list[i+1], items_list[i]
                    st.session_state.stock = dict(items_list)
                    st.session_state.needs_save = True
                    st.rerun()
else:
    # 通常モード（在庫入力）
    @st.fragment(run_every="10s")
    def sync_ui():
        if not st.session_state.needs_save:
            new = load_data()
            if new != st.session_state.stock:
                st.session_state.stock = new
                st.rerun()
        if st.session_state.needs_save:
            save_data(st.session_state.stock, get_device_info())
            st.session_state.needs_save = False
            st.toast("保存完了")

        cols = st.columns(3)
        for i, (item, count) in enumerate(items_list):
            with cols[i % 3]:
                with st.container(border=True):
                    st.write(f"**{item}**")
                    color = "red" if count <= 5 else "black"
                    st.markdown(f"<h2 style='color:{color};'>{count}</h2>", unsafe_allow_html=True)
                    v = st.number_input("数", min_value=0, value=int(count), key=f"in_{item}", label_visibility="collapsed")
                    if v != count:
                        st.session_state.stock[item] = v
                        st.session_state.needs_save = True
                        st.rerun()
    sync_ui()

st.divider()

# --- 管理メニュー：追加・削除・保存・復元を統合して常に表示 ---
st.subheader("⚙️ 管理・データ操作")
col_a, col_b = st.columns(2)

with col_a:
    st.write("### ➕ 品目の管理")
    new_p = st.text_input("新しい品目名")
    if st.button("追加実行"):
        if new_p and new_p not in st.session_state.stock:
            st.session_state.stock[new_p] = 0
            st.session_state.needs_save = True
            st.rerun()
    
    del_p = st.selectbox("品目を削除", [""] + list(st.session_state.stock.keys()))
    if st.button("削除実行"):
        if del_p:
            del st.session_state.stock[del_p]
            st.session_state.needs_save = True
            st.rerun()

with col_b:
    st.write("### 💾 保存と復元")
    # 復元
    up_file = st.file_uploader("CSVから復元", type="csv")
    if up_file:
        try:
            df_up = pd.read_csv(up_file, header=1, index_col=0)
            if st.button("✅ データを復元する"):
                st.session_state.stock = {idx: row['在庫数'] for idx, row in df_up.iterrows()}
                st.session_state.needs_save = True
                st.rerun()
        except: st.error("形式エラー")

    # ダウンロード
    if os.path.exists(BACKUP_DIR):
        files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.csv')], reverse=True)[:5]
        if files:
            sel = st.selectbox("過去の履歴をDL", files)
            with open(f"{BACKUP_DIR}/{sel}", "rb") as f:
                st.download_button("📥 ダウンロード", f, file_name=sel)
