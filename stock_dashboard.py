#!/usr/bin/env python3
"""
少爺專用 - 專業財經儀表板
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

# 頁面設定
st.set_page_config(
    page_title="少爺的股票儀表板",
    page_icon="📈",
    layout="wide"
)

# 少爺的8檔股票
STOCKS = {
    '2330': '台積電',
    '2317': '鴻海', 
    '3532': '台勝科',
    '1503': '士電',
    '2887': '台新新光金',
    '1605': '華新',
    '1717': '長興',
    '1802': '台玻'
}

# 美股
US_STOCKS = {
    'NVDA': 'NVIDIA',
    'TSLA': 'Tesla',
    'AAPL': 'Apple',
    'MSFT': 'Microsoft',
    'GOOGL': 'Google',
    'META': 'Meta',
    'AMZN': 'Amazon'
}

# ===== 台灣證交所 API =====
@st.cache_data
def get_twse_data(code, days=90):
    """從台灣證交所取得股票數據"""
    try:
        from datetime import datetime, timedelta
        import time
        
        all_data = []
        end_date = datetime.now()
        
        # 分多次請求來獲取多天數據
        for i in range(0, days, 30):
            date_str = end_date.strftime('%Y%m%d')
            url = f'https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?&date={date_str}&stockNo={code}&response=json'
            
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            
            if data.get('stat') == 'OK' and data.get('data'):
                for row in data['data']:
                    try:
                        # 解析民國年日期
                        tw_date = row[0]  # 115/03/17
                        year = int(tw_date.split('/')[0]) + 1911
                        month = tw_date.split('/')[1]
                        day = tw_date.split('/')[2]
                        date = f"{year}-{month}-{day}"
                        
                        # 解析價格（移除逗號）
                        open_price = float(row[3].replace(',', ''))
                        high = float(row[4].replace(',', ''))
                        low = float(row[5].replace(',', ''))
                        close = float(row[6].replace(',', ''))
                        
                        all_data.append({
                            'Date': date,
                            'Open': open_price,
                            'High': high,
                            'Low': low,
                            'Close': close,
                            'Volume': int(row[1].replace(',', ''))
                        })
                    except:
                        continue
            
            time.sleep(0.5)  # 避免請求太快
        
        if all_data:
            df = pd.DataFrame(all_data)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            return df
        return None
    except Exception as e:
        print(f"TWSE Error: {e}")
        return None

# ===== 函數定義 =====
@st.cache_data
def get_stock_data(code, period="1mo"):
    """取得股票數據 - 優先使用台灣證交所"""
    # 先嘗試台灣證交所
    df = get_twse_data(code)
    if df is not None and not df.empty:
        return df
    
    # 如果失敗，改用 yfinance
    try:
        ticker = yf.Ticker(f"{code}.TW")
        df = ticker.history(period=period)
        return df
    except:
        return None

@st.cache_data  
def get_us_stock_data(code, period="5d"):
    """取得美股數據"""
    try:
        ticker = yf.Ticker(code)
        df = ticker.history(period=period)
        return df
    except:
        return None

def calculate_ma(df, days):
    """計算均線"""
    return df['Close'].rolling(window=days).mean()

def calculate_rsi(df, days=14):
    """計算RSI"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=days).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=days).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@st.cache_data
def get_twse_basic_info(code):
    """從台灣證交所取得基本資訊"""
    try:
        url = f'https://www.twse.com.tw/rwd/zh/fund/T86?date=&stockNo={code}&response=json'
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        
        if data.get('stat') == 'OK' and data.get('data'):
            # 取最新一季資料
            latest = data['data'][0]
            return {
                '季別': latest[0],
                'EPS': float(latest[2].replace(',', '')) if latest[2] != '--' else None,
                '殖利率': float(latest[4].replace(',', '')) if latest[4] != '--' else None,
                '股息': float(latest[5].replace(',', '')) if latest[5] != '--' else None,
            }
        return None
    except:
        return None

@st.cache_data
def get_fundamental_data(code):
    """取得基本面數據 - 優先使用yfinance，失敗則用台灣證交所"""
    
    # 先嘗試 yfinance
    try:
        ticker = yf.Ticker(f"{code}.TW")
        info = ticker.info
        
        # 基本面資料
        fundamentals = {
            'EPS': info.get('trailingEps'),
            '本益比': info.get('trailingPE'),
            '殖利率': info.get('dividendYield'),
            '股息': info.get('dividendRate'),
            '每股淨值': info.get('bookValue'),
            '股價淨值比': info.get('priceToBook'),
            '52週最高': info.get('fiftyTwoWeekHigh'),
            '52週最低': info.get('fiftyTwoWeekLow'),
            '市值': info.get('marketCap'),
            '產業': info.get('sector'),
            '產業類別': info.get('industry'),
            '資料來源': 'yfinance'
        }
        
        # 如果有基本数据就返回
        if fundamentals.get('EPS') or fundamentals.get('本益比'):
            return fundamentals
            
    except:
        pass
    
    # yfinance 失敗，改用台灣證交所
    twse_data = get_twse_basic_info(code)
    if twse_data:
        # 計算本益比（需要股價）
        try:
            ticker = yf.Ticker(f"{code}.TW")
            price = ticker.history(period='1d')['Close'].iloc[-1]
            if twse_data.get('EPS') and price:
                twse_data['本益比'] = round(price / twse_data['EPS'], 2)
        except:
            pass
        
        return {
            'EPS': twse_data.get('EPS'),
            '本益比': twse_data.get('本益比'),
            '殖利率': twse_data.get('殖利率'),
            '股息': twse_data.get('股息'),
            '每股淨值': None,
            '股價淨值比': None,
            '52週最高': None,
            '52週最低': None,
            '市值': None,
            '產業': None,
            '產業類別': None,
            '資料來源': '台灣證交所'
        }
    
    return None

