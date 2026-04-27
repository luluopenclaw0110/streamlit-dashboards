#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
20檔產業龍頭深度分析報告
格式比照少爺持股深度分析報告
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime

# 頁面設定
st.set_page_config(
    page_title="20檔產業龍頭深度分析",
    page_icon="📊",
    layout="wide"
)

# 載入數據
@st.cache_data
def load_stock_data():
    return [
        {"代碼": "2330", "名稱": "台積電", "產業": "半導體", "股價": 1083.0, "PE": 31.58, "Forward PE": 25.21, "EPS": 34.29, "營收成長": 0.276, "盈餘成長": 0.54, "ROE": 0.362, "評等": "🟢 建議持有", "評估理由": "AI需求無敵，先進製程壟斷，全球晶圓代工龍頭"},
        {"代碼": "2317", "名稱": "鴻海", "產業": "AI伺服器/電子代工", "股價": 196.5, "PE": 16.49, "Forward PE": 13.0, "EPS": 11.91, "營收成長": 0.065, "盈餘成長": 0.20, "ROE": 0.113, "評等": "🔵 成長潛力", "評估理由": "PE便宜，AI伺服器前景佳，布局電動車"},
        {"代碼": "2313", "名稱": "華通", "產業": "PCB/AI伺服器", "股價": 72.8, "PE": 38.43, "Forward PE": 22.0, "EPS": 1.89, "營收成長": 0.15, "盈餘成長": 0.30, "ROE": 0.142, "評等": "🟢 建議持有", "評估理由": "AI伺服器PCB需求強勁，HDI龍頭"},
        {"代碼": "3008", "名稱": "大立光", "產業": "光學鏡頭", "股價": 2825.0, "PE": 16.79, "Forward PE": 14.5, "EPS": 168.25, "營收成長": 0.03, "盈餘成長": 0.15, "ROE": 0.115, "評等": "🔵 成長潛力", "評估理由": "光學龍頭，專利壁壘，高階鏡頭需求回升"},
        {"代碼": "9921", "名稱": "巨大", "產業": "運動休閒", "股價": 235.0, "PE": 35.43, "Forward PE": 18.0, "EPS": 6.63, "營收成長": -0.05, "盈餘成長": -0.10, "ROE": 0.023, "評等": "🔴 風險", "評估理由": "歐美自行車需求放緩，庫存調整中"},
        {"代碼": "2882", "名稱": "兆豐金", "產業": "金控", "股價": 37.5, "PE": 10.48, "Forward PE": 10.0, "EPS": 3.58, "營收成長": 0.08, "盈餘成長": 0.12, "ROE": 0.10, "評等": "🔵 成長潛力", "評估理由": "PE極低，合併效益顯現，官股金控穩健"},
        {"代碼": "1216", "名稱": "統一", "產業": "食品", "股價": 82.3, "PE": 20.76, "Forward PE": 19.0, "EPS": 3.96, "營收成長": 0.045, "盈餘成長": 0.08, "ROE": 0.149, "評等": "🔵 成長潛力", "評估理由": "食品龍頭，統一超穩健，多元佈局"},
        {"代碼": "2207", "名稱": "和泰車", "產業": "汽車", "股價": 780.0, "PE": 14.47, "Forward PE": 13.0, "EPS": 53.91, "營收成長": 0.12, "盈餘成長": 0.18, "ROE": 0.189, "評等": "🟢 建議持有", "評估理由": "Toyota/Lexus代理商，ROE近19%，車市龍頭"},
        {"代碼": "2618", "名稱": "長榮航", "產業": "航空", "股價": 41.85, "PE": 6.98, "Forward PE": 8.5, "EPS": 6.0, "營收成長": 0.15, "盈餘成長": 0.25, "ROE": 0.197, "評等": "🟢 建議持有", "評估理由": "PE僅7，貨運+客運雙動能，獲利強"},
        {"代碼": "2412", "名稱": "中華電", "產業": "電信", "股價": 125.5, "PE": 27.15, "Forward PE": 24.0, "EPS": 4.62, "營收成長": 0.02, "盈餘成長": 0.03, "ROE": 0.101, "評等": "🟡 觀望", "評估理由": "電信龍頭但成長性有限，殖利率約4%"},
        {"代碼": "2002", "名稱": "中鋼", "產業": "鋼鐵", "股價": 22.6, "PE": None, "Forward PE": 12.0, "EPS": -0.23, "營收成長": -0.08, "盈餘成長": -1.5, "ROE": -0.01, "評等": "🔴 風險", "評估理由": "鋼鐵景氣低迷，本業虧損，需觀察需求復甦"},
        {"代碼": "1109", "名稱": "亞泥", "產業": "水泥", "股價": 44.8, "PE": 14.9, "Forward PE": 13.5, "EPS": 3.01, "營收成長": 0.01, "盈餘成長": 0.02, "ROE": 0.037, "評等": "🔵 成長潛力", "評估理由": "水泥龍頭之一，殖利率高，景氣復甦受惠"},
        {"代碼": "1301", "名稱": "台塑", "產業": "石化", "股價": 56.2, "PE": None, "Forward PE": 18.0, "EPS": -1.82, "營收成長": -0.12, "盈餘成長": -2.0, "ROE": -0.031, "評等": "🔴 風險", "評估理由": "石化景氣差，原油波動影響獲利"},
        {"代碼": "1476", "名稱": "儒鴻", "產業": "紡織", "股價": 588.0, "PE": 16.61, "Forward PE": 15.0, "EPS": 35.4, "營收成長": 0.08, "盈餘成長": 0.12, "ROE": 0.188, "評等": "🔵 成長潛力", "評估理由": "機能布料龍頭，運動品牌訂單穩健"},
        {"代碼": "4743", "名稱": "合一", "產業": "生技", "股價": 350.0, "PE": None, "Forward PE": None, "EPS": -5.2, "營收成長": 0.25, "盈餘成長": None, "ROE": None, "評等": "🟡 觀望", "評估理由": "創新藥題材，營收成長但仍虧損"},
        {"代碼": "2345", "名稱": "智邦", "產業": "網通", "股價": 268.0, "PE": 46.62, "Forward PE": 28.0, "EPS": 5.75, "營收成長": 0.22, "盈餘成長": 0.35, "ROE": 0.559, "評等": "🔵 成長潛力", "評估理由": "ROE高達56%，AI伺服器網通需求爆發"},
        {"代碼": "6962", "名稱": "街口", "產業": "電子支付", "股價": 95.6, "PE": 12.9, "Forward PE": 25.0, "EPS": 7.41, "營收成長": 0.45, "盈餘成長": None, "ROE": 0.069, "評等": "🔵 成長潛力", "評估理由": "營收成長45%，電子支付滲透率提升"},
        {"代碼": "2707", "名稱": "晶華", "產業": "飯店", "股價": 215.0, "PE": 15.14, "Forward PE": 18.0, "EPS": 14.2, "營收成長": 0.18, "盈餘成長": 0.30, "ROE": 0.316, "評等": "🟢 建議持有", "評估理由": "ROE 31.6%，旅遊復甦，飯店龍頭"},
        {"代碼": "1229", "名稱": "聯華", "產業": "食品原料", "股價": 68.5, "PE": 16.15, "Forward PE": 15.0, "EPS": 4.24, "營收成長": 0.03, "盈餘成長": 0.05, "ROE": 0.073, "評等": "🟡 觀望", "評估理由": "食品原料穩健，但成長性普通"},
        {"代碼": "2912", "名稱": "永豐餘", "產業": "造紙", "股價": 38.2, "PE": 21.46, "Forward PE": 12.0, "EPS": 1.78, "營收成長": 0.05, "盈餘成長": 0.08, "ROE": 0.254, "評等": "🔵 成長潛力", "評估理由": "ROE 25.4%，造紙龍頭，獲利改善"},
    ]

