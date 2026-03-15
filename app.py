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
    /* 並べ替えモード時のボタンを大きく押しやすく */
    .sort-active button {
        height: 60px !important;
        border: 2px solid #FF4B4B !important;
        background-color: #FFF5F5 !important;
    }
    .stNumberInput { margin-bottom: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🦀 かに大将 在庫管理")

# --- モード切り替えスイッチ (画面上部) ---
col_m1, col_m2 = st.columns([2, 1])
with col_m1:
    mode_text = "🔄 並べ替えを終了" if st.session_state.sort_mode else "↕️ 品目を並べ替える"
    if st.button(mode_text, use_container_width=True):
        st.session_state.sort_mode = not st.session_state.sort_mode
        st.rerun()

# --- メインコンテンツ ---
items_list = list(st.session_state.stock.items())

if st.session_state.sort_mode:
    # 【並べ替えモード】スマホでタップして上下に動かす
    st.info("「▲」や「▼」をタップして順番を入れ替えてください")
    for i, (item, count) in enumerate(items_list):
        with st.container(border=True):
            c1, c2, c3 = st.columns([5, 1, 1])
            with c1: st.write(f"### {item}")
            with c2:
                if i > 0:
                    if st.button("▲", key=f"srt_up_{item}", use_container_width=True):
                        items_list[i], items_list[i-1] = items_list[i-1], items_list[i]
                        st.session_state.stock = dict(items_list)
                        st.session_state.needs_save = True
                        st.rerun()
            with c3:
                if i < len(items_list) - 1:
                    if st.button("▼", key=f"srt_down_{item}", use_container_width=True):
                        items_list[i], items_list[i+1] = items_list[i+1], items_list[i]
                        st.session_state.stock = dict(items_list)
                        st.session_state.needs_save = True
                        st.rerun()
else:
    # 【通常モード】在庫入力
    @st.fragment(run_every="10s")
    def display_stock():
        # 自動同期
        if not st.session_state.needs_save:
            new_data = load_data()
            if new_data != st.session_state.stock:
                st.session_state.stock = new_data
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
                    new_val = st.number_input("数", min_value=0, value=int(count), key=f"in_{item}", label_visibility="collapsed")
                    if new_val != count:
                        st.session_state.stock[item] = new_val
                        st.session_state.needs_save = True
                        st.rerun()
    display_stock()

# --- 管理メニュー（下部に隠す） ---
with st.expander("⚙️ その他（追加・削除・復元）"):
    c_add, c_del = st.columns(2)
    with c_add:
        n = st.text_input("新しい品目")
        if st.button("追加"):
            if n and n not in st.session_state.stock:
                st.session_state.stock[n] = 0
                st.session_state.needs_save = True
                st.rerun()
    with c_del:
        t = st.selectbox("削除", [""] + list(st.session_state.stock.keys()))
        if st.button("削除実行"):
            if t:
                del st.session_state.stock[t]
                st.session_state.needs_save = True
                st.rerun()
