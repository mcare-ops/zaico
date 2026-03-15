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
if 'show_admin' not in st.session_state: st.session_state.show_admin = False
if 'stock' not in st.session_state: st.session_state.stock = load_data()
if 'needs_save' not in st.session_state: st.session_state.needs_save = False

# --- UI改善用CSS ---
st.markdown("""
    <style>
    /* 在庫カード内のボタンを押しやすく調整 */
    .stNumberInput { margin-bottom: 0px !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
    
    /* 並べ替えボタンのスタイル */
    .sort-btn-container button {
        height: 40px !important;
        padding: 0px !important;
        font-size: 18px !important;
        background-color: #f8f9fb !important;
        border: 1px solid #ddd !important;
    }
    
    /* 管理メニュー用ボタン */
    .admin-toggle button {
        width: 100% !important;
        height: 50px !important;
        background-color: #f0f2f6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🦀 かに大将 在庫管理ボード")

# --- メイン在庫表示 (並べ替えボタン内蔵型) ---
@st.fragment(run_every="10s")
def sync_and_display():
    current_info = get_device_info()
    
    # 外部保存された最新データを読み込み
    if not st.session_state.needs_save:
        new_data = load_data()
        if new_data != st.session_state.stock:
            st.session_state.stock = new_data
            st.rerun()

    # 変更があれば保存
    if st.session_state.needs_save:
        save_data(st.session_state.stock, current_info)
        st.session_state.needs_save = False
        st.toast("在庫・並び順を更新しました")

    items_list = list(st.session_state.stock.items())
    cols = st.columns(3)
    
    for i, (item, count) in enumerate(items_list):
        with cols[i % 3]:
            with st.container(border=True):
                # 上部：品目名と並べ替えボタン
                t_col1, t_col2, t_col3 = st.columns([6, 1.5, 1.5])
                with t_col1:
                    st.write(f"**{item}**")
                with t_col2:
                    if i > 0: # 上へボタン
                        if st.button("▲", key=f"up_{item}"):
                            items_list[i], items_list[i-1] = items_list[i-1], items_list[i]
                            st.session_state.stock = dict(items_list)
                            st.session_state.needs_save = True
                            st.rerun()
                with t_col3:
                    if i < len(items_list) - 1: # 下へボタン
                        if st.button("▼", key=f"down_{item}"):
                            items_list[i], items_list[i+1] = items_list[i+1], items_list[i]
                            st.session_state.stock = dict(items_list)
                            st.session_state.needs_save = True
                            st.rerun()
                
                # 中央：在庫数表示
                color = "red" if count <= 5 else "black"
                st.markdown(f"<h2 style='color:{color}; margin: 0px;'>{count}</h2>", unsafe_allow_html=True)
                
                # 下部：数値入力
                new_val = st.number_input("数", min_value=0, value=int(count), key=f"in_{item}", label_visibility="collapsed")
                if new_val != count:
                    st.session_state.stock[item] = new_val
                    st.session_state.needs_save = True
                    st.rerun()

sync_and_display()

st.divider()

# --- 管理メニュー（品目追加や削除など） ---
with st.container(border=False):
    col_admin_toggle = st.columns([1])[0]
    with col_admin_toggle:
        btn_text = "🔼 設定を閉じる" if st.session_state.show_admin else "⚙️ 新規追加・データ管理"
        if st.button(btn_text):
            st.session_state.show_admin = not st.session_state.show_admin
            st.rerun()

if st.session_state.show_admin:
    with st.container(border=True):
        st.subheader("🛠️ 品目管理")
        c_add, c_del = st.columns(2)
        with c_add:
            new_name = st.text_input("➕ 新しい品目名")
            if st.button("追加する"):
                if new_name and new_name not in st.session_state.stock:
                    st.session_state.stock[new_name] = 0
                    st.session_state.needs_save = True
                    st.rerun()
        with c_del:
            target = st.selectbox("🗑️ 削除する品目", [""] + list(st.session_state.stock.keys()))
            if st.button("削除を実行"):
                if target:
                    del st.session_state.stock[target]
                    st.session_state.needs_save = True
                    st.rerun()
        
        st.divider()
        st.subheader("🔄 バックアップ・復元")
        c_dl, c_up = st.columns(2)
        with c_dl:
            if os.path.exists(BACKUP_DIR):
                files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.csv')], reverse=True)[:5]
                if files:
                    selected = st.selectbox("履歴からDL", files)
                    with open(f"{BACKUP_DIR}/{selected}", "rb") as f:
                        st.download_button("📥 ダウンロード", f, file_name=selected)
        with c_up:
            up = st.file_uploader("CSVから復元", type="csv")
            if up:
                try:
                    df_p = pd.read_csv(up, header=1, index_col=0)
                    if st.button("✅ 復元を実行"):
                        st.session_state.stock = {idx: row['在庫数'] for idx, row in df_p.iterrows()}
                        st.session_state.needs_save = True
                        st.rerun()
                except: st.error("CSV形式エラー")
