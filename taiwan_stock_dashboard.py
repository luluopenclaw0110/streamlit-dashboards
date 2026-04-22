#!/usr/bin/env python3
"""台股投資策略分析行情儀錶板 - 每天推薦 20 檔分數最高的個股"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

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
    page_title="台股投資策略分析行情儀錶板",
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

# ============== 大盤指數 ==============
@st.cache_data(ttl=300)
def get_market_indices():
    """取得大盤指數"""
    indices = {}
    try:
        twii = yf.Ticker("^TWII")
        twii_hist = twii.history(period="5d")
        if not twii_hist.empty:
            price = twii_hist['Close'].iloc[-1]
            prev = twii_hist['Close'].iloc[-2] if len(twii_hist) >= 2 else price
            change = price - prev
            pct = (change / prev) * 100 if prev != 0 else 0
            indices['加權指數'] = {'price': price, 'change': change, 'pct': pct}
    except:
        pass
    
    try:
        otc = yf.Ticker("^TaiwanOTC")
        otc_hist = otc.history(period="5d")
        if not otc_hist.empty:
            price = otc_hist['Close'].iloc[-1]
            prev = otc_hist['Close'].iloc[-2] if len(otc_hist) >= 2 else price
            change = price - prev
            pct = (change / prev) * 100 if prev != 0 else 0
            indices['櫃買指數'] = {'price': price, 'change': change, 'pct': pct}
    except:
        pass
    
    return indices

# ============== 技術指標計算 ==============
@st.cache_data(ttl=3600)
def get_stock_data(code, period='20d'):
    try:
        stock = yf.Ticker(code)
        hist = stock.history(period=period)
        return hist
    except:
        return None

def calc_rsi(prices, period=14):
    if len(prices) < period:
        return None
    deltas = prices.diff()
    gain = deltas.where(deltas > 0, 0).rolling(window=period).mean()
    loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else None

def calc_kd(hist, k_period=9, d_period=3):
    if len(hist) < k_period:
        return None, None
    low_min = hist['Low'].rolling(window=k_period).min()
    high_max = hist['High'].rolling(window=k_period).max()
    rsv = (hist['Close'] - low_min) / (high_max - low_min) * 100
    rsv = rsv.fillna(50)
    k = rsv.rolling(window=d_period).mean().iloc[-1]
    d = pd.Series(k).rolling(window=d_period).mean().iloc[-1]
    return k if not np.isnan(k) else None, d if not np.isnan(d) else None

def calc_macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow:
        return None, None
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line.iloc[-1], histogram.iloc[-1]

def calc_ma(prices, period):
    if len(prices) < period:
        return None
    return prices.rolling(window=period).mean().iloc[-1]

def calc_score_enhanced(hist):
    """計算總分（增強版：MA5 + RSI + KD + MACD + Volume）"""
    if hist.empty or len(hist) < 20:
        return 0, {}
    
    close = hist['Close'].dropna()
    if close.empty:
        return 0, {}
    
    price = close.iloc[-1]
    score = 0
    details = {}
    
    ma5 = calc_ma(close, 5)
    if ma5 and price > ma5:
        score += 3
        details['MA5'] = f'✅ 站上 MA5 ({ma5:.0f})'
    elif ma5:
        details['MA5'] = f'⚠️ 低於 MA5 ({ma5:.0f})'
    
    ma20 = calc_ma(close, 20)
    if ma20 and price > ma20:
        score += 2
        details['MA20'] = f'✅ 站上 MA20 ({ma20:.0f})'
    elif ma20:
        details['MA20'] = f'⚠️ 低於 MA20 ({ma20:.0f})'
    
    rsi = calc_rsi(close)
    if rsi:
        details['RSI'] = f'RSI: {rsi:.1f}'
        if rsi < 30:
            score += 3
            details['RSI'] += ' 超賣 ✅'
        elif rsi > 70:
            details['RSI'] += ' 超買 ⚠️'
        else:
            details['RSI'] += ' 正常'
    
    k, d = calc_kd(hist)
    if k is not None and d is not None:
        details['KD'] = f'K: {k:.1f} D: {d:.1f}'
        if k < 30 and d < 30 and k > d:
            score += 3
            details['KD'] += ' 低檔黃金交叉 ✅'
        elif k > 70 and d > 70 and k < d:
            details['KD'] += ' 高檔死亡交叉 ⚠️'
    
    macd, histogram = calc_macd(close)
    if macd is not None:
        details['MACD'] = f'MACD: {macd:.2f}'
        if histogram > 0:
            score += 2
            details['MACD'] += ' 柱狀正值 ✅'
        else:
            details['MACD'] += ' 柱狀負值 ⚠️'
    
    vol = hist['Volume'].iloc[-1]
    vol_avg = hist['Volume'].iloc[-5:].mean() if len(hist) >= 5 else vol
    if vol > vol_avg * 1.5:
        score += 2
        details['Volume'] = f'✅ 量增 ({vol/1000:.0f}K)'
    elif vol > vol_avg:
        score += 1
        details['Volume'] = f'微量增加 ({vol/1000:.0f}K)'
    else:
        details['Volume'] = f'⚠️ 量縮 ({vol/1000:.0f}K)'
    
    return score, details

@st.cache_data(ttl=1800)
def get_stock_news(code):
    try:
        stock = yf.Ticker(code)
        news = stock.news
        if news:
            return news[:3]
    except:
        pass
    return []

def show_stock_detail(code, name):
    st.markdown(f"## 📊 {name} ({code}) 詳細分析")
    
    hist = get_stock_data(code, '3mo')
    if hist is None or hist.empty:
        st.error("無法取得資料")
        return
    
    close = hist['Close'].dropna()
    if close.empty:
        st.error("無價格資料")
        return
    
    price = close.iloc[-1]
    prev_price = close.iloc[-2] if len(close) >= 2 else price
    change = price - prev_price
    pct = (change / prev_price) * 100 if prev_price != 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("現價", f"{price:.0f}", f"{change:+.0f} ({pct:+.1f}%)")
    with col2:
        ma5 = calc_ma(close, 5)
        st.metric("MA5", f"{ma5:.0f}" if ma5 else "-")
    with col3:
        ma20 = calc_ma(close, 20)
        st.metric("MA20", f"{ma20:.0f}" if ma20 else "-")
    with col4:
        rsi = calc_rsi(close)
        st.metric("RSI(14)", f"{rsi:.1f}" if rsi else "-")
    
    k, d = calc_kd(hist)
    st.markdown(f"**KD 指標:** K = {k:.1f}, D = {d:.1f}" if k else "**KD:** 無資料")
    
    macd, histogram = calc_macd(close)
    st.markdown(f"**MACD:** {macd:.2f} (柱狀: {histogram:+.2f})" if macd else "**MACD:** 無資料")
    
    st.markdown("### 價格與技術指標")
    chart_data = pd.DataFrame({
        'Close': close,
        'MA5': close.rolling(5).mean(),
        'MA20': close.rolling(20).mean(),
    })
    st.line_chart(chart_data)
    
    st.markdown("### 最新新聞")
    news = get_stock_news(code)
    if news:
        for item in news:
            st.markdown(f"- [{item.get('title', '無標題')}]({item.get('link', '#')})")
    else:
        st.info("暫無新聞")

# ============== 主程式 ==============
st.markdown("# 📈 台股投資策略分析行情儀錶板")
st.markdown("### 台股投資策略 | 技術分析 | 每日推薦")
st.markdown(f"**更新時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.markdown("## 📊 大盤概況")
indices = get_market_indices()
if indices:
    cols = st.columns(len(indices))
    for idx, (name, data) in enumerate(indices.items()):
        with cols[idx]:
            color = COLORS['up'] if data['change'] > 0 else COLORS['down']
            st.markdown(f"""
            <div style="background: {COLORS['card']}; border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 1rem; text-align: center;">
                <h4 style="color: {COLORS['text']}; margin: 0;">{name}</h4>
                <p style="color: {color}; font-size: 1.5rem; margin: 0.5rem 0;">{data['price']:,.0f}</p>
                <p style="color: {color}; margin: 0;">{data['change']:+,.0f} ({data['pct']:+.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("無法取得大盤指數")

tab1, tab2 = st.tabs(["📈 推薦選股", "📊 個股查詢"])

with tab1:
    st.markdown("## 🏆 每日推薦 TOP 20")
    st.markdown("基於 MA5、RSI、KD、MACD、成交量綜合評分")
    
    col_update, col_period = st.columns([1, 3])
    with col_update:
        if st.button("🔄 更新推薦", type="primary"):
            st.cache_data.clear()
    with col_period:
        period = st.selectbox("資料週期", ["1mo", "3mo", "6mo"], index=0)
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (code, name) in enumerate(STOCKS):
        status_text.text(f"分析中: {code} {name}")
        progress_bar.progress((i + 1) / len(STOCKS))
        
        hist = get_stock_data(code)
        if hist is not None and not hist.empty:
            score, details = calc_score_enhanced(hist)
            price = hist['Close'].iloc[-1]
            change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2] if len(hist) >= 2 else 0
            change_pct = (change / hist['Close'].iloc[-2]) * 100 if len(hist) >= 2 and hist['Close'].iloc[-2] != 0 else 0
            
            results.append({
                '代碼': code.replace('.TW', ''),
                '名稱': name,
                '現價': int(price),
                '漲跌': round(change, 2),
                '漲跌%': round(change_pct, 2),
                '總分': score,
                'MA5': details.get('MA5', '-'),
                'MA20': details.get('MA20', '-'),
                'RSI': details.get('RSI', '-'),
                'KD': details.get('KD', '-'),
                'MACD': details.get('MACD', '-'),
                'Volume': details.get('Volume', '-'),
            })
    
    status_text.text("分析完成！")
    progress_bar.empty()
    
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values('總分', ascending=False).reset_index(drop=True)
        df['排名'] = range(1, len(df) + 1)
        
        st.markdown("### 🏅 TOP 5 推薦")
        cols = st.columns(5)
        for idx, row in df.head(5).iterrows():
            with cols[idx]:
                color = COLORS['up'] if row['漲跌'] > 0 else COLORS['down']
                st.markdown(f"""
                <div style="background: {COLORS['card']}; border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 1rem; text-align: center;">
                    <h4 style="color: {COLORS['text']}; margin: 0;">{row['名稱']}</h4>
                    <p style="color: {color}; font-size: 1.5rem; margin: 0.5rem 0;">{row['現價']}</p>
                    <p style="color: {color}; margin: 0;">{row['漲跌']:+g} ({row['漲跌%']:+.1f}%)</p>
                    <p style="color: {COLORS['text_secondary']}; margin: 0.5rem 0 0;">{row['代碼']}</p>
                    <p style="color: {COLORS['bullish']}; font-size: 1.2rem; margin: 0;">⭐ {row['總分']} 分</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("### 📋 完整排名")
        display_cols = ['排名', '代碼', '名稱', '現價', '漲跌', '漲跌%', '總分', 'MA5', 'RSI']
        df_display = df[display_cols].copy()
        st.dataframe(df_display, use_container_width=True)
        
        st.markdown("### 📊 技術面詳細分析")
        for idx, row in df.iterrows():
            with st.expander(f"#{row['排名']} {row['名稱']} ({row['代碼']}) - 總分: {row['總分']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**MA5:** {row['MA5']}")
                    st.markdown(f"**MA20:** {row['MA20']}")
                    st.markdown(f"**RSI:** {row['RSI']}")
                with col2:
                    st.markdown(f"**KD:** {row['KD']}")
                    st.markdown(f"**MACD:** {row['MACD']}")
                    st.markdown(f"**成交量:** {row['Volume']}")
    else:
        st.error("無法取得股票資料，請稍後再試")

with tab2:
    st.markdown("## 📊 個股查詢")
    stock_options = [f"{code} - {name}" for code, name in STOCKS]
    selected = st.selectbox("選擇股票", stock_options, index=0)
    code = selected.split(" - ")[0]
    name = selected.split(" - ")[1]
    
    if st.button("查詢", type="primary"):
        show_stock_detail(code + ".TW", name)

st.markdown("---")
st.markdown("📈 台股投資策略分析行情儀錶板 | 資料來源: Yahoo Finance | 每小時更新")