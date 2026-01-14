import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. 頁面配置 ---
st.set_page_config(page_title="台股 AI 戰情室 2.0", layout="wide")

# --- 2. 使用者數據庫 (模擬) ---
# 這裡可以為不同使用者定義專屬的初始名單
user_data = {
    "訪客": "2330, 2317",
    "使用者 A (核心)": "2330, 5498, 6182",
    "使用者 B (波段)": "2454, 2603, 2609",
    "使用者 C (存股)": "0050, 0056, 00878"
}

# --- 3. 頂部導覽列：切換使用者 ---
st.write("### 👤 戰情室使用者切換")
selected_user = st.radio(
    "請選擇您的身分進入專屬看板：",
    options=list(user_data.keys()),
    horizontal=True  # 橫向排列，更像按鈕
)

st.divider()

# --- 4. 側邊欄：根據使用者加載名單 ---
st.sidebar.header(f"⚙️ {selected_user} 的設定")
# 根據上方選擇的使用者，自動填入對應的代號
watchlist_input = st.sidebar.text_area(
    "編輯您的監控名單 (逗號隔開)", 
    value=user_data[selected_user],
    height=150
)
stocks = [s.strip() for s in watchlist_input.split(",") if s.strip()]

# --- 5. 數據抓取與顯示 (與前版本邏輯一致) ---
@st.cache_data(ttl=3600)
def get_war_room_data(sid):
    sid = sid.strip().upper()
    for suffix in [".TW", ".TWO"]:
        target_id = f"{sid}{suffix}"
        try:
            ticker = yf.Ticker(target_id)
            df = ticker.history(period="1y")
            if not df.empty:
                return df, target_id, sid 
        except:
            continue
    return pd.DataFrame(), None, None

# --- 6. 戰情看板介面 ---
st.title(f"🏢 {selected_user} 專屬監控看板")

if not stocks:
    st.info("請在左側輸入代號以開始監控。")
else:
    # 戰情總覽表
    summary = []
    with st.spinner('掃描數據中...'):
        for s in stocks:
            df, tid, name = get_war_room_data(s)
            if not df.empty:
                cp = df['Close'].iloc[-1]
                m5 = df['Close'].rolling(5).mean().iloc[-1]
                m37 = df['Close'].rolling(37).mean().iloc[-1]
                vol = df['Volume'].iloc[-1]
                
                # 燈號邏輯
                status = "🟢 多頭強勢" if cp > m5 > m37 else "🔴 趨勢偏空" if cp < m37 else "🟡 整理中"
                summary.append({"名稱": name, "股價": f"{cp:.2f}", "成交量": f"{vol:,.0f}", "狀態": status})

    st.table(pd.DataFrame(summary))
    
    st.divider()
    
    # 個股 K 線切換
    target = st.selectbox("🎯 快速診斷個股 K 線：", stocks)
    if target:
        df, tid, name = get_war_room_data(target)
        if not df.empty:
            df['5MA'] = df['Close'].rolling(5).mean()
            df['37MA'] = df['Close'].rolling(37).mean()
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線')])
            fig.add_trace(go.Scatter(x=df.index, y=df['5MA'], name='5MA', line=dict(color='#00BFFF')))
            fig.add_trace(go.Scatter(x=df.index, y=df['37MA'], name='37MA', line=dict(color='#BA55D3')))
            fig.update_layout(height=450, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
