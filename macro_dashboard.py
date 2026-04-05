#!/usr/bin/env python3
"""
🌐 宏觀經濟儀表板 - 少爺專用
使用方式: streamlit run macro_dashboard.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time

# ===== 配色系統 =====
COLORS = {
    'background': '#0D1117',
    'card': '#161B22',
    'bullish': '#3FB950',     # 多頭 🟢
    'neutral': '#D29922',     # 中性 🟡
    'bearish': '#F85149',     # 空頭 🔴
    'text': '#E6EDF3',
    'text_secondary': '#8B949E',
}

# 頁面設定
st.set_page_config(
    page_title="🌐 宏觀經濟儀表板",
    page_icon="🌐",
    layout="wide"
)

# 自訂 CSS
st.markdown("""
<style>
.stApp { background-color: #0D1117; }
.css-1d391kg { background-color: #161B22; }
div[data-testid="stMetricValue"] { color: #E6EDF3; font-size: 1.8rem; }
div[data-testid="stMetricLabel"] { color: #8B949E; }
.st-dx { background-color: #161B22; }
.element-container { background-color: #161B22; }
</style>
""", unsafe_allow_html=True)

# ===== FRED API =====
FRED_API_KEY = 'edaa5b7562ebd132c42effa0193e5772'

@st.cache_data(ttl=3600)
def get_fred_data(series_id, name, months=12):
    """從 FRED API 取得宏觀數據"""
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
    """取得 FRED 最新值"""
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
    """取得市場數據"""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period)
        return df
    except:
        return None

def get_ticker_price_change(ticker):
    """取得股價和變化"""
    try:
        t = yf.Ticker(ticker)
        price = t.info.get('regularMarketPrice') or t.info.get('currentPrice')
        change = t.info.get('regularMarketChange') or t.info.get('change')
        change_pct = t.info.get('regularMarketChangePercent') or 0
        return price, change, change_pct
    except:
        return None, None, None

# ===== 卡片元件 =====
def render_card(title, latest_val, prev_val, unit='', status='neutral', bar_width=0.7):
    """渲染宏觀指標卡片"""
    
    # 計算變化
    if latest_val is not None and prev_val is not None:
        change = latest_val - prev_val
        change_pct = (change / prev_val * 100) if prev_val != 0 else 0
    else:
        change = None
        change_pct = None
    
    # 根據狀態選擇顏色
    if status == 'bullish':
        status_color = COLORS['bullish']
        arrow = '▲'
    elif status == 'bearish':
        status_color = COLORS['bearish']
        arrow = '▼'
    else:
        status_color = COLORS['neutral']
        arrow = '◆'
    
    # 格式化顯示值
    if latest_val is not None:
        if unit == '%':
            val_str = f"{latest_val:.2f}{unit}"
        elif unit == 'B':
            val_str = f"${latest_val/1e9:.2f}T" if latest_val >= 1e9 else f"${latest_val/1e6:.0f}M"
        else:
            val_str = f"{latest_val:.2f}{unit}"
    else:
        val_str = 'N/A'
    
    if prev_val is not None:
        if unit == '%':
            prev_str = f"{prev_val:.2f}{unit}"
        elif unit == 'B':
            prev_str = f"${prev_val/1e9:.2f}T" if prev_val >= 1e9 else f"${prev_val/1e6:.0f}M"
        else:
            prev_str = f"{prev_val:.2f}{unit}"
    else:
        prev_str = 'N/A'
    
    # 變化字串
    if change is not None and change_pct is not None:
        change_str = f"{arrow} {abs(change_pct):.2f}%"
    else:
        change_str = ''
    
    # HTML 卡片
    card_html = f"""
    <div style="
        background-color: {COLORS['card']};
        border-radius: 12px;
        padding: 16px;
        margin: 8px;
        border: 1px solid #30363D;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="color: {COLORS['text_secondary']}; font-size: 0.85rem;">{title}</span>
            <span style="color: {status_color}; font-size: 1.2rem;">●</span>
        </div>
        <div style="color: {COLORS['text']}; font-size: 1.5rem; font-weight: bold; margin-bottom: 8px;">
            {val_str}
        </div>
        <div style="
            background-color: #0D1117;
            border-radius: 4px;
            height: 6px;
            width: {bar_width*100}%;
            margin-bottom: 12px;
        ">
            <div style="
                background-color: {status_color};
                border-radius: 4px;
                height: 100%;
                width: 100%;
            "></div>
        </div>
        <div style="display: flex; justify-content: space-between; color: {COLORS['text_secondary']}; font-size: 0.8rem;">
            <span>前值: {prev_str}</span>
            <span style="color: {status_color};">{change_str}</span>
        </div>
    </div>
    """
    return card_html

# ===== 主程式 =====
def main():
    st.title("🌐 宏觀經濟儀表板")
    st.markdown("---")
    
    # ===== 第一排：五大央行/巨觀指標 =====
    st.markdown("### 📊 核心巨觀指標")
    
    # Fed 利率
    fed_rate, fed_prev = get_fred_latest('FEDFUNDS')
    
    # 失業率
    unemp_rate, unemp_prev = get_fred_latest('UNRATE')
    
    # CPI 通膨
    cpi, cpi_prev = get_fred_latest('CPIAUCSL')
    if cpi is not None and cpi_prev is not None:
        cpi_yoy = ((cpi / cpi_prev) - 1) * 100 * 12 if cpi_prev > 0 else 0  # 年化
        cpi_yoy_prev = ((cpi_prev / (cpi_prev * 0.99)) - 1) * 100 * 12 if cpi_prev > 0 else 0
    else:
        cpi_yoy = None
        cpi_yoy_prev = None
    
    # GDP
    gdp, gdp_prev = get_fred_latest('GDP')
    
    # 10年債殖利率
    tnxy, tnxy_prev = get_ticker_price_change('^TNX')
    
    # 顯示五個卡片
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        status = 'bearish' if fed_rate and fed_rate > 5 else 'neutral'
        st.markdown(render_card('🏦 Fed利率', fed_rate, fed_prev, '%', status), unsafe_allow_html=True)
    
    with col2:
        status = 'bearish' if unemp_rate and unemp_rate > 5 else 'bullish'
        st.markdown(render_card('👷 失業率', unemp_rate, unemp_prev, '%', status), unsafe_allow_html=True)
    
    with col3:
        status = 'bearish' if cpi_yoy and cpi_yoy > 3 else 'neutral'
        st.markdown(render_card('📈 CPI通膨(年)', cpi_yoy, cpi_yoy_prev, '%', status), unsafe_allow_html=True)
    
    with col4:
        gdp_growth = ((gdp / gdp_prev) - 1) * 100 if gdp and gdp_prev else None
        gdp_growth_prev = None
        status = 'bullish' if gdp_growth and gdp_growth > 2 else 'neutral'
        st.markdown(render_card('📊 GDP季增率', gdp_growth, gdp_growth_prev, '%', status), unsafe_allow_html=True)
    
    with col5:
        status = 'bearish' if tnxy and tnxy > 4.5 else 'neutral'
        st.markdown(render_card('💵 10年債殖利率', tnxy, tnxy_prev, '%', status), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== 第二排：市場情緒 =====
    st.markdown("### 😰 市場情緒 & 資金流向")
    
    # VIX
    vix_price, vix_change, vix_change_pct = get_ticker_price_change('^VIX')
    
    # S&P 500
    sp_price, sp_change, sp_change_pct = get_ticker_price_change('^GSPC')
    
    # Nasdaq
    nasdaq_price, nasdaq_change, nasdaq_change_pct = get_ticker_price_change('^IXIC')
    
    # 美元指數
    dxy_price, dxy_change, dxy_change_pct = get_ticker_price_change('DX-Y.NYB')
    
    # 黃金
    gold_price, gold_change, gold_change_pct = get_ticker_price_change('GC=F')
    
    # BTC
    btc_price, btc_change, btc_change_pct = get_ticker_price_change('BTC-USD')
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        status = 'bearish' if vix_price and vix_price > 25 else 'bullish' if vix_price and vix_price < 15 else 'neutral'
        st.markdown(render_card('😰 VIX恐慌', vix_price, None, '', status, 0.3), unsafe_allow_html=True)
    
    with col2:
        st.markdown(render_card('📈 S&P 500', sp_price, None, '', 'neutral', 0.8), unsafe_allow_html=True)
    
    with col3:
        st.markdown(render_card('🔷 Nasdaq', nasdaq_price, None, '', 'neutral', 0.8), unsafe_allow_html=True)
    
    with col4:
        status = 'bullish' if dxy_price and dxy_price > 105 else 'bearish' if dxy_price and dxy_price < 100 else 'neutral'
        st.markdown(render_card('💵 美元指數', dxy_price, None, '', status), unsafe_allow_html=True)
    
    with col5:
        status = 'bullish' if gold_change and gold_change > 0 else 'bearish'
        st.markdown(render_card('🥇 黃金', gold_price, None, '', status), unsafe_allow_html=True)
    
    with col6:
        status = 'bullish' if btc_change and btc_change > 0 else 'bearish'
        st.markdown(render_card('₿ BTC', btc_price, None, '', status), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== 第三排：信用市場 & AI科技 =====
    st.markdown("### 💳 信用市場 & 🤖 AI科技股")
    
    # HY credit spreads
    hy_spread, hy_prev = get_fred_latest('BAMLEMBISPREAD')
    
    # IG credit spreads
    ig_spread, ig_prev = get_fred_latest('BAMLEASPPISAC')
    
    # HY企業債
    hy_ticker = yf.Ticker('HYG')
    try:
        hy_price = hy_ticker.info.get('regularMarketPrice') or hy_ticker.info.get('currentPrice')
        hy_change = hy_ticker.info.get('regularMarketChange')
    except:
        hy_price = None
        hy_change = None
    
    # IG企業債
    ig_ticker = yf.Ticker('LQD')
    try:
        ig_price = ig_ticker.info.get('regularMarketPrice') or ig_ticker.info.get('currentPrice')
        ig_change = ig_ticker.info.get('regularMarketChange')
    except:
        ig_price = None
        ig_change = None
    
    # NVDA
    nvda_price, nvda_change, nvda_change_pct = get_ticker_price_change('NVDA')
    
    # TSM
    tsm_price, tsm_change, tsm_change_pct = get_ticker_price_change('TSM')
    
    # QQQ
    qqq_price, qqq_change, qqq_change_pct = get_ticker_price_change('QQQ')
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        status = 'bearish' if hy_spread and hy_spread > 500 else 'bullish' if hy_spread and hy_spread < 300 else 'neutral'
        st.markdown(render_card('💳 HY利差(bp)', hy_spread, hy_prev, '', status), unsafe_allow_html=True)
    
    with col2:
        status = 'bearish' if ig_spread and ig_spread > 150 else 'bullish' if ig_spread and ig_spread < 100 else 'neutral'
        st.markdown(render_card('💳 IG利差(bp)', ig_spread, ig_prev, '', status), unsafe_allow_html=True)
    
    with col3:
        st.markdown(render_card('📈 HYG HY債', hy_price, None, '', 'neutral'), unsafe_allow_html=True)
    
    with col4:
        st.markdown(render_card('📈 LQD IG債', ig_price, None, '', 'neutral'), unsafe_allow_html=True)
    
    with col5:
        status = 'bullish' if nvda_change and nvda_change > 0 else 'bearish'
        st.markdown(render_card('🤖 NVDA', nvda_price, None, '', status), unsafe_allow_html=True)
    
    with col6:
        status = 'bullish' if tsm_change and tsm_change > 0 else 'bearish'
        st.markdown(render_card('⚡ TSM 台積電', tsm_price, None, '', status), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== 綜合趨勢圖 =====
    st.markdown("### 📊 綜合趨勢圖")
    
    # 圖表類型選擇
    chart_type = st.selectbox(
        "選擇圖表類型",
        ["S&P 500", "VIX", "10年債殖利率", "美元指數", "GDP vs 通膨", "失業率 vs 薪資"],
        label_visibility="collapsed"
    )
    
    # 建立圖表
    fig = go.Figure()
    
    if chart_type == "S&P 500":
        df = get_market_data('^GSPC', '3mo')
        if df is not None and len(df) > 0:
            fig.add_trace(go.Scatter(
                x=df.index, 
                y=df['Close'], 
                name='S&P 500',
                line=dict(color=COLORS['bullish'], width=2)
            ))
            fig.update_layout(
                title="S&P 500 走勢",
                template="plotly_dark",
                paper_bgcolor=COLORS['card'],
                plot_bgcolor=COLORS['card'],
                height=400
            )
    
    elif chart_type == "VIX":
        df = get_market_data('^VIX', '1mo')
        if df is not None and len(df) > 0:
            fig.add_trace(go.Scatter(
                x=df.index, 
                y=df['Close'], 
                name='VIX',
                line=dict(color=COLORS['bearish'], width=2)
            ))
            fig.update_layout(
                title="VIX 恐慌指數",
                template="plotly_dark",
                paper_bgcolor=COLORS['card'],
                plot_bgcolor=COLORS['card'],
                height=400
            )
    
    elif chart_type == "10年債殖利率":
        df = get_market_data('^TNX', '3mo')
        if df is not None and len(df) > 0:
            fig.add_trace(go.Scatter(
                x=df.index, 
                y=df['Close'], 
                name='10年債殖利率',
                line=dict(color=COLORS['neutral'], width=2)
            ))
            fig.update_layout(
                title="10年債殖利率 (%)",
                template="plotly_dark",
                paper_bgcolor=COLORS['card'],
                plot_bgcolor=COLORS['card'],
                height=400
            )
    
    elif chart_type == "美元指數":
        df = get_market_data('DX-Y.NYB', '3mo')
        if df is not None and len(df) > 0:
            fig.add_trace(go.Scatter(
                x=df.index, 
                y=df['Close'], 
                name='美元指數',
                line=dict(color='#58A6FF', width=2)
            ))
            fig.update_layout(
                title="美元指數 (DXY)",
                template="plotly_dark",
                paper_bgcolor=COLORS['card'],
                plot_bgcolor=COLORS['card'],
                height=400
            )
    
    elif chart_type == "GDP vs 通膨":
        gdp_df = get_fred_data('GDP', 'GDP')
        cpi_df = get_fred_data('CPIAUCSL', 'CPI')
        
        if gdp_df is not None and len(gdp_df) > 0:
            fig.add_trace(go.Scatter(
                x=gdp_df['date'], 
                y=gdp_df['GDP'], 
                name='GDP',
                line=dict(color=COLORS['bullish'], width=2),
                yaxis='y1'
            ))
        
        if cpi_df is not None and len(cpi_df) > 0:
            # CPI 標準化
            cpi_norm = (cpi_df['CPI'] / cpi_df['CPI'].iloc[0] - 1) * 100 * (gdp_df['GDP'].iloc[-1] / gdp_df['GDP'].iloc[0] - 1) if len(gdp_df) > 0 else None
            fig.add_trace(go.Scatter(
                x=cpi_df['date'], 
                y=cpi_df['CPI'], 
                name='CPI',
                line=dict(color=COLORS['bearish'], width=2),
                yaxis='y2'
            ))
        
        fig.update_layout(
            title="GDP vs CPI (歷史走勢)",
            template="plotly_dark",
            paper_bgcolor=COLORS['card'],
            plot_bgcolor=COLORS['card'],
            height=400,
            yaxis=dict(title="GDP", titlefont=dict(color=COLORS['bullish'])),
            yaxis2=dict(title="CPI", titlefont=dict(color=COLORS['bearish']), overlaying='y', side='right')
        )
    
    elif chart_type == "失業率 vs 薪資":
        unemp_df = get_fred_data('UNRATE', '失業率', 24)
        wages_df = get_fred_data('CEU0500000003', '每週薪資', 24)
        
        if unemp_df is not None and len(unemp_df) > 0:
            fig.add_trace(go.Scatter(
                x=unemp_df['date'], 
                y=unemp_df['失業率'], 
                name='失業率 %',
                line=dict(color=COLORS['bearish'], width=2),
                yaxis='y1'
            ))
        
        if wages_df is not None and len(wages_df) > 0:
            fig.add_trace(go.Scatter(
                x=wages_df['date'], 
                y=wages_df['每週薪資'], 
                name='每週薪資 $',
                line=dict(color=COLORS['bullish'], width=2),
                yaxis='y2'
            ))
        
        fig.update_layout(
            title="失業率 vs 薪資成長",
            template="plotly_dark",
            paper_bgcolor=COLORS['card'],
            plot_bgcolor=COLORS['card'],
            height=400,
            yaxis=dict(title="失業率 %", titlefont=dict(color=COLORS['bearish'])),
            yaxis2=dict(title="薪資 $", titlefont=dict(color=COLORS['bullish']), overlaying='y', side='right')
        )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ===== 情境判断 Banner =====
    st.markdown("---")
    
    # 簡單判斷情境
    if vix_price:
        if vix_price > 25:
            mood = "⚠️ 市場恐慌"
            mood_color = COLORS['bearish']
            suggestion = "持有現金、降低科技股曝險"
        elif vix_price < 15:
            mood = "✅ 市場穩定"
            mood_color = COLORS['bullish']
            suggestion = "積極佈局，但留意本益比"
        else:
            mood = "📊 中性觀望"
            mood_color = COLORS['neutral']
            suggestion = "區間操作，等待方向"
    else:
        mood = "📊 載入中..."
        mood_color = COLORS['neutral']
        suggestion = ""
    
    if tnxy:
        if tnxy > 4.5:
            rate_msg = "⚠️ 升息壓力大"
            rate_color = COLORS['bearish']
        elif tnxy > 3.5:
            rate_msg = "📊 利率正常"
            rate_color = COLORS['neutral']
        else:
            rate_msg = "🔽 低利率環境"
            rate_color = COLORS['bullish']
    else:
        rate_msg = ""
        rate_color = COLORS['neutral']
    
    # Banner
    banner_html = f"""
    <div style="
        background: linear-gradient(135deg, {COLORS['card']} 0%, #1a2332 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        border: 1px solid #30363D;
        text-align: center;
    ">
        <h2 style="color: {mood_color}; margin-bottom: 8px;">{mood}</h2>
        <p style="color: {COLORS['text_secondary']}; font-size: 1rem;">
            利率環境: <span style="color: {rate_color};">{rate_msg}</span>
            &nbsp;|&nbsp;
            建議: <span style="color: {COLORS['text']};">{suggestion}</span>
        </p>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)
    
    # ===== 頁腳 =====
    st.markdown("---")
    st.markdown(f"*📊 資料更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    st.markdown("*本報告僅供參考，不構成投資建議*")

if __name__ == '__main__':
    main()
