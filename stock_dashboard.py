#!/usr/bin/env python3
"""
少爺專用 - 專業財經儀表板（含宏觀經濟）
使用方式: streamlit run stock_dashboard.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
import requests

# ===== 配色系統 =====
COLORS = {
    'background': '#0D1117',
    'card': '#161B22',
    'bullish': '#3FB950',     # 多頭 🟢
    'neutral': '#D29922',      # 中性 🟡
    'bearish': '#F85149',      # 空頭 🔴
    'text': '#E6EDF3',
    'text_secondary': '#8B949E',
}

# 頁面設定
st.set_page_config(
    page_title="少爺的股票儀表板",
    page_icon="📈",
    layout="wide"
)

# 自訂 CSS - 強迫所有元素使用深色主題
st.markdown("""
<style>
/* 全域背景 */
.stApp, .main, body { background-color: #0D1117 !important; }

/* 所有區塊/卡片背景 */
[data-testid="stHorizontalBlock"],
[data-testid="stVerticalBlock"],
.css-1d391kg, .css-12wkwq4, .css-1at1ahb,
.element-container, .st-dx, .st-bq, .st-d5, .st-cs, .st-cx {
    background-color: #161B22 !important;
}

/* 側邊欄背景 */
[data-testid="stSidebar"] { background-color: #161B22 !important; }
.css-1vbkw4y { background-color: #161B22 !important; }

/* 文字顏色 */
.stMarkdown, h1, h2, h3, h4, p, span, label { color: #E6EDF3 !important; }

/* Metric 顯示 */
div[data-testid="stMetricValue"] { color: #E6EDF3 !important; font-size: 1.8rem; }
div[data-testid="stMetricLabel"] { color: #8B949E !important; }

/* DataFrame 表格 */
[data-testid="stDataFrame"], .stDataFrame { background-color: #161B22 !important; }

/* 清除 Streamlit 預設白背景 */
.st-d6, .st-d7, .st-cj, .st-d4, .css-2trqyj { background-color: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ===== FRED API =====
FRED_API_KEY = 'edaa5b7562ebd132c42effa0193e5772'

@st.cache_data(ttl=3600)
def get_fred_data(series_id, name, months=12):
    try:
        url = f'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'limit': months,
            'sort_order': 'DESC'
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if 'observations' in data:
            observations = data['observations']
            df = pd.DataFrame(observations)
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna()
            df = df.sort_values('date')
            return df.rename(columns={'value': name})
        return None
    except Exception as e:
        print(f"FRED Error ({series_id}): {e}")
        return None

@st.cache_data(ttl=300)
def get_fred_latest(series_id):
    try:
        url = f'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'limit': 2,
            'sort_order': 'DESC'
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if 'observations' in data and len(data['observations']) >= 2:
            latest = float(data['observations'][0]['value'])
            previous = float(data['observations'][1]['value'])
            return latest, previous
        return None, None
    except:
        return None, None

@st.cache_data(ttl=60)
def get_market_data(ticker, period='1mo'):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period)
        return df
    except:
        return None

def get_ticker_price_change(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if info is None:
            return None, None, None
        price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')
        change = info.get('regularMarketChange') or info.get('change') or 0
        change_pct = info.get('regularMarketChangePercent') or 0
        if price is None:
            return None, None, None
        return price, change, change_pct
    except Exception as e:
        return None, None, None

def render_macro_card(title, latest_val, prev_val, unit='', status='neutral', bar_width=0.7):
    if latest_val is not None and prev_val is not None:
        change = latest_val - prev_val
        change_pct = (change / prev_val * 100) if prev_val != 0 else 0
    else:
        change = None
        change_pct = None
    
    if status == 'bullish':
        status_color = COLORS['bullish']
        arrow = '▲'
    elif status == 'bearish':
        status_color = COLORS['bearish']
        arrow = '▼'
    else:
        status_color = COLORS['neutral']
        arrow = '◆'
    
    if latest_val is not None:
        val_str = f"{latest_val:.2f}{unit}" if unit else f"{latest_val:.2f}"
    else:
        val_str = 'N/A'
    
    prev_str = f"{prev_val:.2f}{unit}" if prev_val is not None else 'N/A'
    change_str = f"{arrow} {abs(change_pct):.2f}%" if change is not None else ''
    
    card_html = f"""
    <div style="background-color: {COLORS['card']}; border-radius: 12px; padding: 16px; margin: 8px; border: 1px solid #30363D;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="color: {COLORS['text_secondary']}; font-size: 0.85rem;">{title}</span>
            <span style="color: {status_color}; font-size: 1.2rem;">●</span>
        </div>
        <div style="color: {COLORS['text']}; font-size: 1.5rem; font-weight: bold; margin-bottom: 8px;">{val_str}</div>
        <div style="background-color: #0D1117; border-radius: 4px; height: 6px; width: {bar_width*100}%; margin-bottom: 12px;">
            <div style="background-color: {status_color}; border-radius: 4px; height: 100%; width: 100%;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; color: {COLORS['text_secondary']}; font-size: 0.8rem;">
            <span>前值: {prev_str}</span>
            <span style="color: {status_color};">{change_str}</span>
        </div>
    </div>
    """
    return card_html

STOCKS = {
    '2330': '台積電', '2317': '鴻海', '3532': '台勝科', '1503': '士電',
    '2887': '台新新光金', '1605': '華新', '1717': '長興', '1802': '台玻'
}

US_STOCKS = {
    'NVDA': 'NVIDIA', 'TSLA': 'Tesla', 'AAPL': 'Apple', 'MSFT': 'Microsoft',
    'GOOGL': 'Google', 'META': 'Meta', 'AMZN': 'Amazon'
}

import os

def load_fundamentals():
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'stock_fundamentals.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['stocks'], data.get('update_date', '未知')
    except Exception as e:
        st.error(f"無法載入基本面資料: {e}")
        return {}, "載入失敗"

FUNDAMENTALS, FUNDAMENTALS_UPDATE_DATE = load_fundamentals()

@st.cache_data
def get_twse_data(code, days=90):
    try:
        all_data = []
        end_date = datetime.now()
        for i in range(0, days, 30):
            date_str = end_date.strftime('%Y%m%d')
            url = f'https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?&date={date_str}&stockNo={code}&response=json'
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            if data.get('stat') == 'OK' and data.get('data'):
                for row in data['data']:
                    try:
                        tw_date = row[0]
                        year = int(tw_date.split('/')[0]) + 1911
                        month = tw_date.split('/')[1]
                        day = tw_date.split('/')[2]
                        date = f"{year}-{month}-{day}"
                        all_data.append({
                            'Date': date, 'Open': float(row[3].replace(',', '')),
                            'High': float(row[4].replace(',', '')), 'Low': float(row[5].replace(',', '')),
                            'Close': float(row[6].replace(',', '')), 'Volume': int(row[1].replace(',', ''))
                        })
                    except:
                        continue
            import time; time.sleep(0.5)
        if all_data:
            df = pd.DataFrame(all_data)
            df['Date'] = pd.to_datetime(df['Date'])
            return df.sort_values('Date')
        return None
    except Exception as e:
        print(f"TWSE Error: {e}")
        return None

@st.cache_data
def get_stock_data(code, period="1mo"):
    df = get_twse_data(code)
    if df is not None and not df.empty:
        return df
    try:
        ticker = yf.Ticker(f"{code}.TW")
        return ticker.history(period=period)
    except:
        return None

@st.cache_data  
def get_us_stock_data(code, period="5d"):
    try:
        ticker = yf.Ticker(code)
        return ticker.history(period=period)
    except:
        return None

def calculate_ma(df, days):
    return df['Close'].rolling(window=days).mean()

def calculate_rsi(df, days=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=days).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=days).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data
def get_fundamental_data(code):
    if code in FUNDAMENTALS:
        data = FUNDAMENTALS[code]
        return {
            'EPS': data.get('EPS'), '本益比': data.get('本益比'),
            '殖利率': data.get('殖利率'), '股息': data.get('股息'),
            '每股淨值': data.get('每股淨值'), '股價淨值比': data.get('股價淨值比'),
            '52週最高': None, '52週最低': None, '市值': None,
            '產業': data.get('產業'), '產業類別': None,
            '財報季度': data.get('財報季度', 'N/A'),
            '備註': data.get('備註', ''),
            '資料來源': f'證交所 ({FUNDAMENTALS_UPDATE_DATE})'
        }
    try:
        ticker = yf.Ticker(f"{code}.TW")
        info = ticker.info
        fundamentals = {
            'EPS': info.get('trailingEps'), '本益比': info.get('trailingPE'),
            '殖利率': info.get('dividendYield'), '股息': info.get('dividendRate'),
            '每股淨值': info.get('bookValue'), '股價淨值比': info.get('priceToBook'),
            '52週最高': info.get('fiftyTwoWeekHigh'), '52週最低': info.get('fiftyTwoWeekLow'),
            '市值': info.get('marketCap'), '產業': info.get('sector'),
            '產業類別': info.get('industry'), '資料來源': 'yfinance'
        }
        if fundamentals.get('EPS') or fundamentals.get('本益比'):
            return fundamentals
    except:
        pass
    return None

# ===== 側邊欄 =====
st.sidebar.title("📈 少爺的股票儀表板")
st.sidebar.markdown("---")

# 主導航分頁
page_options = {
    "🌐 宏觀局勢": "macro",
    "📈 即時股票": "stock", 
    "🏭 產業分析": "industry",
    "🤖 龍龍操盤": "us_stock"
}
selected_page = st.sidebar.radio("📌 選擇功能", list(page_options.keys()), index=0)
page_key = page_options[selected_page]

st.sidebar.markdown("---")

# 初始化默認值（避免跨區塊引用錯誤）
selected_stock = list(STOCKS.items())[0]
period = "3mo"
indicators = ["MA20"]

if page_key == "stock":
    selected_stock = st.sidebar.selectbox("選擇股票", list(STOCKS.items()), format_func=lambda x: f"{x[1]} ({x[0]})")
    period = st.sidebar.selectbox("選擇時間範圍", ["1mo", "3mo", "6mo", "1y", "2y"], index=1, format_func=lambda x: {"1mo": "1個月", "3mo": "3個月", "6mo": "6個月", "1y": "1年", "2y": "2年"}[x])
    indicators = st.sidebar.multiselect("技術指標", ["MA5", "MA20", "MA60", "RSI", "Volume"], default=["MA20"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 快速連結")
st.sidebar.markdown("- [Yahoo 股市](https://tw.stock.yahoo.com/)")
st.sidebar.markdown("- [TradingView](https://www.tradingview.com/)")

# ===== 主頁面 =====
st.title("🌐 少爺的股票儀表板（含宏觀經濟）")

# ================================================
# 🌐 第一區塊：宏觀局勢分析
# ================================================
if page_key == "macro" or page_key not in ["macro", "stock", "industry", "us_stock"]:
    st.markdown("---")
    st.markdown("### 🌐 宏觀局勢分析")

fed_rate, fed_prev = get_fred_latest('FEDFUNDS')
unemp_rate, unemp_prev = get_fred_latest('UNRATE')
cpi, cpi_prev = get_fred_latest('CPIAUCSL')
cpi_yoy = ((cpi / cpi_prev) - 1) * 100 * 12 if cpi is not None and cpi_prev is not None and cpi_prev > 0 else None
gdp, gdp_prev = get_fred_latest('GDP')
tnxy, tnxy_change, tnxy_change_pct = get_ticker_price_change('^TNX')
vix_price, vix_change, vix_change_pct = get_ticker_price_change('^VIX')
sp_price, sp_change, sp_change_pct = get_ticker_price_change('^GSPC')
nasdaq_price, nasdaq_change, nasdaq_change_pct = get_ticker_price_change('^IXIC')
dxy_price, dxy_change, dxy_change_pct = get_ticker_price_change('DX-Y.NYB')
gold_price, gold_change, gold_change_pct = get_ticker_price_change('GC=F')
btc_price, btc_change, btc_change_pct = get_ticker_price_change('BTC-USD')
nvda_price, nvda_change, nvda_change_pct = get_ticker_price_change('NVDA')
tsm_price, tsm_change, tsm_change_pct = get_ticker_price_change('TSM')
qqq_price, qqq_change, qqq_change_pct = get_ticker_price_change('QQQ')
hy_spread, hy_prev = get_fred_latest('BAMLEMBISPREAD')
ig_spread, ig_prev = get_fred_latest('BAMLEASPPISAC')

# 第一排：核心巨觀指標
st.markdown("#### 📊 核心巨觀指標")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    status = 'bearish' if fed_rate and fed_rate > 5 else 'neutral'
    st.markdown(render_macro_card('🏦 Fed利率', fed_rate, fed_prev, '%', status), unsafe_allow_html=True)
with c2:
    status = 'bearish' if unemp_rate and unemp_rate > 5 else 'bullish'
    st.markdown(render_macro_card('👷 失業率', unemp_rate, unemp_prev, '%', status), unsafe_allow_html=True)
with c3:
    status = 'bearish' if cpi_yoy and cpi_yoy > 3 else 'neutral'
    st.markdown(render_macro_card('📈 CPI通膨(年)', cpi_yoy, None, '%', status), unsafe_allow_html=True)
with c4:
    gdp_growth = ((gdp / gdp_prev) - 1) * 100 if gdp and gdp_prev else None
    status = 'bullish' if gdp_growth and gdp_growth > 2 else 'neutral'
    st.markdown(render_macro_card('📊 GDP季增率', gdp_growth, None, '%', status), unsafe_allow_html=True)
with c5:
    status = 'bearish' if tnxy and tnxy > 4.5 else 'neutral'
    st.markdown(render_macro_card('💵 10年債殖利率', tnxy, tnxy_change, '%', status), unsafe_allow_html=True)

# 第二排：市場情緒
st.markdown("#### 😰 市場情緒 & 資金流向")
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    status = 'bearish' if vix_price and vix_price > 25 else 'bullish' if vix_price and vix_price < 15 else 'neutral'
    st.markdown(render_macro_card('😰 VIX恐慌', vix_price, None, '', status, 0.3), unsafe_allow_html=True)
with c2:
    st.markdown(render_macro_card('📈 S&P 500', sp_price, None, '', 'neutral', 0.8), unsafe_allow_html=True)
with c3:
    st.markdown(render_macro_card('🔷 Nasdaq', nasdaq_price, None, '', 'neutral', 0.8), unsafe_allow_html=True)
with c4:
    status = 'bullish' if dxy_price and dxy_price > 105 else 'bearish' if dxy_price and dxy_price < 100 else 'neutral'
    st.markdown(render_macro_card('💵 美元指數', dxy_price, None, '', status), unsafe_allow_html=True)
with c5:
    status = 'bullish' if gold_change and gold_change > 0 else 'bearish'
    st.markdown(render_macro_card('🥇 黃金', gold_price, None, '', status), unsafe_allow_html=True)
with c6:
    status = 'bullish' if btc_change and btc_change > 0 else 'bearish'
    st.markdown(render_macro_card('₿ BTC', btc_price, None, '', status), unsafe_allow_html=True)

# 第三排：AI科技
st.markdown("#### 🤖 AI科技 & 關鍵指標")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    status = 'bullish' if nvda_change and nvda_change > 0 else 'bearish'
    st.markdown(render_macro_card('🤖 NVDA', nvda_price, None, '', status), unsafe_allow_html=True)
with c2:
    status = 'bullish' if tsm_change and tsm_change > 0 else 'bearish'
    st.markdown(render_macro_card('⚡ TSM 台積電', tsm_price, None, '', status), unsafe_allow_html=True)
with c3:
    status = 'bullish' if qqq_change and qqq_change > 0 else 'bearish'
    st.markdown(render_macro_card('📊 QQQ 納指', qqq_price, None, '', status), unsafe_allow_html=True)
with c4:
    status = 'bearish' if hy_spread and hy_spread > 500 else 'bullish' if hy_spread and hy_spread < 300 else 'neutral'
    st.markdown(render_macro_card('💳 HY利差(bp)', hy_spread, hy_prev, '', status), unsafe_allow_html=True)
with c5:
    status = 'bearish' if ig_spread and ig_spread > 150 else 'bullish' if ig_spread and ig_spread < 100 else 'neutral'
    st.markdown(render_macro_card('💳 IG利差(bp)', ig_spread, ig_prev, '', status), unsafe_allow_html=True)

# 情境 Banner
if vix_price:
    if vix_price > 25:
        mood, mood_color, suggestion = "⚠️ 市場恐慌", COLORS['bearish'], "持有現金、降低科技股曝險"
    elif vix_price < 15:
        mood, mood_color, suggestion = "✅ 市場穩定", COLORS['bullish'], "積極佈局，但留意本益比"
    else:
        mood, mood_color, suggestion = "📊 中性觀望", COLORS['neutral'], "區間操作，等待方向"
else:
    mood, mood_color, suggestion = "📊 載入中...", COLORS['neutral'], ""

if tnxy:
    if tnxy > 4.5:
        rate_msg, rate_color = "⚠️ 升息壓力大", COLORS['bearish']
    elif tnxy > 3.5:
        rate_msg, rate_color = "📊 利率正常", COLORS['neutral']
    else:
        rate_msg, rate_color = "🔽 低利率環境", COLORS['bullish']
else:
    rate_msg, rate_color = "", COLORS['neutral']

st.markdown(f"""
<div style="background: linear-gradient(135deg, {COLORS['card']} 0%, #1a2332 100%); border-radius: 16px; padding: 24px; margin: 16px 0; border: 1px solid #30363D; text-align: center;">
    <h2 style="color: {mood_color}; margin-bottom: 8px;">{mood}</h2>
    <p style="color: {COLORS['text_secondary']}; font-size: 1rem;">
        利率環境: <span style="color: {rate_color};">{rate_msg}</span>
        &nbsp;|&nbsp;
        建議: <span style="color: {COLORS['text']};">{suggestion}</span>
    </p>
</div>
""", unsafe_allow_html=True)

# ================================================
# 📈 第二區塊：即時股票
# ================================================
if page_key == "stock":
    st.markdown("---")
    st.markdown(f"### 📈 即時股票：{selected_stock[1]} ({selected_stock[0]})")

df = get_stock_data(selected_stock[0], period)

if df is not None and len(df) > 0:
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
    change = current_price - prev_price
    change_pct = (change / prev_price) * 100
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("現在價格", f"${current_price:.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
    with c2:
        st.metric("最高價", f"${df['High'].max():.2f}")
    with c3:
        st.metric("最低價", f"${df['Low'].min():.2f}")
    
    st.markdown("#### 📊 K線圖")
    candle = go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線')
    fig = go.Figure(data=[candle])
    
    if "MA5" in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=calculate_ma(df, 5), name='MA5', line=dict(color='blue', width=1)))
    if "MA20" in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=calculate_ma(df, 20), name='MA20', line=dict(color='purple', width=2)))
    if "MA60" in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=calculate_ma(df, 60), name='MA60', line=dict(color='orange', width=2)))
    
    fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_dark",
                      title=f"{selected_stock[1]} K線圖", yaxis_title="價格", xaxis_title="日期")
    st.plotly_chart(fig, use_container_width=True)
    
    if "RSI" in indicators:
        st.markdown("#### 📉 RSI 指標")
        rsi = calculate_rsi(df)
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI', line=dict(color='yellow', width=2)))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超買")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超賣")
        fig_rsi.add_hline(y=50, line_dash="dot", line_color="gray")
        fig_rsi.update_layout(height=250, template="plotly_dark", title="RSI (14)", yaxis_title="RSI", yaxis_range=[0, 100])
        st.plotly_chart(fig_rsi, use_container_width=True)
    
    if "Volume" in indicators:
        st.markdown("#### 📊 成交量")
        colors_vol = ['red' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'green' for i in range(len(df))]
        fig_vol = go.Figure(data=[go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=colors_vol)])
        fig_vol.update_layout(height=200, template="plotly_dark", title="成交量", yaxis_title="成交量")
        st.plotly_chart(fig_vol, use_container_width=True)
    
    st.markdown("---")
    st.markdown("#### 💡 技術分析建議")
    
    ma5 = calculate_ma(df, 5).iloc[-1]
    ma20 = calculate_ma(df, 20).iloc[-1]
    ma60 = calculate_ma(df, 60).iloc[-1] if len(df) >= 60 else None
    rsi_val = calculate_rsi(df).iloc[-1]
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**均線狀態：**")
        if ma5 > ma20:
            st.success(f"✅ MA5 > MA20 → 短線偏多")
        else:
            st.warning(f"⚠️ MA5 < MA20 → 短線偏空")
        if ma60 is not None:
            if ma20 > ma60:
                st.success(f"✅ MA20 > MA60 → 中線偏多")
            else:
                st.warning(f"⚠️ MA20 < MA60 → 中線偏空")
        else:
            st.info("📊 數據不足60天，無法計算MA60")
    with c2:
        st.markdown("**RSI 狀態：**")
        if rsi_val > 70:
            st.warning(f"⚠️ RSI = {rsi_val:.1f} → 超買區，可能回檔")
        elif rsi_val < 30:
            st.success(f"✅ RSI = {rsi_val:.1f} → 超賣區，可能反彈")
        else:
            st.info(f"➡️ RSI = {rsi_val:.1f} → 區間整理")
    
    st.markdown("---")
    st.markdown("#### 📋 基本面數據 (資料來源：證交所)")
    fundamentals = get_fundamental_data(selected_stock[0])
    
    if fundamentals:
        c0, c1, c2, c3, c4 = st.columns(5)
        with c0:
            st.metric("財報季度", fundamentals.get('財報季度', 'N/A'))
        eps = fundamentals.get('EPS')
        with c1:
            st.metric("EPS", f"${eps:.2f}" if eps and eps != 'N/A' else "N/A")
        pe = fundamentals.get('本益比')
        with c2:
            st.metric("本益比 (P/E)", f"{pe:.2f}" if pe and pe != 'N/A' else "N/A")
        div_yield = fundamentals.get('殖利率')
        with c3:
            if div_yield and div_yield != 'N/A':
                if isinstance(div_yield, str):
                    div_yield = div_yield.replace('%', '')
                    try: div_yield = float(div_yield)
                    except: div_yield = 'N/A'
                if div_yield != 'N/A':
                    st.metric("殖利率", f"{div_yield:.2f}%")
                else:
                    st.metric("殖利率", "N/A")
            else:
                st.metric("殖利率", "N/A")
        with c4:
            pb = fundamentals.get('每股淨值')
            st.metric("每股淨值", f"${pb:.2f}" if pb and pb != 'N/A' else "N/A")
        
        update_note = fundamentals.get('備註', '')
        if update_note:
            st.caption(f"📅 {update_note}")
        
        sector = fundamentals.get('產業')
        industry = fundamentals.get('產業類別')
        if sector or industry:
            st.markdown(f"**產業：** {sector} / {industry}")
        
        market_cap = fundamentals.get('市值')
        if market_cap:
            if market_cap > 1e12:
                cap_str = f"${market_cap/1e12:.2f}兆"
            elif market_cap > 1e9:
                cap_str = f"${market_cap/1e9:.2f}億"
            else:
                cap_str = f"${market_cap/1e6:.2f}M"
            st.markdown(f"**市值：** {cap_str}")
else:
    st.error("無法取得股票數據，請稍後再試")

# ================================================
# 🏭 第三區塊：產業分析
# ================================================
if page_key == "industry":
    st.markdown("---")
    st.markdown("### 🏭 產業分析：少爺的8檔股票")

prices_data = []
for code, name in STOCKS.items():
    df_stock = get_stock_data(code, "5d")
    if df_stock is not None and len(df_stock) > 0:
        current = df_stock['Close'].iloc[-1]
        prev = df_stock['Close'].iloc[-2] if len(df_stock) > 1 else current
        change = ((current - prev) / prev) * 100
        prices_data.append({'代號': code, '名稱': name, '現價': current, '漲跌幅': change})

if prices_data:
    df_prices = pd.DataFrame(prices_data).sort_values('漲跌幅', ascending=False)
    def color_change(val):
        return f'color: {"green" if val > 0 else "red" if val < 0 else "gray"}'
    st.dataframe(df_prices.style.format({'現價': '${:.2f}', '漲跌幅': '{:+.2f}%'}).applymap(color_change, subset=['漲跌幅']), use_container_width=True)

# ================================================
# 🌍 第四區塊：龍龍操盤 - 美股
# ================================================
if page_key == "us_stock":
    st.markdown("---")
    st.markdown("### 🌍 龍龍操盤：美股昨晚表現")

us_prices = []
for code, name in US_STOCKS.items():
    df_us = get_us_stock_data(code)
    if df_us is not None and len(df_us) > 0:
        current = df_us['Close'].iloc[-1]
        prev = df_us['Close'].iloc[-2] if len(df_us) > 1 else current
        change = ((current - prev) / prev) * 100
        us_prices.append({'代號': code, '名稱': name, '現價': current, '漲跌幅': change})

if us_prices:
    df_us_prices = pd.DataFrame(us_prices).sort_values('漲跌幅', ascending=False)
    st.dataframe(df_us_prices.style.format({'現價': '${:.2f}', '漲跌幅': '{:+.2f}%'}).applymap(color_change, subset=['漲跌幅']), use_container_width=True)

# ===== 頁腳 =====
st.markdown("---")
st.markdown(f"*📊 資料更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
st.markdown("*本報告僅供參考，不構成投資建議*")
