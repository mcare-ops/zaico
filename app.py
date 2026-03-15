import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import cloudinary
import cloudinary.uploader
from PIL import Image
import io

# 画面設定
st.set_page_config(page_title="カニ在庫管理 Pro", layout="wide")

st.title("🦀 カニ在庫管理ボード (完全版)")

# --- 1. 接続設定 ---
# Googleスプレッドシートへの接続
conn = st.connection("gsheets", type=GSheetsConnection)

# Cloudinaryの設定 (Streamlit CloudのSecretsから読み込み)
try:
    cloudinary.config( 
      cloud_name = st.secrets["cloudinary"]["cloud_name"], 
      api_key = st.secrets["cloudinary"]["api_key"], 
      api_secret = st.secrets["cloudinary"]["api_secret"],
      secure = True
    )
except:
    st.warning("Cloudinaryの連携設定（Secrets）が必要です。画像機能を使う場合は設定してください。")

# --- 2. データの読み込み ---
df = conn.read(ttl="0s")

# セッション状態にデータを保持
if 'stock' not in st.session_state:
    # スプレッドシートに「画像URL」列がない場合も想定して取得
    st.session_state.stock = {
        row['品目']: {
            'count': int(row['在庫数']), 
            'image_url': row.get('画像URL', '')
        } for _, row in df.iterrows()
    }

# --- 3. 保存・アップロード用関数 ---
def save_to_gsheet():
    """現在の在庫状態をスプレッドシートへ書き込む"""
    data_list = [
        {'品目': k, '在庫数': v['count'], '画像URL': v['image_url']} 
        for k, v in st.session_state.stock.items()
    ]
    new_df = pd.DataFrame(data_list)
    conn.update(data=new_df)

def upload_image(file, item_name):
    """Cloudinaryに画像をアップしてURLを取得する"""
    try:
        img = Image.open(file)
        img.thumbnail((400, 400)) # 負荷軽減のためサイズを抑える
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        response = cloudinary.uploader.upload(buf.getvalue(), public_id=f"zaico_{item_name}")
        return response['secure_url']
    except Exception as e:
        st.error(f"アップロード失敗: {e}")
        return None

# --- 4. メイン画面の構築 ---
cols = st.columns(2) # スマホで見やすい2列構成

for i, (item, info) in enumerate(st.session_state.stock.items()):
    with cols[i % 2]:
        with st.container(border=True):
            # 品目名と画像
            c1, c2 = st.columns([1, 2])
            with c1:
                if info['image_url']:
                    st.image(info['image_url'], use_container_width=True)
                else:
                    st.caption("No Image")
            with c2:
                st.subheader(item)
                # --- 在庫数の表示（:blackエラーを回避） ---
                if info['count'] <= 5:
                    st.markdown(f"## :red[{info['count']}]") # 5個以下は赤
                else:
                    st.markdown(f"## {info['count']}")      # 通常は黒

            # 操作エリア
            b1, b2, b3 = st.columns([1, 2, 1])
            with b1:
                if st.button("ー", key=f"minus_{item}"):
                    st.session_state.stock[item]['count'] = max(0, info['count'] - 1)
                    save_to_gsheet()
                    st.rerun()
            with b2:
                # 数字を直接入力
                new_val = st.number_input("数", value=info['count'], key=f"in_{item}", label_visibility="collapsed")
                if new_val != info['count']:
                    st.session_state.stock[item]['count'] = new_val
                    save_to_gsheet()
                    st.rerun()
            with b3:
                if st.button("＋", key=f"plus_{item}"):
                    st.session_state.stock[item]['count'] = info['count'] + 1
                    save_to_gsheet()
                    st.rerun()
            
            # 画像アップロード
            new_file = st.file_uploader("画像変更", type=["jpg", "png"], key=f"up_{item}", label_visibility="collapsed")
            if new_file:
                with st.spinner("送信中..."):
                    url = upload_image(new_file, item)
                    if url:
                        st.session_state.stock[item]['image_url'] = url
                        save_to_gsheet()
                        st.rerun()

# サイドバー（品目追加・削除）
with st.sidebar:
    st.header("管理メニュー")
    add_name = st.text_input("新しい品目名")
    if st.button("品目を追加"):
        if add_name and add_name not in st.session_state.stock:
            st.session_state.stock[add_name] = {'count': 0, 'image_url': ''}
            save_to_gsheet()
            st.rerun()
    
    st.divider()
    del_name = st.selectbox("削除する品目", options=[""] + list(st.session_state.stock.keys()))
    if st.button("選択した品目を削除") and del_name:
        del st.session_state.stock[del_name]
        save_to_gsheet()
        st.rerun()
