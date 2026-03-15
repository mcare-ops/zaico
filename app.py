import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, timezone

# データの保存場所
DATA_FILE = "crab_stock_web.csv"
BACKUP_DIR = "backups"

# 日本時間(JST)の定義
JST = timezone(timedelta(hours=+9), 'JST')

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            # 1行目(記録日時)を飛ばして読み込む
            df = pd.read_csv(DATA_FILE, header=1, index_col=0)
            return df.to_dict()['在庫数']
        except:
            pass
    return {"800g (Man)": 26, "1kg (新)": 9, "700g (先)": 3}

def save_data(data):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # 日本時間を取得
    now_jst = datetime.now(JST) 
    timestamp_str = now_jst.strftime('%Y/%m/%d %H:%M:%S')
    file_timestamp = now_jst.strftime('%Y%m%d_%H%M%S')
    
    # データをDataFrameに変換
    df = pd.DataFrame(list(data.items()), columns=['品目', '在庫数']).set_index('品目')
    
    # 保存処理
    for path in [DATA_FILE, f"{BACKUP_DIR}/stock_{file_timestamp}.csv"]:
        with open(path, 'w', encoding='utf-8-sig') as f:
            f.write(f"記録日時(JST)：,{timestamp_str}\n")
            df.to_csv(f)

# 初期化
if 'stock' not in st.session_state:
    st.session_state.stock = load_data()
if 'last_changed_time' not in st.session_state:
    st.session_state.last_changed_time = None
if 'needs_save' not in st.session_state:
    st.session_state.needs_save = False

st.set_page_config(page_title="かに大将 在庫管理", layout="wide")
st.title("🦀 かに大将 在庫管理ボード")

# 20秒経過判定
if st.session_state.needs_save and st.session_state.last_changed_time:
    if datetime.now(JST) - st.session_state.last_changed_time > timedelta(seconds=20):
        save_data(st.session_state.stock)
        st.session_state.needs_save = False
        st.toast("CSVバックアップを日本時間で保存しました！")

# --- メイン画面 ---
cols = st.columns(3)
items = list(st.session_state.stock.items())

for i, (item, count) in enumerate(items):
    # 【修正箇所】cols[i % 3] の後ろにコロンを付けました
    with cols[i % 3]:
        with st.container(border=True):
            st.write(f"**{item}**")
            
            if count <= 5:
                st.markdown(f"## :red[{count}]")
            else:
                st.markdown(f"## {count}")
            
            new_val = st.number_input(
                "在庫数", 
                min_value=0, 
                value=int(count), 
                key=f"input_{item}", 
                label_visibility="collapsed"
            )
            
            if new_val != count:
                st.session_state.stock[item] = new_val
                st.session_state.last_changed_time = datetime.now(JST)
                st.session_state.needs_save = True
                st.rerun()

# --- サイドバー ---
with st.sidebar:
