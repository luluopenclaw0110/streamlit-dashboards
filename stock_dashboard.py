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
import os
import time
import pytz
from bs4 import BeautifulSoup

# 頁面設定
st.set_page_config(
    page_title="少爺的股票儀表板",
    page_icon="📈",
    layout="wide"
)

# 自訂字體大小
st.markdown("""
<style>
    /* 表格字體加大 */
    .dataframe th, .dataframe td {
        font-size: 18px !important;
    }
    div[data-testid="stDataFrame"] td {
        font-size: 18px !important;
    }
    div[data-testid="stDataFrame"] th {
        font-size: 18px !important;
    }
    /* 一般文字加大 */
    .stMarkdown, .stText, p, li {
        font-size: 18px !important;
    }
    /* 基本資料文字加大 */
    div.stWrite {
        font-size: 18px !important;
    }
</style>
""", unsafe_allow_html=True)

# 少爺的股票清單
STOCKS = {
    '2330': '台積電',
    '2317': '鴻海', 
    '3532': '台勝科',
    '1503': '士電',
    '2887': '台新新光金',
    '1605': '華新',
    '1717': '長興',
    '1802': '台玻',
    '2399': '映泰',
    '1514': '亞力',
}

# ===== 從 JSON 讀取基本面資料 =====
def load_fundamentals():
    """從 JSON 檔案載入基本面資料"""
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'stock_fundamentals.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['stocks'], data.get('update_date', '未知')
    except Exception as e:
        return {}, "載入失敗"

def load_industry_news():
    """從 JSON 檔案載入產業動態"""
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'stock_industry_news.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['stocks'], data.get('update_date', '未知')
    except Exception as e:
        return {}, "載入失敗"

FUNDAMENTALS, FUNDAMENTALS_UPDATE_DATE = load_fundamentals()
INDUSTRY_NEWS, INDUSTRY_NEWS_UPDATE_DATE = load_industry_news()

# 美股
US_STOCKS = {
    'NVDA': 'NVIDIA',
    'TSLA': 'Tesla',
    'AAPL': 'Apple',
    'MSFT': 'Microsoft',
    'GOOGL': 'Google',
    'META': 'Meta',
    'AMZN': 'Amazon',
    'TSM': '台積電 ADR',
}

# ===== 側邊欄 =====
st.sidebar.title("📈 少爺的股票儀表板")
st.sidebar.markdown("---")

# 分頁選擇
page = st.sidebar.radio(
    "選擇頁面",
    ["📊 專業分析", "⚡ 即時股價", "🏭 產業分析"]
)

st.sidebar.markdown("---")

# 根據頁面顯示不同的選項
if page == "📊 專業分析":
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

elif page == "🏭 產業分析":
    # 產業分析頁面的選項
    st.sidebar.markdown("### 🏭 產業分析")
    st.sidebar.info("選擇產業和股票進行專業分析")

elif page == "⚡ 即時股價":
    # 即時股價頁面
    st.sidebar.markdown("### ⚡ 即時報價")
    st.sidebar.info("顯示所有股票的即時報價")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 快速連結")
st.sidebar.markdown("- [Yahoo 股市](https://tw.stock.yahoo.com/)")
st.sidebar.markdown("- [TradingView](https://www.tradingview.com/)")

# ===== 函數定義 =====
@st.cache_data
def get_stock_data(code, period):
    """使用 yfinance 取得股票數據"""
    try:
        if code in STOCKS:
            ticker = yf.Ticker(f"{code}.TW")
        else:
            ticker = yf.Ticker(code)
        
        df = ticker.history(period=period)
        
        if df.empty:
            return None
        return df
    except Exception as e:
        return None

def calculate_ma(df, period):
    """計算移動平均線"""
    return df['Close'].rolling(window=period).mean()