# ===== 側邊欄 =====
st.sidebar.title("📈 少爺的股票儀表板")
st.sidebar.markdown("---")

# 選擇股票
selected_stock = st.sidebar.selectbox(
    "選擇股票",
    list(STOCKS.items()),
    format_func=lambda x: f"{x[1]} ({x[0]})"
)

# 選擇時間範圍
period = st.sidebar.selectbox(
    "選擇時間範圍",
    ["1mo", "3mo", "6mo", "1y", "2y"],
    index=1,
    format_func=lambda x: {"1mo": "1個月", "3mo": "3個月", "6mo": "6個月", "1y": "1年", "2y": "2年"}[x]
)

# 選擇技術指標
indicators = st.sidebar.multiselect(
    "技術指標",
    ["MA5", "MA20", "MA60", "RSI", "Volume"],
    default=["MA20"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 快速連結")
st.sidebar.markdown("- [Yahoo 股市](https://tw.stock.yahoo.com/)")
st.sidebar.markdown("- [TradingView](https://www.tradingview.com/)")

# ===== 主頁面 =====
st.title(f"📈 {selected_stock[1]} ({selected_stock[0]}) - 專業分析")

# 取得數據
df = get_stock_data(selected_stock[0], period)

if df is not None and len(df) > 0:
    # 取得最新價格
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
    change = current_price - prev_price
    change_pct = (change / prev_price) * 100
    
    # 顯示價格
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "現在價格",
            f"${current_price:.2f}",
            f"{change:+.2f} ({change_pct:+.2f}%)"
        )
    with col2:
        high = df['High'].max()
        st.metric("最高價", f"${high:.2f}")
    with col3:
        low = df['Low'].min()
        st.metric("最低價", f"${low:.2f}")
    
    # ===== K線圖 =====
    st.markdown("### 📊 K線圖")
    
    # 準備K線數據
    candle = go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='K線'
    )
    
    # 建立圖表
    fig = go.Figure(data=[candle])
    
    # 加入均線
    colors = {'MA5': 'blue', 'MA20': 'purple', 'MA60': 'orange'}
    
    if "MA5" in indicators:
        ma5 = calculate_ma(df, 5)
        fig.add_trace(go.Scatter(x=df.index, y=ma5, name='MA5', line=dict(color='blue', width=1)))
    
    if "MA20" in indicators:
        ma20 = calculate_ma(df, 20)
        fig.add_trace(go.Scatter(x=df.index, y=ma20, name='MA20', line=dict(color='purple', width=2)))
    
    if "MA60" in indicators:
        ma60 = calculate_ma(df, 60)
        fig.add_trace(go.Scatter(x=df.index, y=ma60, name='MA60', line=dict(color='orange', width=2)))
    
    # 圖表設定
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=500,
        template="plotly_dark",
        title=f"{selected_stock[1]} K線圖",
        yaxis_title="價格",
        xaxis_title="日期"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ===== RSI =====
    if "RSI" in indicators:
        st.markdown("### 📉 RSI 指標")
        
        rsi = calculate_rsi(df)
        
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI', line=dict(color='yellow', width=2)))
        
        # RSI 參考線
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超買")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超賣")
        fig_rsi.add_hline(y=50, line_dash="dot", line_color="gray")
        
        fig_rsi.update_layout(
            height=250,
            template="plotly_dark",
            title="RSI (14)",
            yaxis_title="RSI",
            yaxis_range=[0, 100]
        )
        
        st.plotly_chart(fig_rsi, use_container_width=True)
    
    # ===== 成交量 =====
    if "Volume" in indicators:
        st.markdown("### 📊 成交量")
        
        colors_vol = ['red' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'green' 
                      for i in range(len(df))]
        
        fig_vol = go.Figure(data=[
            go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=colors_vol)
        ])
        
        fig_vol.update_layout(
            height=200,
            template="plotly_dark",
            title="成交量",
            yaxis_title="成交量"
        )
        
        st.plotly_chart(fig_vol, use_container_width=True)
    
    # ===== 技術分析建議 =====
    st.markdown("---")
    st.markdown("### 💡 技術分析建議")
    
    # 計算MA關係
    ma5 = calculate_ma(df, 5).iloc[-1]
    ma20 = calculate_ma(df, 20).iloc[-1]
    ma60 = calculate_ma(df, 60).iloc[-1] if len(df) >= 60 else None
    
    rsi_val = calculate_rsi(df).iloc[-1]
    
    col1, col2 = st.columns(2)
    
    with col1:
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
    
    with col2:
        st.markdown("**RSI 狀態：**")
        if rsi_val > 70:
            st.warning(f"⚠️ RSI = {rsi_val:.1f} → 超買區，可能回檔")
        elif rsi_val < 30:
            st.success(f"✅ RSI = {rsi_val:.1f} → 超賣區，可能反彈")
        else:
            st.info(f"➡️ RSI = {rsi_val:.1f} → 區間整理")
    
    # ===== 基本面數據 =====
    st.markdown("---")
    st.markdown("### 📋 基本面數據")
    
    fundamentals = get_fundamental_data(selected_stock[0])
    
    if fundamentals:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            eps = fundamentals.get('EPS')
            if eps:
                st.metric("EPS (每股盈餘)", f"${eps:.2f}")
        
        with col2:
            pe = fundamentals.get('本益比')
            if pe:
                st.metric("本益比 (P/E)", f"{pe:.2f}")
        
        with col3:
            div_yield = fundamentals.get('殖利率')
            if div_yield and div_yield > 0:
                st.metric("殖利率", f"{div_yield*100:.2f}%")
            else:
                st.metric("殖利率", "N/A")
        
        with col4:
            div = fundamentals.get('股息')
            if div:
                st.metric("現金股息", f"${div:.2f}")
        
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            pb = fundamentals.get('股價淨值比')
            if pb:
                st.metric("股價淨值比 (P/B)", f"{pb:.2f}")
        
        with col6:
            book = fundamentals.get('每股淨值')
            if book:
                st.metric("每股淨值", f"${book:.2f}")
        
        with col7:
            high52 = fundamentals.get('52週最高')
            if high52:
                st.metric("52週最高", f"${high52:.2f}")
        
        with col8:
            low52 = fundamentals.get('52週最低')
            if low52:
                st.metric("52週最低", f"${low52:.2f}")
        
        # 產業資訊
        sector = fundamentals.get('產業')
        industry = fundamentals.get('產業類別')
        if sector or industry:
            st.markdown(f"**產業：** {sector} / {industry}")
        
        # 配息歷史
        div_history = fundamentals.get('配息歷史')
        if div_history is not None and len(div_history) > 0:
            st.markdown("### 💰 配息歷史 (近8次)")
            div_df = pd.DataFrame({
                '日期': [d.strftime('%Y-%m') for d in div_history.index],
                '股息': div_history.values
            })
            st.dataframe(div_df, use_container_width=True, hide_index=True)
        
        # 市值
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

