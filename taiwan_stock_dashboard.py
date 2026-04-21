#!/usr/bin/env python3
"""台股推薦儀表板 - 每天推薦 20 檔分數最高的個股"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ============== 設定 ==============
COLORS = {
    'background': '#0D1171',
    'card': '#161B22',
    'up': '#F85149',
    'down': '#3FB950',
    'bullish': '#F85149',
    'bearish': '#3FB950',
    'neutral': '#D29922',
    'text': '#E6EDF3',
    'text_secondary': '#8B949E',
    'border': '#30363D',
}

st.set_page_config(
    page_title="台股推薦儀表板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=dict()
)

st.markdown("""
<style>
.stApp, .main, body { background-color: #0D1171 !important; }
[data-testid="stHorizontalBlock"] { gap: 0.5rem; }
.st-ae, .main, .block-container { padding: 0 !important; }
.st-abw > div { background-color: #161B22; border: 1px solid #30363D; border-radius: 6px; padding: 0.5rem; color: #E6EDF3; }
h1, h2, h3, h4, p, span, label { color: #E6EDF3 !important; }
.st-cs, .st-cx, .st-cy { background-color: #161B22 !important; color: #E6EDF3 !important; border: 1px solid #30363D !important; }
</style>
""", unsafe_allow_html=True)

# ============== Session State ==============
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = '2330.TW'
if 'period' not in st.session_state:
    st.session_state.period = '1mo'

# ============== 股票清單（20檔）=============
STOCKS = [
    ('2330.TW', '台積電'), ('2317.TW', '鴻海'), ('2313.TW', '華通'), ('2887.TW', '台新金'),
    ('2454.TW', '聯發科'), ('2303.TW', '聯電'), ('2377.TW', '聯米'), ('2451.TW', '研華'),
    ('2474.TW', '世紀'), ('2603.TW', '長榮'), ('2881.TW', '元大金'), ('2882.TW', '國泰金'),
    ('2891.TW', '中信金'), ('2002.TW', '中鋼'), ('1216.TW', '統一'), ('1702.TW', '南僑'),
    ('2201.TW', '裕融'), ('2707.TW', '晶華'), ('2727.TW', '王品'), ('3042.TW', '創見'),
]

# ============== 技術指標計算 ==============
@st.cache_data(ttl=3600)
def get_stock_data(code, period='20d'):
    try:
        stock = yf.Ticker(code)
        hist = stock.history(period=period)
        return hist
    except:
        return None

def calc_score(hist):
    """計算總分（基於 5 日均線評分）"""
    if hist.empty or len(hist) < 5:
        return 0, {}
    
    close = hist['Close'].dropna()
    if close.empty:
        return 0, {}
    
    price = close.iloc[-1]
    score = 0
    details = {}
    
    # MA5 均線評分
    ma5 = close.rolling(5).mean().iloc[-1] if len(close) >= 5 else close.mean()
    if price > ma5:
        score += 3
        details['MA5'] = f'✅ 站上 MA5 ({ma5:.0f})'
    else:
        details['MA5'] = f'⚠️ 低於 MA5 ({ma5:.0f})'
    
    # 成交量評分
    vol = hist['Volume'].iloc[-1]
    vol_avg = hist['Volume'].iloc[-3:].mean() if len(hist) >= 3 else vol
    if vol > vol_avg:
        score += 2
        details['Volume'] = f'✅ 量增 ({vol/1000:.0f}K)'
    else:
        details['Volume'] = f'⚠️ 量縮 ({vol/1000:.0f}K)'
    
    return score, details

# ============== 主程式 ==============
st.markdown("# 📈 台股推薦儀表板")
st.markdown("### 每天早上推薦 20 檔分數最高的個股")
st.markdown(f"**更新時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 分析按鈕
if st.button("🔄 更新推薦", type="primary"):
    st.cache_data.clear()

# 評分所有股票
results = []
progress_bar = st.progress(0)
status_text = st.empty()

for i, (code, name) in enumerate(STOCKS):
    status_text.text(f"分析中: {code} {name}")
    progress_bar.progress((i + 1) / len(STOCKS))
    
    hist = get_stock_data(code)
    if hist is not None and not hist.empty:
        score, details = calc_score(hist)
        price = hist['Close'].iloc[-1]
        change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2] if len(hist) >= 2 else 0
        change_pct = (change / hist['Close'].iloc[-2]) * 100 if len(hist) >= 2 and hist['Close'].iloc[-2] != 0 else 0
        
        results.append({
            '代碼': code.replace('.TW', ''),
            '名稱': name,
            '現價': price,
            '漲跌': change,
            '漲跌%': change_pct,
            '總分': score,
            'MA5': details.get('MA5', '-'),
            'Volume': details.get('Volume', '-'),
        })

status_text.text("分析完成！")
progress_bar.empty()

# 排序並顯示
if results:
    df = pd.DataFrame(results)
    df = df.sort_values('總分', ascending=False).reset_index(drop=True)
    df['排名'] = range(1, len(df) + 1)
    df = df[['排名', '代碼', '名稱', '現價', '漲跌', '漲跌%', '總分', 'MA5', 'Volume']]
    
    st.markdown("## 🏆 推薦排名")
    
    # Top 5 卡片
    cols = st.columns(5)
    for idx, row in df.head(5).iterrows():
        with cols[idx]:
            color = COLORS['up'] if row['漲跌'] > 0 else COLORS['down']
            st.markdown(f"""
            <div style="background: {COLORS['card']}; border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 1rem; text-align: center;">
                <h4 style="color: {COLORS['text']}; margin: 0;">{row['名稱']}</h4>
                <p style="color: {color}; font-size: 1.5rem; margin: 0.5rem 0;">{row['現價']:.0f}</p>
                <p style="color: {color}; margin: 0;">{row['漲跌']:+.0f} ({row['漲跌%']:+.1f}%)</p>
                <p style="color: {COLORS['text_secondary']}; margin: 0.5rem 0 0;">{row['代碼']}</p>
                <p style="color: {COLORS['bullish']}; font-size: 1.2rem; margin: 0;">⭐ {row['總分']} 分</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 完整排名表格
    st.markdown("### 📊 完整排名")
    
    for idx, row in df.iterrows():
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 10])
            with col1:
                st.markdown(f"**#{row['排名']}**")
            with col2:
                st.markdown(f"**{row['名稱']}** `{row['代碼']}`")
            with col3:
                color = COLORS['up'] if row['漲跌'] > 0 else COLORS['down']
                st.markdown(f"<span style='color: {color}; font-size: 1.2rem;'>{row['現價']:.0f}</span>", unsafe_allow_html=True)
            with col4:
                st.markdown(f"<span style='color: {color};'> {row['漲跌']:+.0f} ({row['漲跌%']:+.1f}%)</span>", unsafe_allow_html=True)
            with col5:
                indicators = f"{row['MA5']} | {row['Volume']}"
                st.markdown(f"<span style='color: {COLORS['text_secondary']};'>{indicators}</span>", unsafe_allow_html=True)
            st.markdown("---")

else:
    st.error("無法取得股票資料，請稍後再試")
