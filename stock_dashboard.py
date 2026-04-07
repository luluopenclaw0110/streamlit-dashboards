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
/* ===== 問題1：修復 selectbox/multiselect 背景透明 ===== */
.stSelectbox > div > div, .stMultiSelect > div > div { background-color: #2d333b !important; color: #E6EDF3 !important; border: 1px solid #444c56 !important; border-radius: 6px !important; }
.stSelectbox [data-baseweb="select"], .stMultiSelect [data-baseweb="select"] { background-color: #2d333b !important; }
[data-baseweb="popover"], [data-baseweb="menu"] { background-color: #2d333b !important; border: 1px solid #444c56 !important; border-radius: 6px !important; }
[data-baseweb="option"] { background-color: #2d333b !important; color: #E6EDF3 !important; }
[data-baseweb="option"]:hover { background-color: #444c56 !important; }
[data-baseweb="tag"] { background-color: #388bfd !important; color: #ffffff !important; }
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
def get_fred_latest(series_id, limit=14):
    """取得 FRED 最新觀測值（limit 預設14確保有12個月前的CPI資料）"""
    try:
        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'limit': limit,
            'sort_order': 'desc'
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if 'error_code' in data:
            return None, None
        if 'observations' in data:
            obs = data['observations']
            # 收集所有非 null 值（FRED 用 "." 表示缺失值）
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
    if len(series) < days:
        return pd.Series([None] * len(series), index=series.index)
    return series.rolling(window=days).mean()

def calc_rsi(series, days=14):
    if len(series) < days + 1:
        return pd.Series([None] * len(series), index=series.index)
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=days).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=days).mean()
    # 避免除以零
    loss = loss.replace(0, 0.0001)
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_kd(high, low, close, n=9):
    if len(high) < n:
        k = pd.Series([None] * len(high), index=high.index)
        d = pd.Series([None] * len(high), index=high.index)
        return k, d
    lowest_low = low.rolling(window=n).min()
    highest_high = high.rolling(window=n).max()
    # 避免除以零
    denominator = highest_high - lowest_low
    denominator = denominator.replace(0, 0.0001)
    rsv = (close - lowest_low) / denominator * 100
    k = rsv.ewm(alpha=1/3).mean()
    d = k.ewm(alpha=1/3).mean()
    return k, d

def calc_macd(series, fast=12, slow=26, signal=9):
    """計算 MACD"""
    if len(series) < slow:
        return pd.Series([None] * len(series), index=series.index), \
               pd.Series([None] * len(series), index=series.index), \
               pd.Series([None] * len(series), index=series.index)
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

# ===== 宏觀情緒判斷 =====
def get_market_mood(vix, tnxy):
    if vix is None:
        return "📊 載入中...", COLORS['neutral'], ""
    if vix > 25:
        mood, color = "⚠️ 市場恐慌", COLORS['up']
        suggestion = "持有現金、降低科技股曝險"
    elif vix < 15:
        mood, color = "✅ 市場情緒穩定", COLORS['down']
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

# ===== 統一投資建議 =====
def get_unified_recommendation(ma5_val, ma20_val, ma60_val, rsi_val, current_price, pe_ratio=20, roe=15, profit_growth=0):
    """
    統一的投資建議函數，整合技術面與基本面
    返回: (建議文字, 顏色關鍵字, 分數, 信號列表)
    """
    score = 0
    signals = []

    # --- 技術面分析 (權重 60%) ---
    if ma5_val and ma20_val:
        if ma5_val > ma20_val:
            score += 2
            signals.append("MA5 > MA20 短線偏多")
        else:
            score -= 2
            signals.append("MA5 < MA20 短線偏空")

    if ma60_val and ma20_val:
        if ma20_val > ma60_val:
            score += 2
            signals.append("MA20 > MA60 中線偏多")
        else:
            score -= 2
            signals.append("MA20 < MA60 中線偏空")

    if rsi_val:
        if rsi_val > 70:
            score -= 2
            signals.append(f"RSI 超買({rsi_val:.1f})")
        elif rsi_val < 30:
            score += 2
            signals.append(f"RSI 超賣({rsi_val:.1f})")
        else:
            signals.append(f"RSI 中性({rsi_val:.1f})")

    # --- 基本面分析 (權重 40%) ---
    if roe > 20:
        score += 2
        signals.append(f"ROE 優秀({roe:.1f}%)")
    elif roe > 10:
        score += 1
        signals.append(f"ROE 良好({roe:.1f}%)")

    if profit_growth > 20:
        score += 2
        signals.append(f"獲利成長佳({profit_growth:+.1f}%)")
    elif profit_growth > 0:
        score += 1
        signals.append(f"獲利正成長({profit_growth:+.1f}%)")
    elif profit_growth < -20:
        score -= 2
        signals.append(f"獲利衰退({profit_growth:+.1f}%)")

    if 10 < pe_ratio < 25:
        score += 1
        signals.append(f"本益比合理({pe_ratio:.1f})")
    elif pe_ratio > 40:
        score -= 1
        signals.append(f"本益比偏高({pe_ratio:.1f})")

    # 統一判斷標準
    if score >= 4:
        return "💚 建議買入", "green", score, signals
    elif score >= 1:
        return "💙 持續觀察", "blue", score, signals
    elif score <= -4:
        return "❤️ 建議賣出", "red", score, signals
    else:
        return "➡️ 中性觀望", "neutral", score, signals

def get_recommendation(roe, profit_growth, pe_ratio):
    """產業分析專用：僅基本面判斷（保持向後相容）"""
    score = 0
    if roe > 20: score += 2
    elif roe > 10: score += 1
    if profit_growth > 20: score += 2
    elif profit_growth > 0: score += 1
    elif profit_growth < -20: score -= 2
    if 10 < pe_ratio < 25: score += 1
    elif pe_ratio > 40: score -= 1
    if score >= 3: return "💚 建議買入", "green"
    elif score >= 1: return "💙 持續觀察", "blue"
    else: return "❤️ 建議觀望", "red"

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

        # 技術指標（加入「全選」選項在 multiselect 裡）
        ALL_INDICATORS = ["MA5", "MA20", "MA60", "RSI", "KD", "MACD", "Volume"]
        indicators_options = ["全選"] + ALL_INDICATORS

        def on_indicator_change():
            """全選按鈕 callback：選「全選」= 全選，再點「全選」= 全取消"""
            current = st.session_state.indicators
            if "全選" in current:
                # 選了全選 → 顯示所有指標（但 UI 不要重複顯示「全選」在標籤列）
                st.session_state.indicators = ALL_INDICATORS
            elif current:
                # 有選但沒選全選 → 正常
                pass
            else:
                # 全取消
                st.session_state.indicators = []

        selected = st.multiselect(
            "📊 技術指標",
            indicators_options,
            default=st.session_state.indicators if st.session_state.indicators else ALL_INDICATORS,
            key="indicators",
            on_change=on_indicator_change
        )

        st.markdown("---")
        st.markdown("**📊 快速連結**")
        st.markdown("- [Yahoo 股市](https://tw.stock.yahoo.com/)")
        st.markdown("- [TradingView](https://www.tradingview.com/)")
        st.markdown("---")
        st.caption(f"更新時間：{datetime.now().strftime('%H:%M:%S')}")

    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
    tab_main, tab_search, tab_industry = st.tabs(["🏠 主頁", "🔍 個股查詢", "🏭 產業分析"])

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
        vix_status = 'bullish' if vix and vix > 25 else 'bearish' if vix and vix < 15 else 'neutral'

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

        fed_rate, _ = get_fred_latest('FEDFUNDS', limit=2)
        unemp, _ = get_fred_latest('UNRATE', limit=2)
        # CPI: 取14筆，確保有12個月前的資料（用於年增率計算）
        cpi_obs = get_fred_latest('CPIAUCSL', limit=14)
        gdp, gdp_prev = get_fred_latest('GDP', limit=2)

        # CPI 年增率：當期 / 12個月前 - 1
        if cpi_obs[0] and cpi_obs[1]:
            cpi_yoy = ((cpi_obs[0] / cpi_obs[1]) - 1) * 100 if cpi_obs[1] > 0 else None
        else:
            cpi_yoy = None
        gdp_growth = ((gdp / gdp_prev) - 1) * 100 if gdp and gdp_prev and gdp_prev > 0 else None

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
            
            # 根據選擇的指標動態調整 subplot 行數
            num_rows = 2  # 基礎: K線(1) + 指標(1)
            if "MACD" in indicators:
                num_rows = 3  # K線(1) + RSI/KD(1) + MACD(1)
            
            row_heights = [0.55] + [0.45 / (num_rows - 1)] * (num_rows - 1)
            fig = make_subplots(
                rows=num_rows, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.06, 
                row_heights=row_heights,
                subplot_titles=([''] * num_rows)
            )

            # === Row 1: K線蠟燭圖 + MA 均線 ===
            fig.add_trace(go.Candlestick(
                x=df.index, 
                open=df['Open'], 
                high=df['High'], 
                low=df['Low'], 
                close=df['Close'], 
                name='K線', 
                increasing_line_color=COLORS['up'], 
                decreasing_line_color=COLORS['down'],
                increasing_fillcolor=COLORS['up'],
                decreasing_fillcolor=COLORS['down']
            ), row=1, col=1)

            close_series = df['Close']
            if "MA5" in indicators and len(df) >= 5:
                ma5 = calc_ma(close_series, 5)
                fig.add_trace(go.Scatter(x=df.index, y=ma5, name='MA5', line=dict(color='#FFD700', width=1.5), legendgroup='ma'), row=1, col=1)
            if "MA20" in indicators and len(df) >= 20:
                ma20 = calc_ma(close_series, 20)
                fig.add_trace(go.Scatter(x=df.index, y=ma20, name='MA20', line=dict(color='#9B59B6', width=2), legendgroup='ma'), row=1, col=1)
            if "MA60" in indicators and len(df) >= 60:
                ma60 = calc_ma(close_series, 60)
                fig.add_trace(go.Scatter(x=df.index, y=ma60, name='MA60', line=dict(color='#FF6B35', width=2), legendgroup='ma'), row=1, col=1)

            # === Row 2: RSI / KD 指標 ===
            if ("RSI" in indicators or "KD" in indicators) and len(df) >= max(14 if "RSI" in indicators else 0, 9 if "KD" in indicators else 0):
                if "RSI" in indicators and len(df) >= 14:
                    rsi = calc_rsi(close_series)
                    rsi_values = rsi.dropna()
                    if not rsi_values.empty:
                        fig.add_trace(go.Scatter(
                            x=rsi_values.index, 
                            y=rsi_values.values, 
                            name='RSI', 
                            line=dict(color='#F1C40F', width=2),
                            legendgroup='rsi'
                        ), row=2, col=1)
                        fig.add_hline(y=70, line_dash="dash", line_color="#E74C3C", line_width=1, row=2, col=1)
                        fig.add_hline(y=30, line_dash="dash", line_color="#27AE60", line_width=1, row=2, col=1)
                        fig.add_hline(y=50, line_dash="dot", line_color="#7F8C8D", line_width=1, row=2, col=1)

                if "KD" in indicators and len(df) >= 9:
                    k, d = calc_kd(df['High'], df['Low'], close_series)
                    k_valid = k.dropna()
                    d_valid = d.dropna()
                    if not k_valid.empty:
                        fig.add_trace(go.Scatter(x=k_valid.index, y=k_valid.values, name='K', line=dict(color='#E74C3C', width=2), legendgroup='kd'), row=2, col=1)
                        fig.add_trace(go.Scatter(x=d_valid.index, y=d_valid.values, name='D', line=dict(color='#3498DB', width=2), legendgroup='kd'), row=2, col=1)

            # === Row 3: MACD 指標 (新增) ===
            if "MACD" in indicators and len(df) >= 26:
                macd_line, signal_line, histogram = calc_macd(close_series)
                macd_valid = macd_line.dropna()
                signal_valid = signal_line.dropna()
                hist_valid = histogram.dropna()
                
                if not macd_valid.empty:
                    # MACD 柱狀圖 (紅色=負，綠色=正)
                    bar_colors = ['#27AE60' if v >= 0 else '#E74C3C' for v in hist_valid.values]
                    fig.add_trace(go.Bar(
                        x=hist_valid.index, 
                        y=hist_valid.values, 
                        name='MACD Hist', 
                        marker_color=bar_colors,
                        marker=dict(opacity=0.6),
                        legendgroup='macd'
                    ), row=3, col=1)
                    fig.add_trace(go.Scatter(
                        x=macd_valid.index, 
                        y=macd_valid.values, 
                        name='DIF', 
                        line=dict(color='#3498DB', width=2),
                        legendgroup='macd'
                    ), row=3, col=1)
                    fig.add_trace(go.Scatter(
                        x=signal_valid.index, 
                        y=signal_valid.values, 
                        name='MACD', 
                        line=dict(color='#E74C3C', width=2),
                        legendgroup='macd'
                    ), row=3, col=1)

            # === 成交量 (放在最後一個 row) ===
            if "Volume" in indicators:
                colors_vol = [COLORS['bullish'] if df['Close'].iloc[i] >= df['Open'].iloc[i] else COLORS['bearish'] for i in range(len(df))]
                fig.add_trace(go.Bar(
                    x=df.index, 
                    y=df['Volume'], 
                    name='成交量', 
                    marker_color=colors_vol, 
                    marker=dict(opacity=0.5),
                    legendgroup='vol'
                ), row=num_rows, col=1)

            # 統一更新所有 axes（問題3：Y軸字體調大）
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                height=200 + (num_rows * 180),
                paper_bgcolor=COLORS['background'],
                plot_bgcolor=COLORS['background'],
                font=dict(color=COLORS['text'], size=14),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=60, r=20, t=40, b=40)
            )

            for r in range(1, num_rows + 1):
                fig.update_xaxes(gridcolor='#30363D', zerolinecolor='#30363D', showgrid=True, row=r, col=1, tickfont=dict(size=13, color=COLORS['text']))
                fig.update_yaxes(gridcolor='#30363D', zerolinecolor='#30363D', showgrid=True, row=r, col=1, tickfont=dict(size=13, color=COLORS['text']))

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

            # 龍龍觀點（問題4：使用統一的投資建議邏輯）
            st.markdown("##### 🐉 龍龍觀點")
            ma5_val = calc_ma(close_series, 5).iloc[-1] if len(df) >= 5 else None
            ma20_val = calc_ma(close_series, 20).iloc[-1] if len(df) >= 20 else None
            ma60_val = calc_ma(close_series, 60).iloc[-1] if len(df) >= 60 else None
            rsi_series = calc_rsi(close_series)
            rsi_val = float(rsi_series.iloc[-1]) if len(df) >= 14 else None

            # 取得基本面數據用於統一判斷
            fund = FUNDAMENTALS.get(code, {})
            pe_val = 20
            roe_val = 15
            try:
                pe_str = fund.get('本益比', '20')
                if pe_str not in ('N/A', None, ''):
                    pe_val = float(str(pe_str).replace('%', ''))
            except:
                pe_val = 20
            try:
                roe_str = fund.get('ROE', '15')
                if roe_str not in ('N/A', None, ''):
                    roe_val = float(str(roe_str).replace('%', ''))
            except:
                roe_val = 15

            # 使用統一建議函數
            recommendation, rec_color, score, signals = get_unified_recommendation(
                ma5_val, ma20_val, ma60_val, rsi_val,
                current_price, pe_val, roe_val, 0
            )

            # 顯示各項技術信號
            opinions = []
            if ma5_val and ma20_val:
                opinions.append(("✅ MA5 > MA20 → 短線偏多", "bullish") if ma5_val > ma20_val else ("⚠️ MA5 < MA20 → 短線偏空", "bearish"))
            if ma60_val and ma20_val:
                opinions.append(("✅ MA20 > MA60 → 中線偏多", "bullish") if ma20_val > ma60_val else ("⚠️ MA20 < MA60 → 中線偏空", "bearish"))
            if rsi_val:
                if rsi_val > 70: opinions.append((f"⚠️ RSI = {rsi_val:.1f} → 超買區，小心回檔", "bearish"))
                elif rsi_val < 30: opinions.append((f"✅ RSI = {rsi_val:.1f} → 超賣區，留意反彈", "bullish"))
                else: opinions.append((f"➡️ RSI = {rsi_val:.1f} → 區間整理", "neutral"))

            for text, status in opinions:
                st.markdown(f"<span style='color:{COLORS.get(status, COLORS['text'])}'>{text}</span>", unsafe_allow_html=True)

            # 顯示統一的投資建議（與產業分析一致的邏輯）
            color_map = {'green': COLORS['bullish'], 'blue': COLORS['neutral'], 'red': COLORS['bearish'], 'neutral': COLORS['neutral']}
            final_color = color_map.get(rec_color, COLORS['neutral'])
            st.markdown(f"**🐉 龍龍綜合判斷：<span style='color:{final_color}'>{recommendation}</span>** (技術分數: {score:+d})", unsafe_allow_html=True)
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
                            # Fallback: 個別股票查詢（N/A 股票專用）
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

    # =============================================
    # 🏭 Tab 3：產業分析（含布林通道 + 趨勢圖）
    # =============================================
    with tab_industry:
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        st.title("🏭 產業龍頭專業分析")
        st.caption("四大產業龍頭 - 專業技術分析 + 基本面 + 買賣建議")

        # 四大產業完整清單
        INDUSTRY_ALL = {
            '半導體': {'2330': '台積電', '2454': '聯發科', '3034': '聯詠'},
            '電子組裝': {'2317': '鴻海', '2382': '廣達', '2308': '台達電'},
            '傳產-鋼鐵': {'2002': '中鋼', '2027': '燁輝', '2105': '正新'},
            '傳產-塑化': {'1326': '台化', '1303': '南亞', '1301': '台塑'},
        }

        # 產業選擇器
        selected_industry = st.selectbox("選擇產業", list(INDUSTRY_ALL.keys()))
        industry_stocks = INDUSTRY_ALL[selected_industry]

        # 取得基本面數據（快取）
        @st.cache_data(ttl=3600)
        def get_industry_fundamental(code):
            try:
                t = yf.Ticker(f"{code}.TW")
                info = t.info
                return {
                    '股價': info.get('currentPrice') or info.get('regularMarketPrice') or 0,
                    '本益比': info.get('trailingPE') or 0,
                    '殖利率': (info.get('dividendYield') or 0) * 100,
                    'EPS': info.get('trailingEps') or 0,
                    'ROE': (info.get('returnOnEquity') or 0) * 100,
                    '營收': info.get('totalRevenue') or 0,
                    '淨利': info.get('netIncome') or 0,
                    '營收成長': (info.get('revenueGrowth') or 0) * 100,
                    '獲利成長': (info.get('earningsGrowth') or 0) * 100,
                }
            except Exception:
                return None

        # 顯示產業營收排名
        st.markdown("### 📊 產業營收排名")
        ranking_data = []
        for code, name in industry_stocks.items():
            data = get_industry_fundamental(code)
            if data:
                ranking_data.append({
                    '代號': code, '名稱': name,
                    '營收(B)': round(data['營收'] / 1e9, 1) if data['營收'] else 0,
                    '淨利(B)': round(data['淨利'] / 1e9, 2) if data['淨利'] else 0,
                    'EPS': f"${data['EPS']:.2f}" if data['EPS'] else 'N/A',
                    'ROE': f"{data['ROE']:.1f}%",
                    '本益比': f"{data['本益比']:.1f}" if data['本益比'] else 'N/A',
                })

        if ranking_data:
            df_rank = pd.DataFrame(ranking_data)
            df_rank = df_rank.sort_values('營收(B)', ascending=False)
            # 產業排名：根據營收客觀排名（不是投資建議）
            rank_map = {1: '🥇 第1名', 2: '🥈 第2名', 3: '🥉 第3名'}
            for rank, (idx, _) in enumerate(df_rank.iterrows(), 1):
                df_rank.loc[idx, '建議'] = rank_map.get(rank, f'第{rank}名')
            st.dataframe(df_rank, hide_index=True, use_container_width=True)

        st.markdown("---")

        # 選擇要分析的股票
        analysis_stock = st.selectbox(
            "選擇股票進行專業分析",
            list(industry_stocks.items()),
            format_func=lambda x: f"{x[1]} ({x[0]})"
        )

        # 取得 K 線歷史
        df_ind = get_yf_history(f"{analysis_stock[0]}.TW", "3mo")
        fundamental_ind = get_industry_fundamental(analysis_stock[0])

        if df_ind is not None and not df_ind.empty and len(df_ind) > 0:
            # 基本面資訊
            st.markdown("### 📈 基本面資料")
            if fundamental_ind:
                f = fundamental_ind
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("股價", f"${f['股價']:,.2f}" if f['股價'] else "N/A")
                with c2: st.metric("本益比", f"{f['本益比']:.1f}" if f['本益比'] else "N/A")
                with c3: st.metric("ROE", f"{f['ROE']:.1f}%" if f['ROE'] else "N/A")
                with c4:
                    rec, _ = get_recommendation(f['ROE'], f['獲利成長'], f['本益比'])
                    st.markdown(f"**{rec}**")
                c5, c6, c7, c8 = st.columns(4)
                with c5: st.metric("EPS", f"${f['EPS']:.2f}" if f['EPS'] else "N/A")
                with c6: st.metric("殖利率", f"{f['殖利率']:.2f}%" if f['殖利率'] else "N/A")
                with c7: st.metric("營收成長", f"{f['營收成長']:+.1f}%" if f['營收成長'] else "N/A")
                with c8: st.metric("獲利成長", f"{f['獲利成長']:+.1f}%" if f['獲利成長'] else "N/A")

            st.markdown("---")

            # === K線圖 + MA + 布林通道 ===
            st.markdown("### 📊 K線圖 + MA + 布林通道")

            candle = go.Candlestick(
                x=df_ind.index, open=df_ind['Open'], high=df_ind['High'],
                low=df_ind['Low'], close=df_ind['Close'],
                name='K線',
                increasing_line_color=COLORS['up'], decreasing_line_color=COLORS['down'],
                increasing_fillcolor=COLORS['up'], decreasing_fillcolor=COLORS['down']
            )
            fig_ind = go.Figure(data=[candle])

            close_series = df_ind['Close']

            # MA 均線
            if len(df_ind) >= 5:
                ma5 = calc_ma(close_series, 5)
                fig_ind.add_trace(go.Scatter(x=df_ind.index, y=ma5, name='MA5', line=dict(color='#FFD700', width=1.5), legendgroup='ma'))
            if len(df_ind) >= 20:
                ma20 = calc_ma(close_series, 20)
                fig_ind.add_trace(go.Scatter(x=df_ind.index, y=ma20, name='MA20', line=dict(color='#9B59B6', width=2), legendgroup='ma'))
            if len(df_ind) >= 60:
                ma60 = calc_ma(close_series, 60)
                fig_ind.add_trace(go.Scatter(x=df_ind.index, y=ma60, name='MA60', line=dict(color='#FF6B35', width=2), legendgroup='ma'))

            # 布林通道
            if len(df_ind) >= 20:
                boll_ma = calc_ma(close_series, 20)
                boll_std = close_series.rolling(window=20).std()
                boll_upper = boll_ma + 2 * boll_std
                boll_lower = boll_ma - 2 * boll_std
                fig_ind.add_trace(go.Scatter(x=df_ind.index, y=boll_upper, name='布林上軌', line=dict(color='gray', width=1, dash='dash'), legendgroup='boll'))
                fig_ind.add_trace(go.Scatter(x=df_ind.index, y=boll_lower, name='布林下軌', line=dict(color='gray', width=1, dash='dash'), legendgroup='boll'))

            fig_ind.update_layout(
                xaxis_rangeslider_visible=False, height=450,
                paper_bgcolor=COLORS['background'], plot_bgcolor=COLORS['background'],
                font=dict(color=COLORS['text'], size=14), showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=60, r=20, t=40, b=40)
            )
            fig_ind.update_xaxes(gridcolor='#30363D', zerolinecolor='#30363D', tickfont=dict(size=13, color=COLORS['text']))
            fig_ind.update_yaxes(gridcolor='#30363D', zerolinecolor='#30363D', tickfont=dict(size=13, color=COLORS['text']))
            st.plotly_chart(fig_ind, use_container_width=True, key=f"industry_kline_{analysis_stock[0]}")

            # RSI + KD
            col_rsi, col_kd = st.columns(2)
            with col_rsi:
                st.markdown("#### RSI 指標")
                if len(df_ind) >= 14:
                    rsi_ind = calc_rsi(close_series)
                    rsi_valid = rsi_ind.dropna()
                    if not rsi_valid.empty:
                        fig_rsi = go.Figure()
                        fig_rsi.add_trace(go.Scatter(x=rsi_valid.index, y=rsi_valid.values, name='RSI', line=dict(color='#F1C40F', width=2)))
                        fig_rsi.add_hline(y=70, line_dash="dash", line_color="#E74C3C", line_width=1)
                        fig_rsi.add_hline(y=30, line_dash="dash", line_color="#27AE60", line_width=1)
                        fig_rsi.add_hline(y=50, line_dash="dot", line_color="#7F8C8D", line_width=1)
                        fig_rsi.update_layout(
                            height=300, template="plotly_dark",
                            paper_bgcolor=COLORS['background'], plot_bgcolor=COLORS['background'],
                            font=dict(color=COLORS['text'], size=14),
                            margin=dict(l=60, r=20, t=40, b=40),
                            yaxis_range=[0, 100]
                        )
                        fig_rsi.update_xaxes(tickfont=dict(size=13, color=COLORS['text']))
                        fig_rsi.update_yaxes(tickfont=dict(size=13, color=COLORS['text']))
                        st.plotly_chart(fig_rsi, use_container_width=True, key=f"industry_rsi_{analysis_stock[0]}")
            with col_kd:
                st.markdown("#### KD 指標")
                if len(df_ind) >= 9:
                    k_ind, d_ind = calc_kd(df_ind['High'], df_ind['Low'], close_series)
                    k_valid = k_ind.dropna()
                    d_valid = d_ind.dropna()
                    if not k_valid.empty:
                        fig_kd = go.Figure()
                        fig_kd.add_trace(go.Scatter(x=k_valid.index, y=k_valid.values, name='K', line=dict(color='#E74C3C', width=2)))
                        fig_kd.add_trace(go.Scatter(x=d_valid.index, y=d_valid.values, name='D', line=dict(color='#3498DB', width=2)))
                        fig_kd.update_layout(
                            height=300, template="plotly_dark",
                            paper_bgcolor=COLORS['background'], plot_bgcolor=COLORS['background'],
                            font=dict(color=COLORS['text'], size=14),
                            margin=dict(l=60, r=20, t=40, b=40)
                        )
                        fig_kd.update_xaxes(tickfont=dict(size=13, color=COLORS['text']))
                        fig_kd.update_yaxes(tickfont=dict(size=13, color=COLORS['text']))
                        st.plotly_chart(fig_kd, use_container_width=True, key=f"industry_kd_{analysis_stock[0]}")

            # MACD
            st.markdown("#### MACD 指標")
            if len(df_ind) >= 26:
                macd_line, signal_line, histogram = calc_macd(close_series)
                macd_valid = macd_line.dropna()
                signal_valid = signal_line.dropna()
                hist_valid = histogram.dropna()
                if not macd_valid.empty:
                    bar_colors = ['#27AE60' if v >= 0 else '#E74C3C' for v in hist_valid.values]
                    fig_macd = go.Figure()
                    fig_macd.add_trace(go.Bar(x=hist_valid.index, y=hist_valid.values, name='柱狀', marker_color=bar_colors, marker=dict(opacity=0.6)))
                    fig_macd.add_trace(go.Scatter(x=macd_valid.index, y=macd_valid.values, name='DIF', line=dict(color='#3498DB', width=2)))
                    fig_macd.add_trace(go.Scatter(x=signal_valid.index, y=signal_valid.values, name='MACD', line=dict(color='#E74C3C', width=2)))
                    fig_macd.update_layout(
                        height=300, template="plotly_dark",
                        paper_bgcolor=COLORS['background'], plot_bgcolor=COLORS['background'],
                        font=dict(color=COLORS['text'], size=14),
                        margin=dict(l=60, r=20, t=40, b=40)
                    )
                    fig_macd.update_xaxes(tickfont=dict(size=13, color=COLORS['text']))
                    fig_macd.update_yaxes(tickfont=dict(size=13, color=COLORS['text']))
                    st.plotly_chart(fig_macd, use_container_width=True, key=f"industry_macd_{analysis_stock[0]}")

            # 成交量
            st.markdown("#### 成交量")
            colors_vol = [COLORS['up'] if df_ind['Close'].iloc[i] >= df_ind['Open'].iloc[i] else COLORS['down'] for i in range(len(df_ind))]
            fig_vol_ind = go.Figure(data=[go.Bar(x=df_ind.index, y=df_ind['Volume'], name='成交量', marker_color=colors_vol, marker=dict(opacity=0.5))])
            fig_vol_ind.update_layout(
                height=250, template="plotly_dark",
                paper_bgcolor=COLORS['background'], plot_bgcolor=COLORS['background'],
                font=dict(color=COLORS['text'], size=14),
                margin=dict(l=60, r=20, t=40, b=40)
            )
            fig_vol_ind.update_xaxes(tickfont=dict(size=13, color=COLORS['text']))
            fig_vol_ind.update_yaxes(tickfont=dict(size=13, color=COLORS['text']))
            st.plotly_chart(fig_vol_ind, use_container_width=True, key=f"industry_vol_{analysis_stock[0]}")
        else:
            st.error(f"⚠️ 無法取得 {analysis_stock[1]} 股價資料")

        st.caption(f"🕐 資料更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
