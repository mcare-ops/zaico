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
            # 順番を維持して読み込む
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
if 'show_admin' not in st.session_state: st.session_state.show_admin = False
if 'stock' not in st.session_state: st.session_state.stock = load_data()
if 'needs_save' not in st.session_state: st.session_state.needs_save = False

# CSS
st.markdown("""
    <style>
    div.stButton > button { width: 100% !important; font-weight: bold !important; }
    .sort-btn { font-size: 12px !important; height: 30px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("かに大将 在庫管理ボード")

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
        st.toast("在庫・並び順を保存しました")

    items = list(st.session_state.stock.items())
    cols = st.columns(3)
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
st.divider()

# --- 管理メニューの開閉スイッチ ---
btn_label = "🔼 並び替え・管理メニューを閉じる" if st.session_state.show_admin else "⚙️ 並び替え・品目管理を開く"
if st.button(btn_label):
    st.session_state.show_admin = not st.session_state.show_admin
    st.rerun()

# --- 管理メニュー本体 ---
if st.session_state.show_admin:
    with st.container(border=True):
        st.subheader("↕️ 品目の並び替え")
        items_list = list(st.session_state.stock.items())
        
        for i, (name, val) in enumerate(items_list):
            c1, c2, c3, c4 = st.columns([4, 1, 1, 2])
            with c1: st.write(f"**{name}**")
            with c2:
                if i > 0: # 一番上でなければ「上へ」ボタン
                    if st.button("▲", key=f"up_{name}"):
                        items_list[i], items_list[i-1] = items_list[i-1], items_list[i]
                        st.session_state.stock = dict(items_list)
                        st.session_state.needs_save = True
                        st.rerun()
            with c3:
                if i < len(items_list) - 1: # 一番下でなければ「下へ」ボタン
                    if st.button("▼", key=f"down_{name}"):
                        items_list[i], items_list[i+1] = items_list[i+1], items_list[i]
                        st.session_state.stock = dict(items_list)
                        st.session_state.needs_save = True
                        st.rerun()
            with c4:
                if st.button("🗑️ 削除", key=f"del_{name}"):
                    del st.session_state.stock[name]
                    st.session_state.needs_save = True
                    st.rerun()

        st.divider()
        st.subheader("➕ 新しい品目を追加")
        new_name = st.text_input("品目名を入力")
        if st.button("✨ 追加実行"):
            if new_name and new_name not in st.session_state.stock:
                st.session_state.stock[new_name] = 0
                st.session_state.needs_save = True
                st.rerun()

        st.divider()
        st.subheader("📊 履歴の保存・復元")
        col_dl, col_up = st.columns(2)
        with col_dl:
            if os.path.exists(BACKUP_DIR):
                files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.csv')], reverse=True)[:5]
                if files:
                    selected = st.selectbox("履歴ファイル", files)
                    with open(f"{BACKUP_DIR}/{selected}", "rb") as f:
                        st.download_button("📥 ダウンロード", f, file_name=selected)
        with col_up:
            up = st.file_uploader("CSVから復元", type="csv")
            if up:
                try:
                    df_p = pd.read_csv(up, header=1, index_col=0)
                    if st.button("✅ このデータで復元"):
                        st.session_state.stock = {idx: row['在庫数'] for idx, row in df_p.iterrows()}
                        st.session_state.needs_save = True
                        st.rerun()
                except: st.error("形式不備")
