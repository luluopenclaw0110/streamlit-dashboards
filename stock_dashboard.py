#!/usr/bin/env python3
"""
少爺專用 - 整合式單頁股票儀表板
使用方式: streamlit run stock_dashboard.py
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas as pd
from datetime import datetime
import json
import requests
import os
import time

# ===== 配色系統 =====
COLORS = {
    'background': '#0D1117',
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
    page_title="龍龍的12檔股票",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=dict()
)

st.markdown("""
<style>
.stApp, .main, body { background-color: #0D1117 !important; }
[data-testid="stHorizontalBlock"], [data-testid="stVerticalBlock"],
.css-1d391kg, .css-12wkwq4, .css-1at1ahb, .element-container { background-color: #161B22 !important; }
[data-testid="stSidebar"] { background-color: #161B22 !important; }
.stMarkdown, h1, h2, h3, h4, p, span, label { color: #E6EDF3 !important; }
[data-testid="stMainBlockContainer"] { padding-top: 2rem !important; padding-bottom: 8rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
/* Tab 名稱不靠近邊緣 */
[data-testid="stTab"] { padding: 0.5rem 1rem !important; }
[data-testid="stTabList"] { gap: 0.5rem !important; padding: 0 0.5rem !important; }
.stMarkdown h3, .stMarkdown h4 { margin-left: 0.5rem !important; margin-right: 0.5rem !important; }
.css-1lcbmhc.e1fqkh3o3 { padding-left: 1rem; }
div[data-testid="stMetricValue"] { color: #E6EDF3 !important; font-size: 1.8rem; }
div[data-testid="stMetricLabel"] { color: #8B949E !important; }
[data-testid="stDataFrame"] { background-color: #161B22 !important; }
.st-d6, .st-d7, .st-cj, .st-d4, .css-2trqyj { background-color: transparent !important; }
.stSelectbox > div > div, .stMultiSelect > div > div { background-color: #0D1117 !important; color: #E6EDF3 !important; }
header[data-testid="stHeader"] { background-color: #0D1117 !important; }
.stMultiSelect [data-testid="stMultiSelect"] > div > div > div { flex-wrap: wrap; gap: 4px; }
.element-container { margin-left: 4px; margin-right: 4px; }
</style>
""", unsafe_allow_html=True)

# ===== Session State =====
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = '2330'
if 'period' not in st.session_state:
    st.session_state.period = '3mo'
if 'indicators' not in st.session_state:
    st.session_state.indicators = ['MA20', 'RSI', 'Volume']

# ===== 常量 =====
FRED_API_KEY = 'edaa5b7562ebd132c42effa0193e5772'
STOCKS = {
    '1503': '士電', '1605': '華新', '1717': '長興', '1802': '台玻',
    '2317': '鴻海', '2330': '台積電', '2887': '台新新光金',
    '3532': '台勝科', '4716': '大立', '5543': '均豪', '6613': '朋億', '6667': '信紘科'
}
STOCK_OPTIONS = [f"{code} {name}" for code, name in STOCKS.items()]

# ===== FRED API =====
@st.cache_data(ttl=3600)
def get_fred_latest(series_id):
    try:
        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'limit': 4,
            'sort_order': 'desc'
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if 'error_code' in data:
            return None, None
        if 'observations' in data and len(data['observations']) >= 2:
            obs = data['observations']
            non_null = [float(o['value']) for o in obs if o['value'] not in ('', 'None', '.', None) and o['value'] is not None]
            if len(non_null) >= 2:
                return non_null[0], non_null[1]
            elif len(non_null) == 1:
                return non_null[0], None
        return None, None
    except Exception:
        return None, None

# ===== Yahoo Finance =====
@st.cache_data(ttl=60)
def get_ticker_info(ticker):
    """get_ticker_info with retry, 15s timeout, and TWSE fallback"""
    # 1. Try Yahoo Finance with retry
    for attempt in range(3):
        try:
            t = yf.Ticker(ticker)
            info = t.info
            if info and (info.get('regularMarketPrice') or info.get('currentPrice')):
                return info
        except Exception:
            pass
        if attempt < 2:
            time.sleep(0.3)
    # 2. Try yf.download as fallback
    try:
        df = yf.download(ticker, period='5d', interval='1d', progress=False, timeout=15)
        if df is not None and not df.empty:
            close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2] if len(df) > 1 else close
            change = close - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0
            return {
                'regularMarketPrice': float(close),
                'regularMarketChange': float(change),
                'regularMarketChangePercent': float(change_pct)
            }
    except Exception:
        pass
    # 3. TWSE fallback (for codes like 4716, 5543)
    code = ticker.replace('.TW', '').replace('^', '')
    twse_result = _get_twse_realtime(code)
    if twse_result:
        return twse_result
    return {}

def _get_twse_realtime(code):
    """從 TWSE 取得即時股價"""
    try:
        url = f"https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?&date=&stockNo={code}&response=json"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        r = requests.get(url, headers=headers, timeout=15)
        # TWSE doesn't have real-time; try alternative endpoint
        url2 = f"https://www.twse.com.tw/rwd/zh/realTime/getQuote?exch=TSE&str={code}&delay=0"
        r2 = requests.get(url2, headers=headers, timeout=15)
        if r2.status_code == 200:
            data = r2.json()
            if data.get('rtCode') == '0000':
                fields = data.get('rtData', {}).get('quote', {})
                price = fields.get('z') or fields.get('c')
                if price and price not in ('-', '', 'N/A'):
                    return {'regularMarketPrice': float(price), 'regularMarketChange': 0.0, 'regularMarketChangePercent': 0.0}
    except Exception:
        pass
    return None

@st.cache_data(ttl=120)
def get_yf_history(ticker, period='3mo'):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period)
        return df if df is not None and not df.empty else None
    except Exception:
        return None

# ===== TWSE 資料 =====
@st.cache_data(ttl=300)
def get_twse_data(code, days=120):
    """從 TWSE 取得日 K 資料"""
    try:
        all_data = []
        end_date = datetime.now()
        months_to_fetch = (days // 30) + 2
        for i in range(months_to_fetch):
            target = end_date.replace(day=1)
            for _ in range(i):
                if target.month == 1:
                    target = target.replace(year=target.year - 1, month=12, day=1)
                else:
                    target = target.replace(month=target.month - 1, day=1)
            date_str = target.strftime('%Y%m%d')
            url = f'https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?&date={date_str}&stockNo={code}&response=json'
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            if data.get('stat') == 'OK' and data.get('data'):
                for row in data['data']:
                    try:
                        tw_date = row[0]
                        parts = tw_date.split('/')
                        year = int(parts[0]) + 1911
                        month = parts[1].zfill(2)
                        day = parts[2].zfill(2)
                        date = f"{year}-{month}-{day}"
                        all_data.append({
                            'Date': date,
                            'Open': float(row[3].replace(',', '')),
                            'High': float(row[4].replace(',', '')),
                            'Low': float(row[5].replace(',', '')),
                            'Close': float(row[6].replace(',', '')),
                            'Volume': int(row[1].replace(',', ''))
                        })
                    except Exception:
                        continue
            import time; time.sleep(0.5)
        if all_data:
            df = pd.DataFrame(all_data)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date').reset_index(drop=True).set_index('Date')
            df = df[~df.index.duplicated(keep='last')]
            return df
        return None
    except Exception:
        return None

# ===== 技術指標 =====
def calc_ma(series, days):
    return series.rolling(window=days).mean()

def calc_rsi(series, days=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=days).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=days).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_kd(high, low, close, n=9):
    lowest_low = low.rolling(window=n).min()
    highest_high = high.rolling(window=n).max()
    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
    k = rsv.ewm(alpha=1/3).mean()
    d = k.ewm(alpha=1/3).mean()
    return k, d

# ===== 宏觀情緒判斷 =====
def get_market_mood(vix, tnxy):
    if vix is None:
        return "📊 載入中...", COLORS['neutral'], ""
    if vix > 25:
        mood, color = "⚠️ 市場恐慌", COLORS['bearish']
        suggestion = "持有現金、降低科技股曝險"
    elif vix < 15:
        mood, color = "✅ 市場穩定", COLORS['bullish']
        suggestion = "積極佈局，但留意本益比"
    else:
        mood, color = "📊 中性觀望", COLORS['neutral']
        suggestion = "區間操作，等待方向"
    if tnxy:
        if tnxy > 4.5: rate_msg = "⚠️ 升息壓力大"
        elif tnxy > 3.5: rate_msg = "📊 利率正常"
        else: rate_msg = "🔽 低利率環境"
    else:
        rate_msg = ""
    return mood, color, f"{rate_msg} | {suggestion}" if rate_msg else suggestion

# ===== 卡片元件 =====
def render_card(title, value, change=None, change_pct=None, status='neutral', icon=''):
    if status == 'bullish':
        status_color = COLORS['up']
        status_bg = '#F8514920'
        status_icon = '●'
    elif status == 'bearish':
        status_color = COLORS['down']
        status_bg = '#3FB95020'
        status_icon = '●'
    else:
        status_color = COLORS['neutral']
        status_bg = '#D2992220'
        status_icon = '●'

    change_str = ''
    if change is not None and change_pct is not None:
        arrow = '▲' if change_pct >= 0 else '▼'
        change_str = f"{arrow} {abs(change_pct):.2f}%"

    card = f"""
    <div style="background-color: {COLORS['card']}; border-radius: 12px; padding: 16px;
                border: 1px solid {COLORS['border']}; margin: 6px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: {COLORS['text_secondary']}; font-size: 0.95rem; font-weight: bold;">{icon} {title}</span>
            <span style="color: {status_color}; background: {status_bg}; font-size: 1.1rem;
                width: 24px; height: 24px; border-radius: 50%; display: inline-flex;
                align-items: center; justify-content: center; font-weight: bold;">{status_icon}</span>
        </div>
        <div style="color: {COLORS['text']}; font-size: 1.4rem; font-weight: bold; margin: 8px 0;">{value}</div>
        <div style="color: {status_color}; font-size: 0.8rem;">{change_str}</div>
    </div>
    """
    return card

# ===== 載入基本面 =====
@st.cache_data(ttl=600)
def load_fundamentals():
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'stock_fundamentals.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('stocks', {}), data.get('update_date', '未知')
    except Exception:
        return {}, '載入失敗'

FUNDAMENTALS, FUNDAMENTALS_UPDATE = load_fundamentals()

# ===== 主程式 =====
def main():
    with st.sidebar:
        st.title("📈 龍龍股票儀表板")
        st.markdown("---")

        # 股票下拉選單
        default_idx = 2
        selected_label = st.selectbox(
            "📌 選擇股票",
            STOCK_OPTIONS,
            index=default_idx,
            format_func=lambda x: x
        )
        selected_code = selected_label.split(' ')[0]
        st.session_state.selected_stock = selected_code

        st.markdown("---")

        period_map = {"1個月": "1mo", "3個月": "3mo", "6個月": "6mo", "1年": "1y"}
        period_labels = list(period_map.keys())
        selected_period_label = st.selectbox("📅 時間範圍", period_labels, index=2)
        st.session_state.period = period_map[selected_period_label]

        st.session_state.indicators = st.multiselect(
            "📊 技術指標",
            ["MA5", "MA20", "MA60", "RSI", "KD", "Volume"],
            default=["MA20", "RSI", "Volume"]
        )

        st.markdown("---")
        st.markdown("**📊 快速連結**")
        st.markdown("- [Yahoo 股市](https://tw.stock.yahoo.com/)")
        st.markdown("- [TradingView](https://www.tradingview.com/)")
        st.markdown("---")
        st.caption(f"更新時間：{datetime.now().strftime('%H:%M:%S')}")

    tab_main, tab_search = st.tabs(["🏠 主頁", "🔍 個股查詢"])

    # =============================================
    # 🏠 Tab 1：主頁
    # =============================================
    with tab_main:
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        st.title("🌐 龍龍股票儀表板")
        st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (GMT+8)")

        # 市場情緒
        st.markdown("#### 📊 龍龍市場情緒")
        vix_info = get_ticker_info('^VIX')
        tnxy_info = get_ticker_info('^TNX')

        vix = vix_info.get('regularMarketPrice') or vix_info.get('currentPrice')
        vix_change_pct = vix_info.get('regularMarketChangePercent') or 0
        tnxy = tnxy_info.get('regularMarketPrice') or tnxy_info.get('currentPrice')
        tnxy_change_pct = tnxy_info.get('regularMarketChangePercent') or 0

        mood, mood_color, suggestion = get_market_mood(vix, tnxy)
        vix_status = 'bearish' if vix and vix > 25 else 'bullish' if vix and vix < 15 else 'neutral'

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.markdown(render_card('😰 VIX 恐慌指數', f"{vix:.2f}" if vix else "N/A", '▲' if vix_change_pct > 0 else '▼', vix_change_pct, vix_status, '😰'), unsafe_allow_html=True)
        with col2:
            st.markdown(render_card('💵 10年債殖利率', f"{tnxy:.2f}%" if tnxy else "N/A", None, tnxy_change_pct, 'bearish' if tnxy and tnxy > 4.5 else 'neutral', '💵'), unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div style='background: linear-gradient(135deg, {COLORS['card']} 0%, #1a2332 100%); border-radius: 16px; padding: 20px; border: 1px solid {COLORS['border']}; height: 100%;'><h2 style='color: {mood_color}; margin: 0;'>{mood}</h2><p style='color: {COLORS['text_secondary']}; margin: 8px 0 0 0; font-size: 0.9rem;'>{suggestion}</p></div>", unsafe_allow_html=True)

        # 宏觀指標
        st.markdown("---")
        st.markdown("##### 🏦 宏觀指標")

        fed_rate, _ = get_fred_latest('FEDFUNDS')
        unemp, _ = get_fred_latest('UNRATE')
        cpi, cpi_prev = get_fred_latest('CPIAUCSL')
        gdp, gdp_prev = get_fred_latest('GDP')

        cpi_yoy = ((cpi / cpi_prev) - 1) * 100 * 12 if cpi and cpi_prev and cpi_prev > 0 else None
        gdp_growth = ((gdp / gdp_prev) - 1) * 100 if gdp and gdp_prev else None

        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1: st.markdown(render_card('Fed利率', f"{fed_rate:.2f}%" if fed_rate else "N/A", None, None, 'bearish' if fed_rate and fed_rate > 5 else 'neutral', '🏦'), unsafe_allow_html=True)
        with mc2: st.markdown(render_card('失業率', f"{unemp:.2f}%" if unemp else "N/A", None, None, 'bearish' if unemp and unemp > 5 else 'bullish', '👷'), unsafe_allow_html=True)
        with mc3: st.markdown(render_card('CPI通膨(年)', f"{cpi_yoy:.1f}%" if cpi_yoy else "N/A", None, None, 'bearish' if cpi_yoy and cpi_yoy > 3 else 'neutral', '📈'), unsafe_allow_html=True)
        with mc4: st.markdown(render_card('GDP季增率', f"{gdp_growth:.1f}%" if gdp_growth else "N/A", None, None, 'bullish' if gdp_growth and gdp_growth > 2 else 'neutral', '📊'), unsafe_allow_html=True)

        # === K線圖 ===
        code = st.session_state.selected_stock
        stock_name = STOCKS.get(code, code)
        period = st.session_state.period

        st.markdown("---")
        st.markdown(f"##### 📈 {stock_name} ({code}) K線圖")

        df = get_twse_data(code)
        if df is None or df.empty:
            df = get_yf_history(f"{code}.TW", period)

        if df is not None and not df.empty:
            try:
                if isinstance(df.index, pd.DatetimeIndex):
                    now = datetime.now()
                    days_map = {'1mo': 30, '3mo': 90, '6mo': 180, '1y': 365}
                    days_limit = days_map.get(period, 90)
                    start_date = now - pd.Timedelta(days=days_limit)
                    df = df[df.index >= start_date]
            except Exception:
                pass

            current_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2]) if len(df) > 1 else current_price
            change = current_price - prev_price
            change_pct = (change / prev_price) * 100 if prev_price != 0 else 0

            p_col1, p_col2, p_col3 = st.columns(3)
            with p_col1:
                color = COLORS['bullish'] if change >= 0 else COLORS['bearish']
                st.markdown(f"<div style='background-color: {COLORS['card']}; border-radius: 12px; padding: 16px; border: 1px solid {COLORS['border']}; text-align: center;'><div style='color: {COLORS['text_secondary']}; font-size: 0.85rem;'>目前價格</div><div style='color: {COLORS['text']}; font-size: 1.8rem; font-weight: bold;'>{current_price:.2f}</div><div style='color: {color}; font-size: 0.9rem;'>▲ {change_pct:+.2f}%</div></div>", unsafe_allow_html=True)
            with p_col2:
                st.markdown(f"<div style='background-color: {COLORS['card']}; border-radius: 12px; padding: 16px; border: 1px solid {COLORS['border']}; text-align: center;'><div style='color: {COLORS['text_secondary']}; font-size: 0.85rem;'>期間最高</div><div style='color: {COLORS['bullish']}; font-size: 1.8rem; font-weight: bold;'>{df['High'].max():.2f}</div></div>", unsafe_allow_html=True)
            with p_col3:
                st.markdown(f"<div style='background-color: {COLORS['card']}; border-radius: 12px; padding: 16px; border: 1px solid {COLORS['border']}; text-align: center;'><div style='color: {COLORS['text_secondary']}; font-size: 0.85rem;'>期間最低</div><div style='color: {COLORS['bearish']}; font-size: 1.8rem; font-weight: bold;'>{df['Low'].min():.2f}</div></div>", unsafe_allow_html=True)

            indicators = st.session_state.indicators
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.65, 0.35], subplot_titles=('', ''))

            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color=COLORS['up'], decreasing_line_color=COLORS['down']), row=1, col=1)

            close_series = df['Close']
            if "MA5" in indicators and len(df) >= 5:
                fig.add_trace(go.Scatter(x=df.index, y=calc_ma(close_series, 5), name='MA5', line=dict(color='blue', width=1)), row=1, col=1)
            if "MA20" in indicators and len(df) >= 20:
                fig.add_trace(go.Scatter(x=df.index, y=calc_ma(close_series, 20), name='MA20', line=dict(color='purple', width=2)), row=1, col=1)
            if "MA60" in indicators and len(df) >= 60:
                fig.add_trace(go.Scatter(x=df.index, y=calc_ma(close_series, 60), name='MA60', line=dict(color='orange', width=2)), row=1, col=1)

            if "RSI" in indicators and len(df) >= 14:
                rsi = calc_rsi(close_series)
                fig.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI', line=dict(color='yellow', width=2)), row=2, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)

            if "KD" in indicators and len(df) >= 9:
                k, d = calc_kd(df['High'], df['Low'], close_series)
                fig.add_trace(go.Scatter(x=df.index, y=k, name='K', line=dict(color='red', width=2)), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=d, name='D', line=dict(color='blue', width=2)), row=2, col=1)

            if "Volume" in indicators:
                colors_vol = [COLORS['bullish'] if df['Close'].iloc[i] >= df['Open'].iloc[i] else COLORS['bearish'] for i in range(len(df))]
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=colors_vol, marker=dict(opacity=0.7)), row=2, col=1)

            fig.update_layout(xaxis_rangeslider_visible=False, height=600, paper_bgcolor=COLORS['background'], plot_bgcolor=COLORS['background'], font=dict(color=COLORS['text']), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=60, r=20, t=40, b=40))
            for r in [1, 2]:
                fig.update_xaxes(gridcolor='#30363D', zerolinecolor='#30363D', showgrid=True, row=r, col=1)
                fig.update_yaxes(gridcolor='#30363D', zerolinecolor='#30363D', showgrid=True, row=r, col=1)

            # 加入 unique key 避免 DuplicateElementId
            st.plotly_chart(fig, use_container_width=True, key=f"kline_main_{code}")

            # 基本面
            st.markdown("---")
            st.markdown("##### 📉 基本面數據")
            fundamentals = FUNDAMENTALS.get(code, {})

            # 事先初始化，確保 st.metric 一定拿到有效變數
            eps_str = "N/A"
            pe_str = "N/A"
            dy_str = "N/A"
            quarter_str = "N/A"

            try:
                eps_val = fundamentals.get('EPS', 'N/A')
                if eps_val not in ('N/A', None, ''):
                    eps_str = f"{float(str(eps_val).replace('%','')):.2f}"
            except Exception:
                eps_str = "N/A"

            try:
                pe_val = fundamentals.get('本益比', 'N/A')
                if pe_val not in ('N/A', None, ''):
                    pe_str = f"{float(str(pe_val).replace('%','')):.2f}"
            except Exception:
                pe_str = "N/A"

            try:
                dy = fundamentals.get('殖利率', 'N/A')
                if dy not in (None, 'N/A', ''):
                    dy_str = f"{float(str(dy).replace('%','')):.2f}%"
            except Exception:
                dy_str = "N/A"

            try:
                quarter_str = str(fundamentals.get('財報季度', 'N/A'))
            except Exception:
                quarter_str = "N/A"

            b_col1, b_col2, b_col3, b_col4 = st.columns(4)
            with b_col1: st.metric("EPS", eps_str)
            with b_col2: st.metric("本益比 (P/E)", pe_str)
            with b_col3: st.metric("殖利率", dy_str)
            with b_col4: st.metric("財報季度", quarter_str)

            if fundamentals.get('產業'): st.markdown(f"**產業：** {fundamentals.get('產業')}")
            if fundamentals.get('備註'): st.caption(f"📅 {fundamentals.get('備註')}")
            st.caption(f"📊 資料來源：證交所 ({FUNDAMENTALS_UPDATE})")

            # 龍龍觀點
            st.markdown("##### 🐉 龍龍觀點")
            ma5_val = calc_ma(close_series, 5).iloc[-1] if len(df) >= 5 else None
            ma20_val = calc_ma(close_series, 20).iloc[-1] if len(df) >= 20 else None
            ma60_val = calc_ma(close_series, 60).iloc[-1] if len(df) >= 60 else None
            rsi_series = calc_rsi(close_series)
            rsi_val = float(rsi_series.iloc[-1]) if len(df) >= 14 else None

            opinions = []
            if ma5_val and ma20_val:
                opinions.append(("✅ MA5 > MA20 → 短線偏多", "bullish") if ma5_val > ma20_val else ("⚠️ MA5 < MA20 → 短線偏空", "bearish"))
            if ma60_val and ma20_val:
                opinions.append(("✅ MA20 > MA60 → 中線偏多", "bullish") if ma20_val > ma60_val else ("⚠️ MA20 < MA60 → 中線偏空", "bearish"))
            if rsi_val:
                if rsi_val > 70: opinions.append((f"⚠️ RSI = {rsi_val:.1f} → 超買區，小心回檔", "bearish"))
                elif rsi_val < 30: opinions.append((f"✅ RSI = {rsi_val:.1f} → 超賣區，留意反彈", "bullish"))
                else: opinions.append((f"➡️ RSI = {rsi_val:.1f} → 區間整理", "neutral"))

            bullish_cnt = sum(1 for _, s in opinions if s == 'bullish')
            bearish_cnt = sum(1 for _, s in opinions if s == 'bearish')
            if bullish_cnt > bearish_cnt: overall = ("📈 短線偏多看待", COLORS['bullish'])
            elif bearish_cnt > bullish_cnt: overall = ("📉 短線偏空看待", COLORS['bearish'])
            else: overall = ("➡️ 中性觀望", COLORS['neutral'])

            for text, status in opinions:
                st.markdown(f"<span style='color:{COLORS.get(status, COLORS['text'])}'>{text}</span>", unsafe_allow_html=True)
            st.markdown(f"**🐉 龍龍綜合判斷：<span style='color:{overall[1]}'>{overall[0]}</span>**", unsafe_allow_html=True)
        else:
            st.error(f"⚠️ 無法取得 {code} 數據")

    # =============================================
    # 🔍 Tab 2：個股查詢 → 顯示 12 檔持股報價
    # =============================================
    with tab_search:
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        st.title("🔍 持股報價")
        st.caption("即時股價資訊（資料來源：Yahoo Finance）")

        twse_codes = list(STOCKS.keys())  # 12 檔
        yf_tickers = [f"{c}.TW" for c in twse_codes]

        # 一次下載所有 YAHOO 資料
        try:
            all_yf = yf.download(yf_tickers, period='5d', interval='1d', progress=False, timeout=15)
        except Exception:
            all_yf = pd.DataFrame()

        # 4 列 x 3 排顯示（響應式）
        cols_per_row = 3
        for row_start in range(0, len(twse_codes), cols_per_row):
            row_codes = twse_codes[row_start:row_start + cols_per_row]
            row_cols = st.columns(cols_per_row)
            for idx, code in enumerate(row_codes):
                with row_cols[idx]:
                    name = STOCKS.get(code, code)
                    price = 0
                    change_pct = 0
                    try:
                        if isinstance(all_yf, pd.DataFrame) and not all_yf.empty and code in all_yf['Close'].columns:
                            close_series = all_yf['Close'][code].dropna()
                            if len(close_series) >= 1:
                                price = float(close_series.iloc[-1])
                                prev = float(close_series.iloc[-2]) if len(close_series) > 1 else price
                                change = price - prev
                                change_pct = (change / prev * 100) if prev != 0 else 0
                        else:
                            time.sleep(0.3)
                            info = get_ticker_info(f"{code}.TW")
                            price = info.get('regularMarketPrice') or 0
                            change_pct = info.get('regularMarketChangePercent', 0) or 0
                            time.sleep(0.3)  # 避免 Yahoo Finance 限流
                    except Exception:
                        price = 0
                        change_pct = 0

                    is_up = change_pct >= 0
                    color = COLORS['up'] if is_up else COLORS['down']
                    arrow = '▲' if is_up else '▼'
                    price_str = f"{price:.2f}" if price else "N/A"
                    change_str = f"{arrow} {abs(change_pct):.2f}%" if price else "N/A"

                    st.markdown(f"""
                    <div style="background-color: {COLORS['card']}; border-radius: 12px; padding: 16px;
                                border: 1px solid {COLORS['border']}; margin: 4px; text-align: center;">
                        <div style="color: {COLORS['text']}; font-size: 1.1rem; font-weight: bold; margin-bottom: 4px;">{code}</div>
                        <div style="color: {COLORS['text_secondary']}; font-size: 0.8rem; margin-bottom: 8px;">{name}</div>
                        <div style="color: {COLORS['text']}; font-size: 1.6rem; font-weight: bold; margin-bottom: 4px;">{price_str}</div>
                        <div style="color: {color}; font-size: 0.9rem;">{change_str}</div>
                    </div>
                    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
