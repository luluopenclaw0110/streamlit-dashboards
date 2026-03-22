#!/usr/bin/env python3
"""測試版 - 檢查get_fundamental_data函數位置"""

import streamlit as st
import yfinance as yf
from datetime import datetime

st.set_page_config(
    page_title="台積電測試V2",
    page_icon="📈",
    layout="wide"
)

st.title("📈 台積電 (2330) 資料測試 V2")

# 直接在這裡定義函數
def get_fundamental_data(code):
    try:
        ticker = yf.Ticker(f"{code}.TW")
        info = ticker.info
        if not info or len(info) < 3:
            return None
        return {
            '股價': info.get('currentPrice', 0),
            '本益比': info.get('trailingPE', 0),
            '營收': info.get('totalRevenue', 0),
            'EPS': info.get('trailingEps', 0),
            'ROE': (info.get('returnOnEquity', 0) or 0) * 100,
        }
    except Exception as e:
        st.error(f"錯誤: {e}")
        return None

st.markdown("---")

# 直接調用
st.markdown("### 直接調用測試")
data = get_fundamental_data("2330")

if data:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("股價", f"${data.get('股價', 'N/A')}")
    with col2:
        rev = data.get('營收', 0)
        st.metric("營收", f"{round(rev/1e9, 1)}B" if rev else "N/A")
    with col3:
        st.metric("EPS", data.get('EPS', 'N/A'))
    with col4:
        st.metric("ROE", f"{data.get('ROE', 0):.1f}%" if data.get('ROE') else "N/A")
    st.success("✅ 成功取得資料！")
else:
    st.error("❌ 無法取得資料")

st.markdown("---")
st.write(f"時間: {datetime.now()}")
