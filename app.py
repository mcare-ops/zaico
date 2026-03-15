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

# 初期化
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
        st.toast("CSVバックアップを自動保存しました！")

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
            
            new_val = st.number_input(
                "在庫数", 
                min_value=0, 
                value=int(count), 
                key=f"input_{item}", 
                label_visibility="collapsed"
            )
            
            if new_val != count:
                st.session_state.stock[item] = new_val
                st.session_state.last_changed_time = datetime.now()
                st.session_state.needs_save = True
                st.rerun()

# --- サイドバー ---
with st.sidebar:
    st.header("管理メニュー")
    
    # 1. 保存ステータス（変更があったら一番上に表示）
    if st.session_state.needs_save:
        wait = timedelta(seconds=20) - (datetime.now() - st.session_state.last_changed_time)
        sec = int(max(0, wait.total_seconds()))
        st.warning(f"⚠️ 未保存の変更あり\n(あと {sec}秒 で自動保存)")
        if st.button("今すぐCSV保存"):
            save_data(st.session_state.stock)
            st.session_state.needs_save = False
            st.success("保存しました！")
            st.rerun()
    else:
        st.success("✅ データは最新です")

    st.divider()

    # 2. 履歴ダウンロード（常に表示）
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
        else:
            st.info("履歴ファイルはまだありません。")
    
    st.divider()

    # 3. 品目管理（折りたたみ）
    with st.expander("品目を追加・削除する"):
        new_name = st.text_input("新しい品目名")
        if st.button("品目追加"):
            if new_name and new_name not in st.session_state.stock:
                st.session_state.stock[new_name] = 0
                st.session_state.last_changed_time = datetime.now()
                st.session_state.needs_save = True
                st.rerun()
        
        st.divider()
        
        del_target = st.selectbox("削除する品目", [""] + list(st.session_state.stock.keys()))
        if st.button("品目削除"):
            if del_target:
                del st.session_state.stock[del_target]
                st.session_state.last_changed_time = datetime.now()
                st.session_state.needs_save = True
                st.rerun()
