import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. 頁面配置 ---
st.set_page_config(page_title="台股 AI 戰情室 2.6", layout="wide", page_icon="🏢")

# 手機與樣式補丁
st.markdown("""
    <style>
    .js-plotly-plot .plotly .main-svg { touch-action: pan-y pinch-zoom !important; }
    .stMetric { background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 使用者數據庫 & 離線中文名對照表 (確保 100% 顯示中文) ---
# 我幫你預設好了常用代號，之後你也可以自行在程式碼中增加
STOCK_NAMES = {
    "2344": "華邦電", "2408": "南亞科", "2409": "友達", "2454": "聯發科", 
    "3481": "群創", "5498": "凱崴", "8422": "可寧衛", "2330": "台積電",
    "2317": "鴻海", "2603": "長榮", "0050": "元大台灣50", "0056": "元大高股息", "2337": "旺宏"
}

user_profiles = {
    "丘小豬": "2344, 2408, 2409, 2454, 3481, 5498, 8422, 2337",
    "宗珉": "2454, 2317, 2603",
    "MaMa": "0050, 0056, 00878"
}

# --- 3. 數據抓取引擎 (專注於股價與趨勢) ---
@st.cache_data(ttl=3600)
def get_war_room_data(sid):
    sid = sid.strip().upper()
    # 優先從對照表抓中文名，抓不到才顯示代號
    display_name = STOCK_NAMES.get(sid, sid)
    
    for suffix in [".TW", ".TWO"]:
        target_id = f"{sid}{suffix}"
        try:
            ticker = yf.Ticker(target_id)
            df = ticker.history(period="1y")
            if not df.empty:
                return df, target_id, display_name
        except:
            continue
    return pd.DataFrame(), None, display_name

# --- 4. 使用者切換 ---
st.write("### 👤 戰情室使用者入口")
selected_user = st.radio("請選擇身分：", options=list(user_profiles.keys()), horizontal=True)
st.divider()

# --- 5. 側邊欄配置 ---
st.sidebar.header(f"⚙️ {selected_user} 配置")
input_list = st.sidebar.text_area("編輯監控代號", value=user_profiles[selected_user])
stocks = [s.strip() for s in input_list.split(",") if s.strip()]

# --- 6. 主戰情看板 ---
st.title(f"🏢 {selected_user} 實時監控看板")

if not stocks:
    st.info("👈 請在左側輸入股票代號")
else:
    summary = []
    with st.spinner('📢 AI 同步數據中...'):
        for s in stocks:
            df, tid, name = get_war_room_data(s)
            if not df.empty:
                cp = df['Close'].iloc[-1]
                m5 = df['Close'].rolling(5).mean().iloc[-1]
                m13 = df['Close'].rolling(13).mean().iloc[-1]
                m37 = df['Close'].rolling(37).mean().iloc[-1]
                
                # 燈號邏輯
                if cp > m5 > m13 > m37: status = "🟢 多頭排列"
                elif cp < m37: status = "🔴 趨勢偏空"
                elif m5 < m13: status = "🟡 短線轉弱"
                else: status = "⚪ 橫盤整理"
                
                summary.append({"名稱": name, "代號": s, "股價": f"{cp:.2f}", "狀態": status})
    
    if summary:
        st.table(pd.DataFrame(summary))
    st.divider()

    # B. 深度個股診斷區
    st.subheader("🔍 深度 AI 策略診斷")
    focus_target = st.selectbox("🎯 選擇股票查看 5/13/37MA 詳細建議：", stocks)

    if focus_target:
        df, tid, name = get_war_room_data(focus_target)
        if not df.empty:
            df['5MA'] = df['Close'].rolling(5).mean()
            df['13MA'] = df['Close'].rolling(13).mean()
            df['37MA'] = df['Close'].rolling(37).mean()
            
            curr_p = round(df['Close'].iloc[-1], 2)
            m5 = round(df['5MA'].iloc[-1], 2)
            m13 = round(df['13MA'].iloc[-1], 2)
            m37 = round(df['37MA'].iloc[-1], 2)

            # K 線圖 (手機優化視野)
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線')])
            fig.add_trace(go.Scatter(x=df.index, y=df['5MA'], name='5MA', line=dict(color='#00BFFF', width=1.5)))
            fig.add_trace(go.Scatter(x=df.index, y=df['13MA'], name='13MA', line=dict(color='#FF8C00', width=1.5)))
            fig.add_trace(go.Scatter(x=df.index, y=df['37MA'], name='37MA', line=dict(color='#BA55D3', width=2)))
            
            last_60 = [df.index[-60] if len(df)>60 else df.index[0], df.index[-1]]
            fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False,
                              margin=dict(l=5, r=5, t=10, b=10), dragmode='pan',
                              xaxis=dict(range=last_60), yaxis=dict(fixedrange=True))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            # --- 🤖 AI 詳細建議 (原版文字保留，絕不刪減) ---
            st.write(f"#### 🤖 {name} ({focus_target}) 實戰策略指引")
            c1, c2, c3 = st.columns(3)
            c1.metric("5MA (極短支撐)", f"{m5}")
            c2.metric("13MA (短線強弱)", f"{m13}")
            c3.metric("37MA (生命線)", f"{m37}")

            with st.expander("📝 點擊查看 AI 深度分析與明日策略", expanded=True):
                if curr_p > m5 > m13 > m37:
                    st.success("**【趨勢：多頭噴發期】**")
                    st.write(f"""
                    * **均線結構**：目前的排列為『完全多頭』，代表市場信心極強。
                    * **支撐觀察**：5MA ({m5}) 為強勢股防線，未破前不預設壓力。
                    * **操作策略**：持股續抱，若想加碼，請靜待回測 13MA ({m13}) 附近且不跌破的時機。
                    """)
                elif curr_p > m37:
                    st.warning("**【趨勢：高檔整理/短線修正】**")
                    st.write(f"""
                    * **均線結構**：股價雖在 37MA ({m37}) 之上，但已跌破 5MA。顯示買盤力道暫歇。
                    * **支撐觀察**：必須緊盯 13MA ({m13}) 的支撐性，若此線也跌破，將轉向測試 37MA。
                    * **操作策略**：暫不追高。若有獲利可先調節 1/2 部位，保留現金等 5MA 重新站穩。
                    """)
                else:
                    st.error("**【趨勢：空頭轉弱期】**")
                    st.write(f"""
                    * **均線結構**：股價位於 37MA ({m37}) 之下，代表中期持有者全數套牢。
                    * **阻力觀察**：上方的 13MA ({m13}) 目前轉為沉重壓力，反彈站不穩皆應視為逃命波。
                    * **操作策略**：**『保護本金』** 為首要目標，不建議攤平。靜待 5MA 與 13MA 重新黃金交叉後再進場。
                    """)

