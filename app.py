import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 頁面設定 ---
st.set_page_config(page_title="台股 AI 戰情室 2.0", layout="wide", page_icon="🏢")

# --- 數據抓取函數 (防封鎖穩定版) ---
@st.cache_data(ttl=3600)
def get_war_room_data(sid):
    sid = sid.strip().upper()
    for suffix in [".TW", ".TWO"]:
        target_id = f"{sid}{suffix}"
        try:
            ticker = yf.Ticker(target_id)
            df = ticker.history(period="1y")
            if not df.empty:
                # 這裡只抓代號，避免抓 info 導致 RateLimit 錯誤
                return df, target_id, sid 
        except:
            continue
    return pd.DataFrame(), None, None

# --- 側邊欄：分組設定 ---
st.sidebar.header("👤 監控分組切換")
group_name = st.sidebar.selectbox("切換清單", ["我的核心持股", "觀察清單", "自定義清單"])

# 預設名單
default_map = {
    "我的核心持股": "2330, 5498, 6182",
    "觀察清單": "2454, 2317, 2603",
    "自定義清單": ""
}

watchlist = st.sidebar.text_area("編輯本組代號 (逗號隔開)", value=default_map[group_name])
stocks = [s.strip() for s in watchlist.split(",") if s.strip()]

# --- 主畫面 ---
st.title(f"🏢 台股戰情室 - {group_name}")

if not stocks:
    st.info("👈 請在左側輸入股票代號，例如：2330, 5498")
else:
    # 1. 戰情匯總表格
    summary = []
    with st.spinner('掃描市場趨勢中...'):
        for s in stocks:
            df, tid, name = get_war_room_data(s)
            if not df.empty:
                cp = df['Close'].iloc[-1]
                m5 = df['Close'].rolling(5).mean().iloc[-1]
                m13 = df['Close'].rolling(13).mean().iloc[-1]
                m37 = df['Close'].rolling(37).mean().iloc[-1]
                vol = df['Volume'].iloc[-1]
                
                # AI 燈號邏輯 (5/13/37 MA 結構)
                if cp > m5 > m13 > m37:
                    status = "🟢 多頭強勢"
                elif cp < m37:
                    status = "🔴 中期破線"
                elif m5 < m13:
                    status = "🟡 短期轉弱"
                else:
                    status = "⚪ 區間整理"
                
                summary.append({
                    "股票名稱": name, 
                    "最後成交價": f"{cp:.2f}", 
                    "今日成交量(股)": f"{vol:,.0f}", 
                    "目前趨勢": status
                })

    st.subheader("📊 清單即時狀態掃描")
    # 顯示漂亮的表格，不顯示索引
    st.table(pd.DataFrame(summary))

    st.divider()

    # 2. 個股切換深度分析
    st.subheader("🔍 快速切換 K 線診斷")
    target = st.selectbox("選取要查看細節的股票", stocks)
    
    if target:
        df, tid, name = get_war_room_data(target)
        if not df.empty:
            df['5MA'] = df['Close'].rolling(5).mean()
            df['13MA'] = df['Close'].rolling(13).mean()
            df['37MA'] = df['Close'].rolling(37).mean()
            
            # 畫圖
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], 
                low=df['Low'], close=df['Close'], name='K線'
            )])
            fig.add_trace(go.Scatter(x=df.index, y=df['5MA'], name='5MA', line=dict(color='#00BFFF', width=1.5)))
            fig.add_trace(go.Scatter(x=df.index, y=df['13MA'], name='13MA', line=dict(color='#FF8C00', width=1.5)))
            fig.add_trace(go.Scatter(x=df.index, y=df['37MA'], name='37MA', line=dict(color='#BA55D3', width=2)))
            
            fig.update_layout(
                height=450, 
                template="plotly_dark", 
                xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 簡易文字提醒
            current_close = df['Close'].iloc[-1]
            ma37_val = df['37MA'].iloc[-1]
            if current_close > ma37_val:
                st.success(f"📈 {name} 股價在 37MA ({ma37_val:.2f}) 之上，中期趨勢安全。")
            else:
                st.error(f"📉 {name} 股價在 37MA ({ma37_val:.2f}) 之下，中期趨勢偏空。")
