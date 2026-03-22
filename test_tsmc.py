#!/usr/bin/env python3
"""測試版 - 只抓取台積電資料"""

import streamlit as st
import yfinance as yf
from datetime import datetime

st.set_page_config(
    page_title="台積電測試",
    page_icon="📈",
    layout="wide"
)

st.title("📈 台積電 (2330) 資料測試")

st.markdown("---")

# 測試1: 基本資料
st.markdown("### 基本資料")

try:
    ticker = yf.Ticker("2330.TW")
    info = ticker.info
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("股價", f"${info.get('currentPrice', 'N/A')}")
    with col2:
        st.metric("本益比", info.get('trailingPE', 'N/A'))
    with col3:
        st.metric("EPS", info.get('trailingEps', 'N/A'))
    with col4:
        roe = info.get('returnOnEquity', 0)
        st.metric("ROE", f"{roe*100:.1f}%" if roe else "N/A")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        rev = info.get('totalRevenue', 0)
        st.metric("營收", f"{rev/1e9:.1f}B" if rev else "N/A")
    with col6:
        st.metric("淨利", f"{info.get('netIncome', 'N/A')}")
    with col7:
        st.metric("殖利率", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "N/A")
    with col8:
        st.metric("每股淨值", info.get('bookValue', 'N/A'))
        
    st.success(f"✅ 抓到 {len(info)} 個欄位的資料")
    
except Exception as e:
    st.error(f"❌ 錯誤: {e}")

st.markdown("---")

# 測試2: 歷史股價
st.markdown("### 歷史股價 (3個月)")

try:
    df = ticker.history(period="3mo")
    if df is not None and len(df) > 0:
        st.line_chart(df['Close'])
        st.success(f"✅ 抓到 {len(df)} 天的股價資料")
    else:
        st.error("❌ 無法取得歷史股價")
except Exception as e:
    st.error(f"❌ 錯誤: {e}")

st.markdown("---")

# 除錯資訊
st.markdown("### 除錯資訊")
st.write(f"現在時間: {datetime.now()}")
st.write(f"YFinance 版本: {yf.__version__}")