# ===== 報價牆 =====
st.markdown("---")
st.markdown("### 📈 少爺的8檔股票")

# 取得所有股票報價
prices_data = []
for code, name in STOCKS.items():
    df_stock = get_stock_data(code, "5d")
    if df_stock is not None and len(df_stock) > 0:
        current = df_stock['Close'].iloc[-1]
        prev = df_stock['Close'].iloc[-2] if len(df_stock) > 1 else current
        change = ((current - prev) / prev) * 100
        prices_data.append({
            '代號': code,
            '名稱': name,
            '現價': current,
            '漲跌幅': change
        })

if prices_data:
    df_prices = pd.DataFrame(prices_data)
    
    # 排序
    df_prices = df_prices.sort_values('漲跌幅', ascending=False)
    
    # 顯示表格
    def color_change(val):
        color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
        return f'color: {color}'
    
    st.dataframe(
        df_prices.style.format({'現價': '${:.2f}', '漲跌幅': '{:+.2f}%'})
                          .applymap(color_change, subset=['漲跌幅']),
        use_container_width=True
    )

# ===== 美股報價 =====
st.markdown("---")
st.markdown("### 🌍 美股昨晚表現")

us_prices = []
for code, name in US_STOCKS.items():
    df_us = get_us_stock_data(code)
    if df_us is not None and len(df_us) > 0:
        current = df_us['Close'].iloc[-1]
        prev = df_us['Close'].iloc[-2] if len(df_us) > 1 else current
        change = ((current - prev) / prev) * 100
        us_prices.append({
            '代號': code,
            '名稱': name,
            '現價': current,
            '漲跌幅': change
        })

if us_prices:
    df_us_prices = pd.DataFrame(us_prices)
    df_us_prices = df_us_prices.sort_values('漲跌幅', ascending=False)
    
    st.dataframe(
        df_us_prices.style.format({'現價': '${:.2f}', '漲跌幅': '{:+.2f}%'})
                          .applymap(color_change, subset=['漲跌幅']),
        use_container_width=True
    )

# ===== 頁腳 =====
st.markdown("---")
st.markdown(f"*📊 資料更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
st.markdown("*本報告僅供參考，不構成投資建議*")
