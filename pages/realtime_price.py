#!/usr/bin/env python3
"""
Yahoo 股市即時股價爬蟲
"""
import requests
from bs4 import BeautifulSoup
import time
import streamlit as st

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

@st.cache_data(ttl=60)  # 快取 60 秒
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
            change_text = change_elem[0].get_text().strip()
            # 判斷漲跌
            if '+' in change_text:
                change_pct = float(change_text.replace('+', '').replace('%', ''))
            elif '-' in change_text:
                change_pct = float(change_text.replace('-', '').replace('%', ''))
                change_pct = -change_pct
        
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
