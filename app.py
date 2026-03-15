import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# データの保存場所
DATA_FILE = "crab_stock_web.csv"
BACKUP_DIR = "backups"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, index_col=0).to_dict()['在庫数']
    # 初期データ
    return {"800g (Man)": 26, "1kg (新)": 9, "700g (先)": 3}

def save_data(data):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    # 辞書をDataFrameに変換
    df = pd.DataFrame(list(data.items()), columns=['品目', '在庫数']).set_index('品目')
    
    # 最新版をCSVで保存
    df.to_csv(DATA_FILE, encoding='utf-8-sig') # Excelで開けるように sig を付与
    
    # 履歴として保存（日付付きCSV）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    df.to_csv(f"{BACKUP_DIR}/stock_{timestamp}.csv", encoding='utf-8-sig')

# 初期化
if 'stock' not in st.session_state:
    st.session_state.stock = load_data()
if 'last_changed_time' not in st.session_state:
    st.session_state.last_changed_time = None
if 'needs_save' not in st.session_state:
    st.session_state.needs_save = False

st.set_page_config(page_title="カニ在庫管理 CSV版", layout="wide")
st.title("かに大将 在庫管理ボード (CSV)")

# 20秒経過判定
if st.session_state.needs_save and st.session_state.last_changed_time:
    if datetime.now() - st.session_state.last_changed_time > timedelta(seconds=20):
        save_data(st.session_state.stock)
        st.session_state.needs_save = False
        st.toast("CSVバックアップを保存しました！")

# メイン画面
cols = st.columns(2)
for i, (item, count) in enumerate(st.session_state.stock.items()):
    with cols[i % 2]:
        with st.container(border=True):
            st.subheader(item)
            if count <= 5: st.markdown(f"## :red[{count}]")
            else: st.markdown(f"## {count}")
            
            b1, b2, b3 = st.columns([1, 2, 1])
            with b1:
                if st.button("ー", key=f"m_{item}"):
                    st.session_state.stock[item] = max(0, count - 1)
                    st.session_state.last_changed_time, st.session_state.needs_save = datetime.now(), True
                    st.rerun()
            with b2:
                new_val = st.number_input("数", value=int(count), key=f"i_{item}", label_visibility="collapsed")
                if new_val != count:
                    st.session_state.stock[item] = new_val
                    st.session_state.last_changed_time, st.session_state.needs_save = datetime.now(), True
                    st.rerun()
            with b3:
                if st.button("＋", key=f"p_{item}"):
                    st.session_state.stock[item] = count + 1
                    st.session_state.last_changed_time, st.session_state.needs_save = datetime.now(), True
                    st.rerun()

# サイドバー
with st.sidebar:
    st.header("管理メニュー")
    if st.session_state.needs_save:
        wait = timedelta(seconds=20) - (datetime.now() - st.session_state.last_changed_time)
        st.warning(f"保存まであと {int(max(0, wait.total_seconds()))}秒")
        if st.button("今すぐ保存"):
            save_data(st.session_state.stock)
            st.session_state.needs_save = False
            st.rerun()
    
    st.divider()
    st.subheader("CSV履歴のダウンロード")
    if os.path.exists(BACKUP_DIR):
        files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.csv')], reverse=True)[:10]
        if files:
            selected = st.selectbox("過去のCSVデータ", files)
            with open(f"{BACKUP_DIR}/{selected}", "rb") as f:
                st.download_button("CSVをダウンロード", f, file_name=selected)