def calculate_rsi(df, period=14):
    """計算RSI"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@st.cache_data(ttl=60)
def get_realtime_price(code):
    """從 Yahoo 股市抓取即時股價"""
    try:
        url = f'https://tw.stock.yahoo.com/quote/{code}'
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        web = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(web.text, 'html.parser')
        
        price_elem = soup.select('.Fz\\(32px\\)')
        if price_elem:
            price_text = price_elem[0].get_text().replace(',', '')
            price = float(price_text)
            
            elem_classes = price_elem[0].get('class', [])
            is_down = any('trend-down' in str(c) for c in elem_classes)
        else:
            return None
        
        change_elem = soup.select('.Fz\\(20px\\)')
        change_pct = 0
        if change_elem:
            change_text = change_elem[0].get_text().strip().replace(',', '')
            try:
                change_amount = float(change_text)
                if price > 0:
                    change_pct = (change_amount / (price - change_amount)) * 100
                    if is_down:
                        change_pct = -abs(change_pct)
            except:
                change_pct = 0
        
        return {'price': price, 'change_pct': round(change_pct, 2)}
    except:
        return None

# ===== 專業分析頁面 =====
if page == "📊 專業分析":
    st.title("📊 股票專業分析")
    
    # 取得數據
    df = get_stock_data(selected_stock[0], period)
    
    # 取得數據
    df = get_stock_data(selected_stock[0], period)
    
    if df is not None and len(df) > 0:
        # 顯示基本資訊
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[0] if len(df) > 1 else current_price
        change = current_price - prev_price
        change_pct = (change / prev_price) * 100
        
        # 取得當日漲跌幅
        realtime_data = get_realtime_price(selected_stock[0])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 區間漲跌（收盤價）**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("目前價格", f"${current_price:,.2f}", f"{change:+.2f}")
            with col_b:
                st.metric("漲跌幅", f"{change_pct:+.2f}%")
            col_c, col_d = st.columns(2)
            with col_c:
                st.metric("期間最高", f"${df['High'].max():,.2f}")
            with col_d:
                st.metric("期間最低", f"${df['Low'].min():,.2f}")
        
        with col2:
            st.markdown("**📈 即時報價**")
            if realtime_data:
                col_e, col_f = st.columns(2)
                with col_e:
                    st.metric("現價", f"${realtime_data['price']:,.2f}", f"{realtime_data['change_pct']:+.2f}%")
                with col_f:
                    # 計算漲跌金額
                    change_amt = realtime_data['price'] * realtime_data['change_pct'] / 100
                    st.metric("漲跌金額", f"{change_amt:+,.2f}")
            else:
                st.info("無法取得即時資料")
        
        # K線圖
        st.markdown("### 📊 K線圖")
        
        candle = go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='K線',
            increasing_line_color='red',
            decreasing_line_color='green'
        )
        
        fig = go.Figure(data=[candle])
        
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
        
        fig.update_layout(
            xaxis_rangeslider_visible=False,
            height=500,
            template="plotly_dark",
            title=f"{selected_stock[1]} K線圖",
            yaxis_title="價格",
            xaxis_title="日期"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # RSI
        if "RSI" in indicators:
            st.markdown("### 📉 RSI 指標")
            
            rsi = calculate_rsi(df)
            
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI', line=dict(color='cyan', width=2)))
            
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超買")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超賣")
            fig_rsi.add_hline(y=50, line_dash="dot", line_color="gray")
            
            fig_rsi.update_layout(
                height=350,
                template="plotly_dark",
                title="RSI (14)",
                yaxis_title="RSI",
                yaxis_range=[0, 100]
            )
            
            st.plotly_chart(fig_rsi, use_container_width=True)
        
        # 成交量
        if "Volume" in indicators:
            st.markdown("### 📊 成交量")
            
            colors_vol = ['red' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'green' 
                          for i in range(len(df))]
            
            fig_vol = go.Figure(data=[
                go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=colors_vol)
            ])
            
            fig_vol.update_layout(
                height=350,
                template="plotly_dark",
                title="成交量",
                yaxis_title="成交量",
                xaxis_title="日期"
            )
            
            st.plotly_chart(fig_vol, use_container_width=True)
        
        # 基本面資料
        st.markdown("---")
        st.markdown("### 📈 基本面資料")
        st.caption(f"最後更新：{FUNDAMENTALS_UPDATE_DATE}")
        
        if selected_stock[0] in FUNDAMENTALS:
            fundamentals = FUNDAMENTALS[selected_stock[0]]
            
            # 基本資料
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**基本資料**")
                st.write(f"📈 股價：{fundamentals.get('股價', 'N/A')}")
                st.write(f"📊 本益比：{fundamentals.get('本益比', 'N/A')}")
                st.write(f"💰 殖利率：{fundamentals.get('殖利率', 'N/A')}")
                st.write(f"📉 每股淨值：{fundamentals.get('每股淨值', 'N/A')}")
                st.write(f"📅 財報季度：{fundamentals.get('財報季度', 'N/A')}")
                st.write(f"💵 EPS：{fundamentals.get('EPS', 'N/A')}")
            
            # 配息歷史 (近8次)
            div_history = fundamentals.get('配息歷史')
            if div_history and len(div_history) > 0:
                st.markdown("### 💰 配息歷史 (近8次)")
                div_df = pd.DataFrame(div_history)
                st.dataframe(div_df, hide_index=True, use_container_width=True)
            
            # 季財報 (近4季)
            quarterly = fundamentals.get('季財報')
            if quarterly and len(quarterly) > 0:
                st.markdown("### 📊 季財報 (近4季)")
                q_df = pd.DataFrame(quarterly)
                
                # 格式化數字（單位縮減）
                for col in ['營收', '毛利', '營業利益', '淨利']:
                    if col in q_df.columns:
                        q_df[col] = q_df[col].apply(lambda x: f"${x/1e9:.1f}B" if x and x > 0 else "N/A")
                if 'EPS' in q_df.columns:
                    q_df['EPS'] = q_df['EPS'].apply(lambda x: f"${x}" if x else "N/A")
                if '稀釋EPS' in q_df.columns:
                    q_df['稀釋EPS'] = q_df['稀釋EPS'].apply(lambda x: f"${x}" if x else "N/A")
                
                st.dataframe(q_df, hide_index=True, use_container_width=True)
        else:
            st.info("尚無基本面資料")
        
        # 產業動態
        if selected_stock[0] in INDUSTRY_NEWS:
            st.markdown("---")
            st.markdown("### 📰 產業動態")
            st.caption(f"最後更新：{INDUSTRY_NEWS_UPDATE_DATE}")
            
            news_data = INDUSTRY_NEWS[selected_stock[0]]
            
            # 產業分析
            if '產業分析' in news_data:
                st.info(f"📊 {news_data['產業分析']}")
            
            # 個股新聞
            if '個股新聞' in news_data:
                st.markdown("**個股新聞：**")
                for news in news_data['個股新聞'][:5]:
                    title = news.get('標題', '無標題')
                    url = news.get('連結', news.get('url', '#'))
                    st.markdown(f"- [{title}]({url})")
            
            # 產業新聞
            if '產業新聞' in news_data:
                st.markdown("**產業新聞：**")
                for news in news_data['產業新聞'][:5]:
                    title = news.get('標題', '無標題')
                    url = news.get('連結', news.get('url', '#'))
                    st.markdown(f"- [{title}]({url})")
        else:
            st.info("尚無產業動態")
    
    # ===== 美股報價 =====
    st.markdown("---")
    st.markdown("### 🌍 美股昨晚表現")
    
    us_prices = []
    for code, name in US_STOCKS.items():
        try:
            df_us = get_stock_data(code, "5d")
            if df_us is not None and len(df_us) > 1:
                current = df_us['Close'].iloc[-1]
                prev = df_us['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                us_prices.append({
                    '代號': code,
                    '名稱': name,
                    '現價': round(current, 2),
                    '漲跌幅': round(change, 2)
                })
        except:
            pass
    
    if us_prices and len(us_prices) > 0:
        df_us_prices = pd.DataFrame(us_prices)
        
        # 移除可能的NaN值
        df_us_prices = df_us_prices.dropna(subset=['現價', '漲跌幅'])
        
        if len(df_us_prices) > 0:
            df_us_prices = df_us_prices.sort_values('漲跌幅', ascending=False)
            
            # 格式化漲跌幅
            df_us_prices['漲跌'] = df_us_prices['漲跌幅'].apply(lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%")
            df_us_prices['現價'] = df_us_prices['現價'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(
                df_us_prices[['代號', '名稱', '現價', '漲跌']],
                hide_index=True,
                use_container_width=True
            )
    else:
        st.info("無法取得美股資料")

# ===== 即時股價頁面 =====
elif page == "⚡ 即時股價":
    st.title("⚡ 即時股價")
    st.caption("資料來源：Yahoo 股市 | 每分鐘更新")
    
    with st.spinner('正在抓取即時股價...'):
        prices = []
        for code, name in STOCKS.items():
            data = get_realtime_price(code)
            if data:
                prices.append({
                    '代號': code,
                    '名稱': name,
                    '現價': data['price'],
                    '漲跌幅': data['change_pct']
                })
            time.sleep(0.5)
    
    if prices:
        df = pd.DataFrame(prices)
        
        # 顯示
        for _, row in df.iterrows():
            emoji = '🔴' if row['漲跌幅'] > 0 else '🟢' if row['漲跌幅'] < 0 else '⚪'
            
            col1, col2, col3 = st.columns([1, 2, 2])
            with col1:
                st.write(f"**{row['代號']}** {row['名稱']}")
            with col2:
                st.write(f"💵 ${row['現價']:,.2f}")
            with col3:
                st.write(f"{emoji} {row['漲跌幅']:+.2f}%")
        
        st.divider()
        
        # 簡易表格
        st.subheader("📊 報價表")
        
        df['漲跌'] = df['漲跌幅'].apply(lambda x: f"+{x:.2f}%" if x > 0 else f"{x:.2f}%")
        df['現價'] = df['現價'].apply(lambda x: f"${x:,.2f}")
        
        df = df.sort_values('漲跌幅', ascending=False)
        
        def color_change(val):
            return 'red' if val > 0 else 'green' if val < 0 else 'gray'
        
        st.dataframe(
            df[['代號', '名稱', '現價', '漲跌']],
            hide_index=True,
            use_container_width=True
        )
        
        st.caption(f"🕐 更新時間：{datetime.now().strftime('%H:%M:%S')}")
    else:
        st.error("無法取得股價資料，請稍後再試")

# ===== 產業分析頁面 =====
elif page == "🏭 產業分析":
    st.title("🏭 產業龍頭專業分析")
    st.caption("每天自動更新 | 產業排名 - 專業技術分析 + 基本面 + 買賣建議")
    
    # 產業龍頭股票（各產業營收第一）
    INDUSTRY_LEADERS = {
        '半導體': {'2330': '台積電'},
        '電子組裝': {'2317': '鴻海'},
        '傳產-鋼鐵': {'2002': '中鋼'},
        '傳產-塑化': {'1326': '台化'},
    }
    
    # 產業完整清單
    INDUSTRY_ALL = {
        # AI / 電子產業鏈
        '晶圓代工': {'2330': '台積電', '2303': '聯電', '5347': '世界先進'},
        'IC設計': {'2454': '聯發科', '2379': '瑞昱', '3034': '聯詠', '6415': '矽力-KY'},
        'ASIC': {'3661': '世芯-KY', '3443': '創意', '3035': '智原'},
        'IP矽智財': {'3529': '力旺', '6643': 'M31', '3035': '智原'},
        '記憶體': {'2408': '南亞科', '2344': '華邦電', '2337': '旺宏'},
        '封測': {'3711': '日月光投控', '6239': '力成', '2449': '京元電子'},
        '半導體設備': {'2404': '漢唐', '6196': '帆宣', '3583': '辛耘', '6223': '旺矽'},
        '矽晶圓': {'6488': '環球晶', '3532': '台勝科', '3016': '嘉晶'},
        'CCL材料': {'2383': '台光電', '6213': '聯茂', '6274': '台燿'},
        'IC載板': {'3037': '欣興', '3189': '景碩', '8046': '南電'},
        'PCB': {'3044': '健鼎', '5469': '瀚宇博', '2313': '華通'},
        'AI伺服器': {'2317': '鴻海', '2382': '廣達', '3231': '緯創', '6669': '緯穎', '2356': '英業達', '2376': '技嘉'},
        '散熱': {'3017': '奇鋐', '3324': '雙鴻', '6230': '超眾'},
        '電源': {'2308': '台達電', '2301': '光寶科', '6412': '群電'},
        '光通訊': {'3363': '上詮', '6442': '光聖', '3081': '聯亞'},
        '光學': {'3008': '大立光', '3406': '玉晶光', '3019': '亞光'},
        # 傳產
        '塑化': {'1301': '台塑', '1303': '南亞', '1326': '台化'},
        '鋼鐵': {'2002': '中鋼', '2014': '中鴻', '2027': '大成鋼'},
        '航運': {'2603': '長榮', '2609': '陽明', '2615': '萬海'},
        '水泥': {'1101': '台泥', '1102': '亞泥'},
        # 金融
        '金控': {'2881': '富邦金', '2882': '國泰金', '2891': '中信金', '2886': '兆豐金', '2884': '玉山金'},
    }
    
    # 技術指標計算函數
    def calculate_ma(df, period):
        return df['Close'].rolling(window=period).mean()
    
    def calculate_rsi(df, period=14):
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_kd(df):
        low_min = df['Low'].rolling(window=9).min()
        high_max = df['High'].rolling(window=9).max()
        k = 100 * (df['Close'] - low_min) / (high_max - low_min)
        d = k.rolling(window=3).mean()
        return k, d
    
    def calculate_bollinger(df, period=20, std_dev=2):
        ma = df['Close'].rolling(window=period).mean()
        std = df['Close'].rolling(window=period).std()
        upper = ma + std_dev * std
        lower = ma - std_dev * std
        return ma, upper, lower
    
    def calculate_macd(df, fast=12, slow=26, signal=9):
        ema_fast = df['Close'].ewm(span=fast).mean()
        ema_slow = df['Close'].ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def get_recommendation(roe, profit_growth, pe_ratio):
        """給出買賣建議"""
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
    
    # 產業選擇器
    selected_industry = st.selectbox("選擇產業", list(INDUSTRY_ALL.keys()))
    
    # 取得該產業的股票
    industry_stocks = INDUSTRY_ALL[selected_industry]
    
    # 取得股價數據
    @st.cache_data(ttl=300)
    def get_industry_stock_data(code):
        try:
            ticker = yf.Ticker(f"{code}.TW")
            df = ticker.history(period="6mo")  # 改為6個月，這樣MA60才能計算
            return df
        except:
            return None
    
    # 取得基本面數據（不安裝快取，確保每次取得最新資料）
    def get_fundamental_data(code):
        try:
            ticker = yf.Ticker(f"{code}.TW")
            info = ticker.info
            if not info or len(info) < 3:
                return None
            return {
                '股價': info.get('currentPrice', 0),
                '本益比': info.get('trailingPE', 0),
                '殖利率': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                '每股淨值': info.get('bookValue', 0),
                'EPS': info.get('trailingEps', 0),
                'ROE': (info.get('returnOnEquity', 0) or 0) * 100,
                '營收': info.get('totalRevenue', 0),
                '淨利': info.get('netIncome', 0),
                '營收成長': (info.get('revenueGrowth', 0) or 0) * 100,
                '獲利成長': (info.get('earningsGrowth', 0) or 0) * 100,
            }
        except Exception as e:
            return None
    
    import time
    
    # 營收排名：只留第一個股票，頁面載入就查
    st.markdown("### 📊 產業營收排名")
    
    # 只取第一個股票
    first_code, first_name = list(industry_stocks.items())[0]
    st.markdown(f"**{first_name} ({first_code})**")
    
    # 頁面載入就查
    fundamental = get_fundamental_data(first_code)
    
    if fundamental:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            rev = fundamental.get('營收', 0)
            st.metric("營收", f"{round(rev/1e9, 1)}B" if rev else "N/A")
        with col2:
            st.metric("淨利", f"{round(fundamental.get('淨利', 0)/1e9, 2)}B" if fundamental.get('淨利') else "N/A")
        with col3:
            st.metric("EPS", f"{round(fundamental.get('EPS', 0), 2)}" if fundamental.get('EPS') else "N/A")
        with col4:
            st.metric("ROE", f"{fundamental.get('ROE', 0):.1f}%" if fundamental.get('ROE') else "N/A")
        
        col5, col6 = st.columns(2)
        with col5:
            st.metric("本益比", round(fundamental.get('本益比', 0), 1) if fundamental.get('本益比') else "N/A")
        with col6:
            rec, _ = get_recommendation(fundamental.get('ROE', 0), fundamental.get('獲利成長', 0), fundamental.get('本益比', 0))
            st.metric("建議", rec)
    else:
        st.info("無法取得資料")
    
    st.markdown("---")
    
    # 選擇要分析的股票
    analysis_stock = st.selectbox(
        "選擇股票進行專業分析",
        list(industry_stocks.items()),
        format_func=lambda x: f"{x[1]} ({x[0]})"
    )
    
    # 取得數據
    df = get_industry_stock_data(analysis_stock[0])
    fundamental = get_fundamental_data(analysis_stock[0])
    
    if df is not None and len(df) > 0:
        # 基本面資訊
        st.markdown("### 📈 基本面資料")
        
        if fundamental:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("股價", f"${fundamental['股價']:,.2f}")
            with col2:
                st.metric("本益比", f"{fundamental['本益比']:.1f}")
            with col3:
                st.metric("ROE", f"{fundamental['ROE']:.1f}%")
            with col4:
                rec, color = get_recommendation(fundamental['ROE'], fundamental['獲利成長'], fundamental['本益比'])
                st.markdown(f"**{rec}**")
            
            col5, col6, col7, col8 = st.columns(4)
            with col5:
                st.metric("EPS", f"${fundamental['EPS']:.2f}")
            with col6:
                st.metric("殖利率", f"{fundamental['殖利率']:.2f}%")
            with col7:
                st.metric("營收成長", f"{fundamental['營收成長']:+.1f}%")
            with col8:
                st.metric("獲利成長", f"{fundamental['獲利成長']:+.1f}%")
        
        st.markdown("---")
        
        # K線圖 + 技術指標
        st.markdown("### 📊 K線圖 + 技術指標")
        
        # K線
        candle = go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='K線',
            increasing_line_color='red',
            decreasing_line_color='green'
        )
        
        fig = go.Figure(data=[candle])
        
        # MA
        ma20 = calculate_ma(df, 20)
        ma60 = calculate_ma(df, 60)
        fig.add_trace(go.Scatter(x=df.index, y=ma20, name='MA20', line=dict(color='purple', width=2)))
        fig.add_trace(go.Scatter(x=df.index, y=ma60, name='MA60', line=dict(color='orange', width=2)))
        
        #布林通道
        ma, upper, lower = calculate_bollinger(df)
        fig.add_trace(go.Scatter(x=df.index, y=upper, name='布林上軌', line=dict(color='gray', width=1, dash='dash')))
        fig.add_trace(go.Scatter(x=df.index, y=lower, name='布林下軌', line=dict(color='gray', width=1, dash='dash')))
        
        fig.update_layout(
            xaxis_rangeslider_visible=False,
            height=450,
            template="plotly_dark",
            title=f"{analysis_stock[1]} K線圖 + MA + 布林通道",
            yaxis_title="價格",
            xaxis_title="日期"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # RSI + KD
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### RSI 指標")
            rsi = calculate_rsi(df)
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI', line=dict(color='cyan', width=2)))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超買")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超賣")
            fig_rsi.update_layout(height=300, template="plotly_dark", yaxis_range=[0, 100])
            st.plotly_chart(fig_rsi, use_container_width=True)
        
        with col2:
            st.markdown("#### KD 指標")
            k, d = calculate_kd(df)
            fig_kd = go.Figure()
            fig_kd.add_trace(go.Scatter(x=df.index, y=k, name='K', line=dict(color='blue', width=2)))
            fig_kd.add_trace(go.Scatter(x=df.index, y=d, name='D', line=dict(color='red', width=2)))
            fig_kd.update_layout(height=300, template="plotly_dark")
            st.plotly_chart(fig_kd, use_container_width=True)
        
        # MACD
        st.markdown("#### MACD 指標")
        macd, signal, hist = calculate_macd(df)
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Bar(x=df.index, y=hist, name='柱狀', marker_color='gray'))
        fig_macd.add_trace(go.Scatter(x=df.index, y=macd, name='MACD', line=dict(color='blue', width=2)))
        fig_macd.add_trace(go.Scatter(x=df.index, y=signal, name='Signal', line=dict(color='orange', width=2)))
        fig_macd.update_layout(height=300, template="plotly_dark")
        st.plotly_chart(fig_macd, use_container_width=True)
        
        # 成交量
        st.markdown("#### 成交量")
        colors_vol = ['red' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'green' for i in range(len(df))]
        fig_vol = go.Figure(data=[go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=colors_vol)])
        fig_vol.update_layout(height=250, template="plotly_dark")
        st.plotly_chart(fig_vol, use_container_width=True)
        
    else:
        st.error("無法取得股價資料")
    
    st.caption(f"🕐 資料更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ===== 頁腳 =====
st.markdown("---")
st.markdown(f"*📊 資料更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
st.markdown("*本報告僅供參考，不構成投資建議*")
