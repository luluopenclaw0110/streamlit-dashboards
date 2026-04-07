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

# ===== 配色系統 =====
# 台股格式：上漲(紅)、下跌(綠)
COLORS = {
    'background': '#0D1117',
    'card': '#161B22',
    'up': '#F85149',      # 台股上漲：紅
    'down': '#3FB950',    # 台股下跌：綠
    'bullish': '#F85149', # 別名（台股上漲）
    'bearish': '#3FB950', # 別名（台股下跌）
    'neutral': '#D29922',
    'text': '#E6EDF3',
    'text_secondary': '#8B949E',
    'border': '#30363D',
}

# 頁面設定
st.set_page_config(
    page_title="少爺的股票儀表板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=dict()
)

# 深色主題 CSS
st.markdown("""
<style>
.stApp, .main, body { background-color: #0D1117 !important; }
[data-testid="stHorizontalBlock"], [data-testid="stVerticalBlock"],
.css-1d391kg, .css-12wkwq4, .css-1at1ahb, .element-container { background-color: #161B22 !important; }
[data-testid="stSidebar"] { background-color: #161B22 !important; }
.stMarkdown, h1, h2, h3, h4, p, span, label { color: #E6EDF3 !important; }
/* 主標題與頁面邊緣保持距離 */
[data-testid="stMainBlockContainer"] { padding-top: 2rem !important; padding-bottom: 8rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
/* 每個 section 標題不要切齊邊緣 */
.stMarkdown h3, .stMarkdown h4 { margin-left: 0.5rem !important; margin-right: 0.5rem !important; }
/* 側邊欄與主體之間留白 */
.css-1lcbmhc.e1fqkh3o3 { padding-left: 1rem; }
div[data-testid="stMetricValue"] { color: #E6EDF3 !important; font-size: 1.8rem; }
div[data-testid="stMetricLabel"] { color: #8B949E !important; }
[data-testid="stDataFrame"] { background-color: #161B22 !important; }
.st-d6, .st-d7, .st-cj, .st-d4, .css-2trqyj { background-color: transparent !important; }
.stSelectbox > div > div, .stMultiSelect > div > div { background-color: #0D1117 !important; color: #E6EDF3 !important; }
header[data-testid="stHeader"] { background-color: #0D1117 !important; }
/* 技術指標選單：tag 右側留空間避免與 x 按鈕重疊 */
.stMultiSelect [data-testid="stMultiSelect"] > div > div > div { flex-wrap: wrap; gap: 4px; }
/* 每個 stMarkdown 標題卡片給左右留白 */
.element-container { margin-left: 4px; margin-right: 4px; }
</style>
""", unsafe_allow_html=True)

# ===== Session State 初始化 =====
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
    '2317': '鴻海', '2330': '台積電', '2887': '台新新光金', '3532': '台勝科',
    '4716': '大立', '5543': '均豪', '6613': '朋億', '6667': '信紘科'
}
US_STOCKS = ['NVDA', 'QQQ', 'TSM']

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
        # Handle FRED error response
        if 'error_code' in data:
            return None, None
        if 'observations' in data and len(data['observations']) >= 2:
            obs = data['observations']
            # Find two non-null values
            non_null = [float(o['value']) for o in obs if o['value'] not in ('', 'None', '.', None) and o['value'] is not None]
            if len(non_null) >= 2:
                return non_null[0], non_null[1]
            elif len(non_null) == 1:
                return non_null[0], None
        return None, None
    except Exception as e:
        return None, None

# ===== Yahoo Finance =====
@st.cache_data(ttl=60)
def get_ticker_info(ticker):
    """使用 Ticker().info 並加入 fallback 到 download()"""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if info and (info.get('regularMarketPrice') or info.get('currentPrice')):
            return info
    except Exception:
        pass
    # Fallback: 用 yf.download 取得報價
    try:
        df = yf.download(ticker, period='5d', interval='1d', progress=False, timeout=10)
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
    return {}

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
            return df.sort_values('Date').reset_index(drop=True).set_index('Date')
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
        if tnxy > 4.5:
            rate_msg = "⚠️ 升息壓力大"
        elif tnxy > 3.5:
            rate_msg = "📊 利率正常"
        else:
            rate_msg = "🔽 低利率環境"
    else:
        rate_msg = ""

    return mood, color, f"{rate_msg} | {suggestion}" if rate_msg else suggestion

