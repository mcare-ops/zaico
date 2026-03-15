import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# データの保存場所
DATA_FILE = "crab_stock_web.csv"
BACKUP_DIR = "backups"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_csv(DATA_FILE, index_col=0).to_dict()['在庫数']
        except:
            return {"イカ": 4, "ズワイガニ800g": 0}
    return {"イカ": 4, "ズワイガニ800g": 0}

def save_data(data):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    df = pd.DataFrame(list(data.items()), columns=['品目', '在庫数']).set_index('品目')
    df.to_csv(DATA_FILE, encoding='utf-8-sig')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    df.to_csv(f"{BACKUP_DIR}/stock_{timestamp}.csv", encoding='utf-8-sig')

# 初期化
if 'stock' not in st.session_state:
    st.session_state.stock = load_data()
if 'last_changed_time' not in st.session_state:
    st.session_state.last_changed_time = None
if 'needs_save' not in st.session_state:
    st.session_state.needs_save = False

st.set_page_config(page_title="かに大将 在庫管理", layout="wide")
st.title("🦀 かに大将 在庫管理ボード (CSV)")

# --- 自動保存ロジック（20秒経過） ---
if st.session_state.needs_save and st.session_state.last_changed_time:
    if datetime.now() - st.session_state.last_changed_time > timedelta(seconds=20):
        save_data(st.session_state.stock)
        st.session_state.needs_save = False
        st.toast("CSVバックアップを自動保存しました")

# --- メイン画面 ---
cols = st.columns(2)
items = list(st.session_state.stock.items())

for i, (item, count) in enumerate(items):
    with cols[i % 2]:
        with st.container(border=True):
            st.subheader(item)
            
            # 色分け表示
            if count <= 5: st.markdown(f"## :red[{count}]")
            else: st.markdown(f"## {count}")
            
            # --- ここが修正ポイント：操作ボタン ---
            b1, b2, b3 = st.columns([1, 2, 1])
            with b1:
                # 減らすボタン
                if st.button("ー", key=f"btn_m_{item}"):
                    st.session_state.stock[item] = max(0, count - 1)
                    st.session_state.last_changed_time = datetime.now()
                    st.session_state.needs_save = True
                    st.rerun() # 即座に画面を書き換える
            with b2:
                # 直接入力
                new_val = st.number_input("数", value=int(count), key=f"input_{item}", label_visibility="collapsed")
                if new_val != count:
                    st.session_state.stock[item] = new_val
                    st.session_state.last_changed_time = datetime.now()
                    st.session_state.needs_save = True
                    st.rerun()
            with b3:
                # 増やすボタン
                if st.button("＋", key=f"btn_p_{item}"):
                    st.session_state.stock[item] = count + 1
                    st.session_state.last_changed_time = datetime.now()
                    st.session_state.needs_save = True
                    st.rerun() # 即座に画面を書き換える

# --- サイドバー ---
with st.sidebar:
    st.header("管理メニュー")
    
    # 品目追加
    st.subheader("品目の追加")
    new_name = st.text_input("新しい品目名を入力")
    if st.button("追加する"):
        if new_name and new_name not in st.session_state.stock:
            st.session_state.stock[new_name] = 0
            st.session_state.last_changed_time, st.session_state.needs_save = datetime.now(), True
            st.rerun()

    st.divider()

    # 品目削除
    st.subheader("品目の削除")
    del_target = st.selectbox("削除する品目を選択", [""] + list(st.session_state.stock.keys()))
    if st.button("選択した品目を削除"):
        if del_target:
            del st.session_state.stock[del_target]
            st.session_state.last_changed_time, st.session_state.needs_save = datetime.now(), True
            st.rerun()

    st.divider()

    # 保存状態
    if st.session_state.needs_save:
        wait = timedelta(seconds=20) - (datetime.now() - st.session_state.last_changed_time)
        st.warning(f"保存まであと {int(max(0, wait.total_seconds()))}秒")
        if st.button("今すぐ保存"):
            save_data(st.session_state.stock)
            st.session_state.needs_save = False
            st.success("手動保存しました")
            st.rerun()
    
    # 履歴
    st.subheader("CSV履歴のダウンロード")
    if os.path.exists(BACKUP_DIR):
        files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.csv')], reverse=True)[:10]
        if files:
            selected = st.selectbox("過去のCSVデータ", files)
            with open(f"{BACKUP_DIR}/{selected}", "rb") as f:
                st.download_button("CSVをダウンロード", f, file_name=selected)