stocks = load_stock_data()

# 自訂 CSS - 深色金屬風格
st.markdown("""
<style>
    /* 深色背景 */
    .stApp {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #e6edf3;
    }
    
    /* 標題樣式 */
    h1, h2, h3 {
        color: #58a6ff !important;
        font-family: 'Noto Sans TC', sans-serif;
    }
    
    /* 卡片容器 */
    .stock-card {
        background: linear-gradient(135deg, #21262d 0%, #30363d 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .stock-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(88, 166, 255, 0.15);
    }
    
    /* 評等標籤 */
    .rating-green { color: #3fb950; font-weight: bold; }
    .rating-blue { color: #58a6ff; font-weight: bold; }
    .rating-yellow { color: #d29922; font-weight: bold; }
    .rating-orange { color: #f0883e; font-weight: bold; }
    .rating-red { color: #f85149; font-weight: bold; }
    
    /* 產業標籤 */
    .industry-tag {
        background: #30363d;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        color: #8b949e;
    }
    
    /* 數據表格 */
    .data-table {
        width: 100%;
        border-collapse: collapse;
    }
    
    .data-table th {
        background: #21262d;
        color: #8b949e;
        padding: 12px;
        text-align: left;
    }
    
    .data-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #30363d;
    }
    
    .data-table tr:hover {
        background: #21262d;
    }
    
    /* 側邊欄 */
    .css-1d391kg {
        background: #161b22;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        color: #58a6ff;
    }
    
    /* 篩選下拉選單 */
    .stSelectbox label {
        color: #8b949e !important;
    }
    
    /* 區塊標題 */
    .section-header {
        border-bottom: 2px solid #30363d;
        padding-bottom: 8px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# 標題
st.title("📊 20檔產業龍頭深度分析報告")
st.markdown(f"**更新日期**: {datetime.now().strftime('%Y-%m-%d')}")

# 側邊欄 - 篩選功能
with st.sidebar:
    st.header("🎛️ 篩選功能")
    
    # 評等篩選
    rating_filter = st.multiselect(
        "評等篩選",
        ["🟢 建議持有", "🔵 成長潛力", "🟡 觀望", "🟠 留意", "🔴 風險"],
        default=["🟢 建議持有", "🔵 成長潛力", "🟡 觀望", "🟠 留意", "🔴 風險"]
    )
    
    # 產業篩選
    industries = sorted(list(set([s["產業"] for s in stocks])))
    industry_filter = st.multiselect(
        "產業篩選",
        industries,
        default=industries
    )
    
    st.markdown("---")
    st.markdown("### 📈 評等分布")
    
    # 評等統計
    rating_counts = {}
    for s in stocks:
        rating = s["評等"]
        rating_counts[rating] = rating_counts.get(rating, 0) + 1
    
    for rating, count in sorted(rating_counts.items(), key=lambda x: x[1], reverse=True):
        st.write(f"{rating} **{count}檔**")

# 篩選數據
filtered_stocks = [s for s in stocks if s["評等"] in rating_filter and s["產業"] in industry_filter]

# 建立 DataFrame 顯示
st.markdown("---")
st.markdown(f"### 📋 篩選結果: {len(filtered_stocks)} 檔股票")

# 創建顯示表格
for stock in filtered_stocks:
    # 解析評等
    rating = stock["評等"]
    rating_class = "rating-green" if "🟢" in rating else "rating-blue" if "🔵" in rating else "rating-yellow" if "🟡" in rating else "rating-orange" if "🟠" in rating else "rating-red"
    
    # 格式化數據
    pe_val = f"{stock['PE']:.2f}" if stock.get('PE') else "N/A"
    fwd_pe_val = f"{stock['Forward PE']:.2f}" if stock.get('Forward PE') else "N/A"
    roe_val = f"{stock['ROE']*100:.1f}%" if stock.get('ROE') else "N/A"
    rev_growth_val = f"{stock['營收成長']*100:.1f}%" if stock.get('營收成長') else "N/A"
    eps_growth_val = f"{stock['盈餘成長']*100:.1f}%" if stock.get('盈餘成長') else "N/A"
    
    # 卡片顯示
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 3])
        
        with col1:
            st.markdown(f"""
            <div class="stock-card">
                <h3 style="margin:0;color:#e6edf3;">{stock['代碼']} {stock['名稱']}</h3>
                <span class="industry-tag">{stock['產業']}</span>
                <br><br>
                <span class="{rating_class}" style="font-size:18px;">{rating}</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stock-card">
                <table class="data-table">
                    <tr><td><b>股價</b></td><td>${stock['股價']}</td></tr>
                    <tr><td><b>本益比</b></td><td>{pe_val}</td></tr>
                    <tr><td><b>預估本益比</b></td><td>{fwd_pe_val}</td></tr>
                    <tr><td><b>EPS</b></td><td>${stock['EPS']:.2f}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stock-card">
                <table class="data-table">
                    <tr><td><b>ROE</b></td><td>{roe_val}</td></tr>
                    <tr><td><b>營收成長</b></td><td>{rev_growth_val}</td></tr>
                    <tr><td><b>盈餘成長</b></td><td>{eps_growth_val}</td></tr>
                    <tr><td colspan="2"><b>評估理由</b></td></tr>
                    <tr><td colspan="2" style="color:#8b949e;font-size:13px;">{stock['評估理由']}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")

# 總結區塊
st.markdown("## 📊 投資建議總結")

# 分類顯示
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🟢 建議持有")
    for s in stocks:
        if "🟢" in s["評等"]:
            st.write(f"- **{s['代碼']} {s['名稱']}** ({s['產業']})")

with col2:
    st.markdown("### 🔵 成長潛力")
    for s in stocks:
        if "🔵" in s["評等"]:
            st.write(f"- **{s['代碼']} {s['名稱']}** ({s['產業']})")

with col3:
    st.markdown("### 🟡 觀望 / 🔴 風險")
    for s in stocks:
        if "🟡" in s["評等"] or "🔴" in s["評等"]:
            st.write(f"- **{s['代碼']} {s['名稱']}** ({s['產業']})")

# 頁腳
st.markdown("---")
st.markdown("*本報告僅供參考，不構成投資建議。投資前請自行評估風險。*")