import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# データの保存場所
DATA_FILE = "crab_stock_web.csv"
BACKUP_DIR = "backups"

# --- データ管理関数 ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, index_col=0)
            return df.to_dict()['在庫数']
        except:
            pass
    return {"800g (Man)": 26, "1kg (新)": 9, "700g (先)": 3}

def save_data(data):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    df = pd.DataFrame(list(data.items()), columns=['品目', '在庫数']).set_index('品目')
    df.to_csv(DATA_FILE, encoding='utf-8-sig')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    df.to_csv(f"{BACKUP_DIR}/stock_{timestamp}.csv", encoding='utf-8-sig')

# --- ボタン操作用関数 ---
def update_stock(item, delta):
    st.session_state.stock[item] = max(0, st.session_state.stock[item] + delta)
    st.session_state.last_changed_time = datetime.now()
    st.session_state.needs_save = True

# --- 初期化 ---
if 'stock' not in st.session_state:
    st.session_state.stock = load_data()
if 'last_changed_time' not in st.session_state:
    st.session_state.last_changed_time = None
if 'needs_save' not in st.session_state:
    st.session_state.needs_save = False

st.set_page_config(page_title="かに大将 在庫管理", layout="wide")
st.title("かに大将 在庫管理ボード")

# 20秒経過判定（自動保存）
if st.session_state.needs_save and st.session_state.last_changed_time:
    if datetime.now() - st.session_state.last_changed_time > timedelta(seconds=20):
        save_data(st.session_state.stock)
        st.session_state.needs_save = False
        st.toast("バックアップを保存しました")

# --- メイン画面 ---
cols = st.columns(2)
items = list(st.session_state.stock.items())

for i, (item, count) in enumerate(items):
    with cols[i % 2]:
        with st.container(border=True):
            st.subheader(item)
            
            # 在庫数の表示
            if count <= 5:
                st.markdown(f"## :red[{count}]")
            else:
                st.markdown(f"## {count}")
            
            # 操作エリア
            b1, b2, b3 = st.columns([1, 2, 1])
            with b1:
                if st.button("ー", key=f"btn_m_{item}"):
                    update_stock(item, -1)
                    st.rerun()
            with b2:
                # 入力欄から直接変更
                new_val = st.number_input("数", value=int(count), key=f"input_{item}", label_visibility="collapsed")
                if new_val != count:
                    st.session_state.stock[item] = new_val
                    st.session_state.last_changed_time = datetime.now()
                    st.session_state.needs_save = True
                    st.rerun()
            with b3:
                if st.button("＋", key=f"btn_p_{item}"):
                    update_stock(item, 1)
                    st.rerun()

# --- サイドバー ---
with st.sidebar:
    st.header("管理メニュー")
    
    # 品目追加
    with st.expander("品目を追加する"):
        new_name = st.text_input("新しい品目名")
        if st.button("追加"):
            if new_name and new_name not in st.session_state.stock:
                st.session_state.stock[new_name] = 0
                st.session_state.last_changed_time = datetime.now()
                st.session_state.needs_save = True
                st.rerun()

    # 品目削除
    with st.expander("品目を削除する"):
        del_target = st.selectbox("削除する品目", [""] + list(st.session_state.stock.keys()))
        if st.button("削除実行"):
            if del_target:
                del st.session_state.stock[del_target]
                st.session_state.last_changed_time = datetime.now()
                st.session_state.needs_save = True
                st.rerun()

    st.divider()

    # 保存ステータス
    if st.session_state.needs_save:
        wait = timedelta(seconds=20) - (datetime.now() - st.session_state.last_changed_time)
        st.warning(f"保存まであと {int(max(0, wait.total_seconds()))}秒")
        if st.button("今すぐ保存"):
            save_data(st.session_state.stock)
            st.session_state.needs_save = False
            st.rerun()
    
    # 履歴
    st.subheader("CSV履歴")
    if os.path.exists(BACKUP_DIR):
        files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.csv')], reverse=True)[:5]
        for f_name in files:
            with open(f"{BACKUP_DIR}/{f_name}", "rb") as f:
                st.download_button(f"📥 {f_name}", f, file_name=f_name, key=f"dl_{f_name}")
