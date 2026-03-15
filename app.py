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

# アプリ設定（サイドバーを最初から閉じ、画面を広く使う）
st.set_page_config(page_title="かに大将 在庫管理", layout="wide", initial_sidebar_state="collapsed")

# セッション初期化
if 'show_admin' not in st.session_state:
    st.session_state.show_admin = False
if 'stock' not in st.session_state:
    st.session_state.stock = load_data()
if 'needs_save' not in st.session_state:
    st.session_state.needs_save = False

# デザインCSS
st.markdown("""
    <style>
    div.stButton > button {
        width: 100% !important;
        height: 50px !important;
        font-weight: bold !important;
    }
    /* 管理メニューを囲む枠 */
    .admin-box {
        padding: 20px;
        border: 2px solid #f0f2f6;
        border-radius: 10px;
        background-color: #fafafa;
        margin-top: 20px;
    }
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
        st.toast("在庫を保存しました")

    # 在庫表示エリア
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

st.divider()

# --- 管理メニューの表示スイッチ ---
# ボタンを押すごとに show_admin を True/False 切り替える
btn_label = "🔼 管理メニューを閉じる" if st.session_state.show_admin else "⚙️ 管理メニューを開く"
if st.button(btn_label):
    st.session_state.show_admin = not st.session_state.show_admin
    st.rerun()

# --- 管理メニュー本体 (メイン画面に表示) ---
if st.session_state.show_admin:
    with st.container(border=True):
        st.subheader("⚙️ 管理設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### ➕ 品目の追加・削除")
            name = st.text_input("新しい品目名")
            if st.button("この品目を追加"):
                if name and name not in st.session_state.stock:
                    st.session_state.stock[name] = 0
                    st.session_state.needs_save = True
                    st.rerun()
            
            st.divider()
            target = st.selectbox("削除する品目を選択", [""] + list(st.session_state.stock.keys()))
            if st.button("この品目を削除"):
                if target:
                    del st.session_state.stock[target]
                    st.session_state.needs_save = True
                    st.rerun()

        with col2:
            st.write("### 🔄 CSVから復元")
            up = st.file_uploader("バックアップCSVを選択", type="csv")
            if up:
                try:
                    df_p = pd.read_csv(up, header=1, index_col=0)
                    st.dataframe(df_p)
                    if st.button("このデータで上書き復元"):
                        st.session_state.stock = df_p.to_dict()['在庫数']
                        st.session_state.needs_save = True
                        st.rerun()
                except: st.error("CSVの形式が正しくありません")

        st.divider()
        st.write("### 📊 過去の履歴をダウンロード")
        if os.path.exists(BACKUP_DIR):
            files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.csv')], reverse=True)[:5]
            if files:
                selected = st.selectbox("ダウンロードするファイルを選択", files)
                with open(f"{BACKUP_DIR}/{selected}", "rb") as f:
                    st.download_button("📥 CSVダウンロード", f, file_name=selected)
