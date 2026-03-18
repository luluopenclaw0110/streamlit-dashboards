#!/usr/bin/env python3
"""
Yahoo 股市即時股價爬蟲
"""
import requests
from bs4 import BeautifulSoup
import time
import streamlit as st
from datetime import datetime
import pytz

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
    'TSM': '台積電 ADR'
}

def is_trading_hours():
    """判斷是否在台灣股市交易時間內"""
    tw_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tw_tz)
    
    # 取得星期幾 (0=周一, 6=周日)
    weekday = now.weekday()
    
    # 假日(六日)不交易
    if weekday >= 5:
        return False
    
    # 交易時間 9:00 - 14:00 (含盤後定價)
    hour = now.hour
    minute = now.minute
    
    if hour < 9:
        return False
    if hour >= 14:
        return False
    
    return True

def get_cache_ttl():
    """根據是否在交易時間回傳不同的快取時間"""
    if is_trading_hours():
        return 60  # 交易時間內 60 秒更新
    else:
        return 3600  # 非交易時間 1 小時更新

@st.cache_data(ttl=get_cache_ttl())
def get_realtime_price(code):
    """從 Yahoo 股市抓取即時股價"""
    try:
        url = f'https://tw.stock.yahoo.com/quote/{code}'
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        web = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(web.text, 'html.parser')
        
        # 找股價 (32px 字體)
        price_elem = soup.select('.Fz\\(32px\\)')
        if price_elem:
            price_text = price_elem[0].get_text().replace(',', '')
            price = float(price_text)
        else:
            return None
        
        # 找漲跌幅 (20px 字體)
        change_elem = soup.select('.Fz\\(20px\\)')
        change = 0
        change_pct = 0
        if change_elem:
            # change_elem[0] = 漲跌金額 (如 "35.00")
            # change_elem[1] = 漲跌百分比 (如 "(1.87%)")
            # 找百分比那個
            for elem in change_elem:
                text = elem.get_text().strip()
                if '(' in text and ')' in text and '%' in text:
                    # 解析 "(1.87%)" 或 "(-1.5%)"
                    pct_text = text.replace('(', '').replace(')', '').replace('%', '')
                    try:
                        change_pct = float(pct_text)
                    except:
                        change_pct = 0
                    break
        
        return {
            'price': price,
            'change_pct': change_pct
        }
    except Exception as e:
        return None

def get_all_prices():
    """取得所有股票的即時股價"""
    results = []
    
    for code, name in STOCKS.items():
        data = get_realtime_price(code)
        if data:
            results.append({
                '代號': code,
                '名稱': name,
                '現價': data['price'],
                '漲跌幅': data['change_pct']
            })
        # 不要太快抓，避免被 ban
        time.sleep(0.5)
    
    return results

# ===== Streamlit 頁面 =====
st.set_page_config(
    page_title="即時股價",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ 即時股價")
st.caption("資料來源：Yahoo 股市 | 每分鐘更新")

# 取得即時股價
with st.spinner('正在抓取即時股價...'):
    prices = get_all_prices()

if prices:
    import pandas as pd
    
    # 轉換為 DataFrame
    df = pd.DataFrame(prices)
    
    # 計算漲跌顏色
    def color_change(val):
        if val > 0:
            return '🟢'
        elif val < 0:
            return '🔴'
        else:
            return '⚪'
    
    # 顯示
    for _, row in df.iterrows():
        emoji = '🟢' if row['漲跌幅'] > 0 else '🔴' if row['漲跌幅'] < 0 else '⚪'
        
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
    
    # 格式化漲跌幅
    df['漲跌'] = df['漲跌幅'].apply(lambda x: f"+{x:.2f}%" if x > 0 else f"{x:.2f}%")
    df['現價'] = df['現價'].apply(lambda x: f"${x:,.2f}")
    
    # 排序
    df = df.sort_values('漲跌幅', ascending=False)
    
    st.dataframe(
        df[['代號', '名稱', '現價', '漲跌']],
        hide_index=True,
        use_container_width=True
    )
    
    # 更新時間
    from datetime import datetime
    st.caption(f"🕐 更新時間：{datetime.now().strftime('%H:%M:%S')}")
    
else:
    st.error("無法取得股價資料，請稍後再試")

# 手動更新按鈕
if st.button('🔄 重新整理'):
    st.rerun()

# 顯示交易時間狀態
st.divider()
tw_tz = pytz.timezone('Asia/Taipei')
now = datetime.now(tw_tz)
is_trading = is_trading_hours()

if is_trading:
    st.success(f"🟢 股市交易中 ({now.strftime('%H:%M:%S')}) | 自動更新頻率：60秒")
else:
    st.info(f"⚪ 股市已收盤 ({now.strftime('%H:%M:%S')}) | 自動更新頻率：1小時")