# ===== 卡片元件 =====
def render_card(title, value, change=None, change_pct=None, status='neutral', icon=''):
    # 燈號大小：根據狀態顯示不同尺寸的圓圈燈
    if status == 'bullish':
        status_color = COLORS['up']    # 台股上漲：紅
        status_bg = '#F8514920'        # 淡淡的紅色背景
        status_icon = '●'
    elif status == 'bearish':
        status_color = COLORS['down']  # 台股下跌：綠
        status_bg = '#3FB95020'        # 淡淡的綠色背景
        status_icon = '●'
    else:
        status_color = COLORS['neutral']
        status_bg = '#D2992220'
        status_icon = '●'

    change_str = ''
    if change is not None and change_pct is not None:
        arrow = '▲' if change >= 0 else '▼'
        change_str = f"{arrow} {abs(change_pct):.2f}%"

    card = f"""
    <div style="background-color: {COLORS['card']}; border-radius: 12px; padding: 16px;
                border: 1px solid {COLORS['border']}; margin: 6px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: {COLORS['text_secondary']}; font-size: 0.95rem; font-weight: bold;">{icon} {title}</span>
            <span style="
                color: {status_color};
                background: {status_bg};
                font-size: 1.1rem;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                ">{status_icon}</span>
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
    # === 側邊欄：股票選擇器 ===
    with st.sidebar:
        st.title("📈 股票儀表板")
        st.markdown("---")

        # 股票選擇
        stock_options = [f"{code} {name}" for code, name in STOCKS.items()]
        selected = st.selectbox(
            "📌 選擇股票",
            stock_options,
            index=stock_options.index('2330 台積電') if '2330 台積電' in stock_options else 0
        )
        st.session_state.selected_stock = selected.split(' ')[0]

        # 時間範圍
        period_map = {"1個月": "1mo", "3個月": "3mo", "6個月": "6mo", "1年": "1y"}
        period_labels = list(period_map.keys())
        default_period_idx = 2  # 6個月
        selected_period_label = st.selectbox("📅 時間範圍", period_labels, index=default_period_idx)
        st.session_state.period = period_map[selected_period_label]

        # 技術指標
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

    # === 主頁 Header ===
    st.title(f"🌐 少爺的股票儀表板")
    st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (GMT+8)")

    # === 第一區塊：市場情緒 Banner ===
    st.markdown("#### 📊 龍龍市場情緒")
    vix_info = get_ticker_info('^VIX')
    tnxy_info = get_ticker_info('^TNX')

    vix = vix_info.get('regularMarketPrice') or vix_info.get('currentPrice')
    vix_change = vix_info.get('regularMarketChange') or 0
    vix_change_pct = vix_info.get('regularMarketChangePercent') or 0

    tnxy = tnxy_info.get('regularMarketPrice') or tnxy_info.get('currentPrice')
    tnxy_change_pct = tnxy_info.get('regularMarketChangePercent') or 0

    mood, mood_color, suggestion = get_market_mood(vix, tnxy)

    vix_status = 'bearish' if vix and vix > 25 else 'bullish' if vix and vix < 15 else 'neutral'
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        vix_val = f"{vix:.2f}" if vix else "N/A"
        vix_arrow = '▲' if vix_change_pct and vix_change_pct > 0 else '▼'
        st.markdown(render_card('😰 VIX 恐慌指數', vix_val, vix_arrow, vix_change_pct, vix_status, '😰'), unsafe_allow_html=True)
    with col2:
        tnxy_val = f"{tnxy:.2f}%" if tnxy else "N/A"
        tnxy_status = 'bearish' if tnxy and tnxy > 4.5 else 'neutral'
        st.markdown(render_card('💵 10年債殖利率', tnxy_val, None, tnxy_change_pct, tnxy_status, '💵'), unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {COLORS['card']} 0%, #1a2332 100%);
                    border-radius: 16px; padding: 20px; border: 1px solid {COLORS['border']}; height: 100%;">
            <h2 style="color: {mood_color}; margin: 0;">{mood}</h2>
            <p style="color: {COLORS['text_secondary']}; margin: 8px 0 0 0; font-size: 0.9rem;">{suggestion}</p>
        </div>
        """, unsafe_allow_html=True)

    # === 第二區塊：宏觀指標 + 8檔股票（左右佈局）===
    st.markdown("---")

    # Fed 利率、失業率、CPI 用快取
    fed_rate, fed_prev = get_fred_latest('FEDFUNDS')
    unemp, unemp_prev = get_fred_latest('UNRATE')
    cpi, cpi_prev = get_fred_latest('CPIAUCSL')
    gdp, gdp_prev = get_fred_latest('GDP')

    cpi_yoy = None
    if cpi and cpi_prev and cpi_prev > 0:
        cpi_yoy = ((cpi / cpi_prev) - 1) * 100 * 12

    gdp_growth = None
    if gdp and gdp_prev:
        gdp_growth = ((gdp / gdp_prev) - 1) * 100

    left_col, right_col = st.columns([1, 2.5])

    with left_col:
        st.markdown("##### 🏦 宏觀指標")
        mc1, mc2 = st.columns(2)
        with mc1:
            status = 'bearish' if fed_rate and fed_rate > 5 else 'neutral'
            val = f"{fed_rate:.2f}%" if fed_rate else "N/A"
            prev_str = f"{fed_prev:.2f}%" if fed_prev else "N/A"
            st.markdown(render_card('Fed利率', val, None, None, status, '🏦'), unsafe_allow_html=True)
        with mc2:
            status = 'bearish' if unemp and unemp > 5 else 'bullish'
            val = f"{unemp:.2f}%" if unemp else "N/A"
            st.markdown(render_card('失業率', val, None, None, status, '👷'), unsafe_allow_html=True)

        mc3, mc4 = st.columns(2)
        with mc3:
            status = 'bearish' if cpi_yoy and cpi_yoy > 3 else 'neutral'
            val = f"{cpi_yoy:.1f}%" if cpi_yoy else "N/A"
            st.markdown(render_card('CPI通膨(年)', val, None, None, status, '📈'), unsafe_allow_html=True)
        with mc4:
            status = 'bullish' if gdp_growth and gdp_growth > 2 else 'neutral'
            val = f"{gdp_growth:.1f}%" if gdp_growth else "N/A"
            st.markdown(render_card('GDP季增率', val, None, None, status, '📊'), unsafe_allow_html=True)

    with right_col:
        st.markdown("##### 💰 龍龍的12檔股票")
        # 一次取得所有報價
        stock_rows = []
        for code, name in STOCKS.items():
            info = get_ticker_info(f"{code}.TW")
            price = info.get('regularMarketPrice') or info.get('currentPrice')
            change = info.get('regularMarketChange') or 0
            change_pct = info.get('regularMarketChangePercent') or 0
            if price:
                stock_rows.append({
                    '代號': code, '名稱': name,
                    '價格': f"{price:.2f}",
                    '漲跌': f"{change:+.2f}",
                    '漲跌幅': f"{change_pct:+.2f}%",
                    'is_up': change >= 0
                })

        if stock_rows:
            cols = st.columns(4)
            for i, row in enumerate(stock_rows):
                color = COLORS['bullish'] if row['is_up'] else COLORS['bearish']
                arrow = '▲' if row['is_up'] else '▼'
                with cols[i % 4]:
                    st.markdown(f"""
                    <div style="background-color: {COLORS['card']}; border-radius: 10px; padding: 12px;
                                border: 1px solid {COLORS['border']}; text-align: center; margin: 4px; min-height: 100px;
                                display: flex; flex-direction: column; justify-content: space-between;">
                        <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem;">{row['代號']} {row['名稱']}</div>
                        <div style="color: {COLORS['text']}; font-size: 1.2rem; font-weight: bold; margin: 4px 0;">{row['價格']}</div>
                        <div style="color: {color}; font-size: 0.85rem;">{arrow} {row['漲跌幅']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # === 第三區塊：K線圖 + 技術指標 ===
    st.markdown("---")
    st.markdown(f"##### 📈 {STOCKS.get(st.session_state.selected_stock, st.session_state.selected_stock)} K線圖")

    code = st.session_state.selected_stock
    period = st.session_state.period

    # 嘗試 TWSE，若失敗用 yfinance
    df = get_twse_data(code)
    if df is None or df.empty:
        df = get_yf_history(f"{code}.TW", period)

    if df is not None and not df.empty:
        # 過濾日期範圍
        try:
            if 'Date' in df.columns or df.index.name == 'Date':
                pass
            elif isinstance(df.index, pd.DatetimeIndex):
                now = datetime.now()
                if period == '1mo':
                    start_date = now - pd.Timedelta(days=30)
                elif period == '3mo':
                    start_date = now - pd.Timedelta(days=90)
                elif period == '6mo':
                    start_date = now - pd.Timedelta(days=180)
                elif period == '1y':
                    start_date = now - pd.Timedelta(days=365)
                else:
                    start_date = now - pd.Timedelta(days=90)
                df = df[df.index >= start_date]
        except Exception:
            pass

        current_price = float(df['Close'].iloc[-1])
        prev_price = float(df['Close'].iloc[-2]) if len(df) > 1 else current_price
        change = current_price - prev_price
        change_pct = (change / prev_price) * 100 if prev_price != 0 else 0

        # 價格 summary
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            color = COLORS['bullish'] if change >= 0 else COLORS['bearish']
            st.markdown(f"""
            <div style="background-color: {COLORS['card']}; border-radius: 12px; padding: 16px; border: 1px solid {COLORS['border']}; text-align: center;">
                <div style="color: {COLORS['text_secondary']}; font-size: 0.85rem;">目前價格</div>
                <div style="color: {COLORS['text']}; font-size: 1.8rem; font-weight: bold;">{current_price:.2f}</div>
                <div style="color: {color}; font-size: 0.9rem;">▲ {change_pct:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with p_col2:
            high = df['High'].max()
            st.markdown(f"""
            <div style="background-color: {COLORS['card']}; border-radius: 12px; padding: 16px; border: 1px solid {COLORS['border']}; text-align: center;">
                <div style="color: {COLORS['text_secondary']}; font-size: 0.85rem;">期間最高</div>
                <div style="color: {COLORS['bullish']}; font-size: 1.8rem; font-weight: bold;">{high:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with p_col3:
            low = df['Low'].min()
            st.markdown(f"""
            <div style="background-color: {COLORS['card']}; border-radius: 12px; padding: 16px; border: 1px solid {COLORS['border']}; text-align: center;">
                <div style="color: {COLORS['text_secondary']}; font-size: 0.85rem;">期間最低</div>
                <div style="color: {COLORS['bearish']}; font-size: 1.8rem; font-weight: bold;">{low:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        # === K線圖 ===
        indicators = st.session_state.indicators

        if len(df) > 0:
            fig = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.65, 0.35],
                subplot_titles=('', '')
            )

            # K線 - 台股格式：上漲紅，下跌綠
            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'],
                    name='K線', increasing_line_color=COLORS['up'],
                    decreasing_line_color=COLORS['down']
                ),
                row=1, col=1
            )

            # MA 線
            close_series = df['Close']
            if "MA5" in indicators and len(df) >= 5:
                fig.add_trace(go.Scatter(x=df.index, y=calc_ma(close_series, 5), name='MA5',
                                          line=dict(color='blue', width=1)), row=1, col=1)
            if "MA20" in indicators and len(df) >= 20:
                fig.add_trace(go.Scatter(x=df.index, y=calc_ma(close_series, 20), name='MA20',
                                          line=dict(color='purple', width=2)), row=1, col=1)
            if "MA60" in indicators and len(df) >= 60:
                fig.add_trace(go.Scatter(x=df.index, y=calc_ma(close_series, 60), name='MA60',
                                          line=dict(color='orange', width=2)), row=1, col=1)

            # RSI
            if "RSI" in indicators and len(df) >= 14:
                rsi = calc_rsi(close_series)
                fig.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI',
                                          line=dict(color='yellow', width=2)), row=2, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)

            # KD
            if "KD" in indicators and len(df) >= 9:
                k, d = calc_kd(df['High'], df['Low'], close_series)
                fig.add_trace(go.Scatter(x=df.index, y=k, name='K',
                                          line=dict(color='red', width=2)), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=d, name='D',
                                          line=dict(color='blue', width=2)), row=2, col=1)

            # 成交量
            if "Volume" in indicators:
                colors_vol = [COLORS['bullish'] if df['Close'].iloc[i] >= df['Open'].iloc[i]
                              else COLORS['bearish'] for i in range(len(df))]
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量',
                                      marker_color=colors_vol, marker=dict(opacity=0.7)), row=2, col=1)

            fig.update_layout(
                xaxis_rangeslider_visible=False,
                height=600,
                paper_bgcolor=COLORS['background'],
                plot_bgcolor=COLORS['background'],
                font=dict(color=COLORS['text']),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=60, r=20, t=40, b=40)
            )
            fig.update_xaxes(gridcolor='#30363D', zerolinecolor='#30363D', showgrid=True, row=1, col=1)
            fig.update_xaxes(gridcolor='#30363D', zerolinecolor='#30363D', showgrid=True, row=2, col=1)
            fig.update_yaxes(gridcolor='#30363D', zerolinecolor='#30363D', showgrid=True, row=1, col=1)
            fig.update_yaxes(gridcolor='#30363D', zerolinecolor='#30363D', showgrid=True, row=2, col=1)

            st.plotly_chart(fig, use_container_width=True)

            # === 第四區塊：基本面 + 龍龍觀點 ===
            st.markdown("---")
            st.markdown("##### 📉 基本面數據")

            fundamentals = FUNDAMENTALS.get(code, {})
            eps = fundamentals.get('EPS')
            pe = fundamentals.get('本益比')
            div_yield = fundamentals.get('殖利率')
            div = fundamentals.get('股息')
            bv = fundamentals.get('每股淨值')
            sector = fundamentals.get('產業')
            quarter = fundamentals.get('財報季度', 'N/A')
            note = fundamentals.get('備註', '')

            b_col1, b_col2, b_col3, b_col4 = st.columns(4)
            with b_col1:
                eps_str = f"{float(eps):.2f}" if eps not in (None, 'N/A', '') else "N/A"
                try: eps_str = f"{float(str(eps).replace('%','')):.2f}"
                except: pass
                st.metric("EPS", eps_str, help="每股盈餘")
            with b_col2:
                pe_str = f"{float(pe):.2f}" if pe not in (None, 'N/A', '') else "N/A"
                try: pe_str = f"{float(str(pe).replace('%','')):.2f}"
                except: pass
                st.metric("本益比 (P/E)", pe_str, help="股價盈餘比")
            with b_col3:
                try:
                    if div_yield not in (None, 'N/A', ''):
                        dy_val = float(str(div_yield).replace('%',''))
                        dy_str = f"{dy_val:.2f}%"
                    else:
                        dy_str = "N/A"
                except:
                    dy_str = "N/A"
                st.metric("殖利率", dy_str, help="股息殖利率")
            with b_col4:
                st.metric("財報季度", str(quarter), help="最新財報季度")

            if sector:
                st.markdown(f"**產業：** {sector}")
            if note:
                st.caption(f"📅 {note}")
            st.caption(f"📊 資料來源：證交所 ({FUNDAMENTALS_UPDATE})")

            # === 龍龍觀點 ===
            st.markdown("##### 🐉 龍龍觀點")

            ma5_val = calc_ma(close_series, 5).iloc[-1] if len(df) >= 5 else None
            ma20_val = calc_ma(close_series, 20).iloc[-1] if len(df) >= 20 else None
            ma60_val = calc_ma(close_series, 60).iloc[-1] if len(df) >= 60 else None
            rsi_val = calc_rsi(close_series).iloc[-1] if len(df) >= 14 else None

            opinions = []

            # 均線觀點
            if ma5_val and ma20_val:
                if ma5_val > ma20_val:
                    opinions.append(("✅ MA5 > MA20 → 短線偏多", "bullish"))
                else:
                    opinions.append(("⚠️ MA5 < MA20 → 短線偏空", "bearish"))

            if ma60_val and ma20_val:
                if ma20_val > ma60_val:
                    opinions.append(("✅ MA20 > MA60 → 中線偏多", "bullish"))
                else:
                    opinions.append(("⚠️ MA20 < MA60 → 中線偏空", "bearish"))

            # RSI 觀點
            if rsi_val:
                if rsi_val > 70:
                    opinions.append((f"⚠️ RSI = {rsi_val:.1f} → 超買區，小心回檔", "bearish"))
                elif rsi_val < 30:
                    opinions.append((f"✅ RSI = {rsi_val:.1f} → 超賣區，留意反彈", "bullish"))
                else:
                    opinions.append((f"➡️ RSI = {rsi_val:.1f} → 區間整理", "neutral"))

            # 綜合建議
            bullish_count = sum(1 for _, s in opinions if s == 'bullish')
            bearish_count = sum(1 for _, s in opinions if s == 'bearish')
            neutral_count = sum(1 for _, s in opinions if s == 'neutral')

            if bullish_count > bearish_count:
                overall = ("📈 短線偏多看待", COLORS['bullish'])
            elif bearish_count > bullish_count:
                overall = ("📉 短線偏空看待", COLORS['bearish'])
            else:
                overall = ("➡️ 中性觀望", COLORS['neutral'])

            for text, status in opinions:
                color = COLORS.get(status, COLORS['text'])
                st.markdown(f"<span style='color:{color}'>{text}</span>", unsafe_allow_html=True)

            st.markdown(f"**🐉 龍龍綜合判斷：<span style='color:{overall[1]}'>{overall[0]}</span>**",
                       unsafe_allow_html=True)

    else:
        st.error("⚠️ 無法取得股票數據，請稍後再試或更換股票")

    # === 第五區塊：美股表現 ===
    st.markdown("---")
    st.markdown("##### 🇺🇸 美股昨晚表現")

    us_cols = st.columns(len(US_STOCKS))
    for i, ticker in enumerate(US_STOCKS):
        with us_cols[i]:
            info = get_ticker_info(ticker)
            price = info.get('regularMarketPrice') or info.get('currentPrice')
            change = info.get('regularMarketChange') or 0
            change_pct = info.get('regularMarketChangePercent') or 0

            if price:
                name = {'NVDA': 'NVIDIA', 'QQQ': 'QQQ納指', 'TSM': 'TSM台積電'}.get(ticker, ticker)
                color = COLORS['bullish'] if change >= 0 else COLORS['bearish']
                arrow = '▲' if change >= 0 else '▼'

                st.markdown(f"""
                <div style="background-color: {COLORS['card']}; border-radius: 12px; padding: 16px;
                            border: 1px solid {COLORS['border']}; text-align: center;">
                    <div style="color: {COLORS['text_secondary']}; font-size: 0.8rem;">{ticker} {name}</div>
                    <div style="color: {COLORS['text']}; font-size: 1.4rem; font-weight: bold; margin: 6px 0;">{price:.2f}</div>
                    <div style="color: {color}; font-size: 0.9rem;">{arrow} {change_pct:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: {COLORS['card']}; border-radius: 12px; padding: 16px;
                            border: 1px solid {COLORS['border']}; text-align: center;">
                    <div style="color: {COLORS['text_secondary']}; font-size: 0.8rem;">{ticker}</div>
                    <div style="color: {COLORS['text']}; font-size: 1.2rem; margin: 6px 0;">N/A</div>
                </div>
                """, unsafe_allow_html=True)

    # === 頁腳 ===
    st.markdown("---")
    st.markdown(f"*📊 資料更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 本報告僅供參考，不構成投資建議*")

if __name__ == "__main__":
    main()
