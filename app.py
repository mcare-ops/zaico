import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# データの保存ファイル
DATA_FILE = "crab_stock_web.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # 初期データ
    return {"800g (Man)": 26, "1kg (新)": 9, "700g (先)": 7}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# セッション状態の初期化
if 'stock' not in st.session_state:
    st.session_state.stock = load_data()

st.set_page_config(page_title="カニ在庫管理", layout="wide")

st.title("🦀 カニ在庫管理ボード")

# --- メイン画面 ---
cols = st.columns(2) # スマホで見やすい2列構成

for i, (item, count) in enumerate(st.session_state.stock.items()):
    with cols[i % 2]:
        with st.container(border=True):
            st.subheader(item)
            
            # 在庫数の表示（5個以下なら赤色、それ以外は黒）
            if count <= 5:
                st.markdown(f"## :red[{count}]")
            else:
                st.markdown(f"## {count}")
            
            # 操作ボタンと入力
            b_col1, b_col2, b_col3 = st.columns([1, 2, 1])
            with b_col1:
                if st.button("ー", key=f"minus_{item}"):
                    st.session_state.stock[item] = max(0, count - 1)
                    save_data(st.session_state.stock)
                    st.rerun()
            with b_col2:
                # 直接数値入力
                new_val = st.number_input("数", value=int(count), key=f"input_{item}", label_visibility="collapsed")
                if new_val != count:
                    st.session_state.stock[item] = new_val
                    save_data(st.session_state.stock)
                    st.rerun()
            with b_col3:
                if st.button("＋", key=f"plus_{item}"):
                    st.session_state.stock[item] = count + 1
                    save_data(st.session_state.stock)
                    st.rerun()

            if st.button("削除", key=f"del_{item}", type="secondary"):
                del st.session_state.stock[item]
                save_data(st.session_state.stock)
                st.rerun()

# --- 管理機能（サイドバー） ---
with st.sidebar:
    st.header("管理設定")
    new_item = st.text_input("新しい品目名")
    if st.button("品目追加"):
        if new_item and new_item not in st.session_state.stock:
            st.session_state.stock[new_item] = 0
            save_data(st.session_state.stock)
            st.rerun()
    
    st.divider()
    # CSV出力機能
    df_csv = pd.DataFrame(list(st.session_state.stock.items()), columns=['品目', '在庫数'])
    csv = df_csv.to_csv(index=False).encode('shift-jis')
    st.download_button("在庫一覧をCSV出力", csv, f"stock_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
