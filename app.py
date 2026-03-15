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
    with cols[i % 3]:
        with st.container(border=True):
            st.write(f"**{item}**")
            
            if count <= 5:
                st.markdown(f"## :red[{count}]")
            else:
                st.markdown(f"## {count}")
            
            # 【修正箇所】カッコを正しく閉じました
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
    st.header("管理メニュー")
    
    with st.expander("➕ 品目を追加・削除する"):
        new_name = st.text_input("新しい品目名")
        if st.button("品目追加"):
            if new_name and new_name not in st.session_state.stock:
                st.session_state.stock[new_name] = 0
                st.session_state.last_changed_time = datetime.now(JST)
                st.session_state.needs_save = True
                st.rerun()
        
        st.divider()
        
        del_target = st.selectbox("削除する品目", [""] + list(st.session_state.stock.keys()))
        if st.button("品目削除"):
            if del_target:
                del st.session_state.stock[del_target]
                st.session_state.last_changed_time = datetime.now(JST)
                st.session_state.needs_save = True
                st.rerun()

    st.divider()

    if st.session_state.needs_save:
        wait = timedelta(seconds=20) - (datetime.now(JST) - st.session_state.last_changed_time)
        sec = int(max(0, wait.total_seconds()))
        st.warning(f"⚠️ 未保存の変更あり\n(あと {sec}秒 で自動保存)")
        if st.button("今すぐCSV保存"):
            save_data(st.session_state.stock)
            st.session_state.needs_save = False
            st.rerun()
    else:
        st.success("✅ データは最新です")

    st.divider()

    st.subheader("📊 履歴(CSV)の保存")
    if os.path.exists(BACKUP_DIR):
        files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.csv')], reverse=True)[:5]
        if files:
            selected = st.selectbox("保存するファイルを選択", files)
            with open(f"{BACKUP_DIR}/{selected}", "rb") as f:
                st.download_button(
                    label="📥 CSVをダウンロード",
                    data=f,
                    file_name=selected,
                    mime="text/csv",
                    key="download_csv"
                )
