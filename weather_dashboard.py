#!/usr/bin/env python3
"""
少爺專用 - 專業天氣儀表板 V5 Modern Grid ✨
使用方式: streamlit run weather_dashboard.py
"""

import streamlit as st
import plotly.graph_objects as go
import subprocess
import json
import time
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 頁面設定
st.set_page_config(
    page_title="少爺的天氣儀表板 🌤️",
    page_icon="🌤️",
    layout="wide"
)

# ===== 自訂 CSS：Modern Grid V5 =====
st.markdown("""
<style>
    /* ── Modern 字型與背景 ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&family=Noto+Sans+TC:wght@300;400;500;700&display=swap');

    :root {
        --bg-start: #0f0f1a;
        --bg-mid:   #1a1a2e;
        --bg-end:   #16213e;
        --glass-bg: rgba(30, 30, 50, 0.75);
        --glass-border: rgba(255, 255, 255, 0.1);
        --accent: #38bdf8;  /* 亮藍色 */
        --accent-warm: #f97316; /* 橙色 */
        --text-primary: #ffffff;
        --text-muted: rgba(255,255,255,0.65);
        --card-gradient: linear-gradient(145deg, rgba(30,30,50,0.9), rgba(15,15,30,0.95));
    }

    html, body, .stApp {
        background: linear-gradient(135deg, var(--bg-start) 0%, var(--bg-mid) 50%, var(--bg-end) 100%) !important;
        font-family: 'Inter', 'Noto Sans TC', 'PingFang TC', sans-serif !important;
        color: var(--text-primary) !important;
        min-height: 100vh;
    }

    /* ── Modern 頂部 Hero ── */
    .hero-title {
        text-align: center;
        padding: 1rem 0 0.5rem;
    }
    .hero-title h1 {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #38bdf8, #7dd3fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: 1px;
    }
    .hero-title .subtitle {
        color: var(--text-muted);
        font-size: 0.85rem;
        margin-top: 4px;
    }
    
    /* ── 資訊卡片網格 (6欄) ── */
    .info-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 12px;
        margin-bottom: 1rem;
    }
    @media (max-width: 1200px) {
        .info-grid { grid-template-columns: repeat(3, 1fr); }
    }
    @media (max-width: 768px) {
        .info-grid { grid-template-columns: repeat(2, 1fr); }
    }
    
    /* ── 横向滾動每小時預報 ── */
    .hourly-scroll {
        display: flex;
        gap: 12px;
        overflow-x: auto;
        padding: 12px 0;
        margin-bottom: 1rem;
        scrollbar-width: thin;
        scrollbar-color: rgba(56, 189, 248, 0.3) transparent;
    }
    .hourly-scroll::-webkit-scrollbar {
        height: 6px;
    }
    .hourly-scroll::-webkit-scrollbar-track {
        background: transparent;
    }
    .hourly-scroll::-webkit-scrollbar-thumb {
        background: rgba(56, 189, 248, 0.3);
        border-radius: 3px;
    }
    .hourly-card {
        flex: 0 0 auto;
        min-width: 80px;
        background: var(--card-gradient);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 1rem 0.8rem;
        text-align: center;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        transition: all 0.3s ease;
    }
    .hourly-card:hover {
        border-color: var(--accent);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(56, 189, 248, 0.2);
    }
    .hourly-card .hour-time {
        font-size: 0.75rem;
        color: var(--text-muted);
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .hourly-card .hour-icon {
        font-size: 1.8rem;
        margin-bottom: 0.4rem;
    }
    .hourly-card .hour-temp {
        font-size: 1.1rem;
        font-weight: 700;
        color: #fff;
    }
    
    /* ── 每週預報卡片網格 ── */
    .weekly-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 10px;
        margin-bottom: 1rem;
    }
    @media (max-width: 900px) {
        .weekly-grid { grid-template-columns: repeat(4, 1fr); }
    }
    @media (max-width: 600px) {
        .weekly-grid { grid-template-columns: repeat(2, 1fr); }
    }
    .weekly-card {
        background: var(--card-gradient);
        border: 1px solid var(--glass-border);
        border-radius: 14px;
        padding: 1rem 0.6rem;
        text-align: center;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        transition: all 0.3s ease;
    }
    .weekly-card:hover {
        border-color: var(--accent-warm);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(249, 115, 22, 0.15);
    }
    .weekly-card .day-name {
        font-size: 0.75rem;
        color: var(--text-muted);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    .weekly-card .day-icon {
        font-size: 2rem;
        margin-bottom: 0.4rem;
    }
    .weekly-card .day-temp {
        font-size: 1rem;
        font-weight: 700;
        color: #fff;
    }
    .weekly-card .day-rain {
        font-size: 0.7rem;
        color: #38bdf8;
        margin-top: 0.2rem;
    }

    /* ── 金屬質感膠囊導航列 (Pill Tabs) ── */
    .pill-tabs {
        display: flex;
        justify-content: center;
        gap: 8px;
        margin: 1.2rem 0;
    }
    .pill-tab {
        padding: 10px 32px;
        border-radius: 50px;
        border: 1px solid rgba(180, 160, 120, 0.4);
        background: linear-gradient(145deg, rgba(30,30,50,0.9), rgba(20,20,35,0.95));
        color: var(--text-muted);
        font-weight: 600;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        text-decoration: none;
        user-select: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .pill-tab:hover {
        border-color: rgba(201, 162, 39, 0.6);
        color: #e8e8e8;
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0,0,0,0.4), 0 0 20px rgba(201, 162, 39, 0.2);
    }
    .pill-tab.active {
        background: var(--gold-gradient);
        border-color: transparent;
        color: #1a1a2e;
        font-weight: 700;
        box-shadow: 0 6px 30px rgba(201, 162, 39, 0.5), 0 0 40px rgba(201, 162, 39, 0.3);
        transform: translateY(-2px);
    }

    /* ── 金屬質感卡片 ── */
    .glass-card {
        background: linear-gradient(145deg, rgba(30,30,50,0.8), rgba(20,20,35,0.9));
        border: 1px solid rgba(180, 160, 120, 0.4);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .glass-card:hover {
        transform: translateY(-4px) scale(1.01);
        border-color: rgba(201, 162, 39, 0.6);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5), 0 0 30px rgba(201, 162, 39, 0.2), inset 0 1px 0 rgba(255,255,255,0.15);
    }

    /* ── 金屬質感主天氣 Hero 卡片 ── */
    .weather-hero {
        text-align: center;
        padding: 2.5rem 2rem;
        background: linear-gradient(145deg, rgba(25,25,45,0.9), rgba(15,15,30,0.95));
        border: 2px solid transparent;
        border-radius: 24px;
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        box-shadow: 0 16px 64px rgba(0,0,0,0.5), 0 0 50px rgba(201, 162, 39, 0.1), inset 0 2px 0 rgba(255,255,255,0.1);
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .weather-hero::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(201, 162, 39, 0.8), transparent);
    }
    .weather-hero .big-emoji {
        font-size: 5rem;
        line-height: 1;
        filter: drop-shadow(0 0 20px rgba(201, 162, 39, 0.4));
    }
    .weather-hero .temp-display {
        font-size: 5rem;
        font-weight: 900;
        background: var(--gold-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 40px rgba(201, 162, 39, 0.6);
        line-height: 1;
        margin: 0.5rem 0;
        letter-spacing: 4px;
    }
    .weather-hero .desc-text {
        font-size: 1.5rem;
        font-weight: 600;
        color: #e8e8e8;
        letter-spacing: 2px;
    }
    .weather-hero .temp-range {
        font-size: 1.1rem;
        color: var(--text-muted);
        margin-top: 0.5rem;
    }

    /* ── 浮動動畫 ── */
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }

    /* ── Hero 天氣卡片 ── */
    .weather-hero {
        text-align: center;
        padding: 2rem 1.5rem;
        background: var(--card-gradient);
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        box-shadow: 0 16px 48px rgba(0,0,0,0.4);
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .weather-hero::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
    }
    .weather-hero .big-emoji {
        font-size: 5rem;
        line-height: 1;
        animation: float 3s ease-in-out infinite;
    }
    .weather-hero .temp-display {
        font-size: 4.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #38bdf8, #7dd3fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1;
        margin: 0.3rem 0;
        letter-spacing: 2px;
    }
    .weather-hero .desc-text {
        font-size: 1.4rem;
        font-weight: 500;
        color: rgba(255,255,255,0.9);
    }
    .weather-hero .temp-range {
        font-size: 1rem;
        color: var(--text-muted);
        margin-top: 0.4rem;
    }
    
    /* ── 數據指標卡 (6欄) ── */
    .info-card {
        background: var(--card-gradient);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 1.2rem 0.8rem;
        text-align: center;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    .info-card:hover {
        border-color: var(--accent);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(56, 189, 248, 0.2);
    }
    .info-card .info-emoji { font-size: 1.6rem; margin-bottom: 0.3rem; }
    .info-card .info-label {
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .info-card .info-value {
        font-size: 1.3rem;
        font-weight: 800;
        color: #fff;
    }
    .info-card .info-sub {
        font-size: 0.7rem;
        color: var(--text-muted);
        margin-top: 0.2rem;
    }
    
    /* ── 響應式斷點 ── */
    @media (max-width: 768px) {
        .hero-title h1 { font-size: 1.5rem; }
        .weather-hero { padding: 1.2rem; }
        .weather-hero .big-emoji { font-size: 3rem; }
        .weather-hero .temp-display { font-size: 2.8rem; }
        .info-grid { grid-template-columns: repeat(3, 1fr) !important; }
        .weekly-grid { grid-template-columns: repeat(4, 1fr) !important; }
    }
    @media (max-width: 480px) {
        .info-grid { grid-template-columns: repeat(2, 1fr) !important; }
        .weekly-grid { grid-template-columns: repeat(2, 1fr) !important; }
    }
    
    /* ── 浮動動畫 ── */
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
    }
    @keyframes float-slow {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
    }
    
    /* ── 區塊標題 ── */
    .section-title {
        font-size: 1rem;
        font-weight: 700;
        color: rgba(255,255,255,0.9);
        margin-bottom: 0.8rem;
        letter-spacing: 0.5px;
    }
    .section-title span {
        color: var(--accent);
    }
    
    /* ── 側邊欄 Modern 風格 ── */
    .css-1d391kg {
        background: rgba(20, 20, 35, 0.95) !important;
    }
    .st-emotion-cache-1wbqy4d {
        background: var(--card-gradient) !important;
    }

    /* ── AQI 彩虹進度條 ── */
    .aqi-section {
        margin-bottom: 1.5rem;
    }
    .aqi-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 0.8rem;
    }
    .aqi-badge {
        background: linear-gradient(135deg, #6C63FF, #a78bfa);
        border-radius: 50px;
        padding: 4px 18px;
        font-size: 0.85rem;
        font-weight: 700;
        color: white;
        white-space: nowrap;
    }
    .aqi-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: rgba(255,255,255,0.9);
    }
    .aqi-status-text {
        font-size: 0.9rem;
        color: var(--text-muted);
    }
    .rainbow-bar-container {
        background: rgba(255,255,255,0.1);
        border-radius: 50px;
        height: 18px;
        overflow: hidden;
        position: relative;
        margin-bottom: 0.5rem;
    }
    .rainbow-bar {
        height: 100%;
        border-radius: 50px;
        background: linear-gradient(to right,
            #00e400 0%, #00e400 20%,
            #ffff00 20%, #ff7e00 40%,
            #ff0000 40%, #ff7e00 60%,
            #8b5cf6 60%, #8b5cf6 80%,
            #7e0023 80%, #7e0023 100%
        );
        position: relative;
        transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .rainbow-bar::after {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: inherit;
        filter: blur(4px);
        opacity: 0.5;
    }
    .aqi-marker {
        position: absolute;
        top: -4px;
        width: 4px;
        height: 26px;
        background: white;
        border-radius: 2px;
        box-shadow: 0 0 8px rgba(255,255,255,0.8);
        transition: left 1.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .aqi-labels {
        display: flex;
        justify-content: space-between;
        font-size: 0.7rem;
        color: var(--text-muted);
        font-weight: 600;
        padding: 0 2px;
    }
    .aqi-detail-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin-top: 0.8rem;
    }
    @media (max-width: 600px) {
        .aqi-detail-grid { grid-template-columns: repeat(2, 1fr); }
    }
    .aqi-detail-card {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 0.8rem;
        text-align: center;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }
    .aqi-detail-card .ad-label {
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .aqi-detail-card .ad-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #fff;
        margin-top: 2px;
    }

    /* ── 建議卡片 ── */
    .suggestions {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 10px;
        margin-bottom: 1.5rem;
    }
    .sugg-card {
        border-radius: 14px;
        padding: 0.9rem 1.1rem;
        font-size: 0.88rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }
    .sugg-card.good {
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.4);
        color: #86efac;
    }
    .sugg-card.warn {
        background: rgba(251, 191, 36, 0.15);
        border: 1px solid rgba(251, 191, 36, 0.4);
        color: #fde68a;
    }
    .sugg-card.danger {
        background: rgba(248, 113, 113, 0.15);
        border: 1px solid rgba(248, 113, 113, 0.4);
        color: #fca5a5;
    }
    .sugg-card .sugg-emoji { font-size: 1.4rem; }

    /* ── 側邊欄美化 ── */
    .stSidebar {
        background: rgba(15, 12, 41, 0.7) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid var(--glass-border);
    }
    .stSidebar .stSelectbox label,
    .stSidebar .stSlider label,
    .stSidebar .stCheckbox label {
        color: rgba(255,255,255,0.7) !important;
    }

    /* ── Streamlit 原生元素覆寫 ── */
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: white !important;
    }
    .stSlider > div > div > div {
        background: rgba(255,255,255,0.1) !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 50px !important;
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: rgba(255,255,255,0.6) !important;
        padding: 6px 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6C63FF, #a78bfa) !important;
        border-color: transparent !important;
        color: white !important;
        box-shadow: 0 4px 16px rgba(108,99,255,0.4) !important;
    }

    /* ── Plotly 圖表美化 ── */
    .js-plotly-plot .plotly .modebar { opacity: 0.3; }

    /* ── 淡入動畫 ── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fadeInUp 0.6s ease forwards; }
    .fade-in-delay-1 { animation: fadeInUp 0.6s 0.1s ease forwards; opacity: 0; }
    .fade-in-delay-2 { animation: fadeInUp 0.6s 0.2s ease forwards; opacity: 0; }
    .fade-in-delay-3 { animation: fadeInUp 0.6s 0.3s ease forwards; opacity: 0; }

    /* ── 報告時間 ── */
    .report-time {
        text-align: center;
        color: var(--text-muted);
        font-size: 0.8rem;
        margin-bottom: 1rem;
    }

    /* ── Footer ── */
    .footer {
        text-align: center;
        color: rgba(255,255,255,0.3);
        font-size: 0.75rem;
        padding: 1.5rem 0 0.5rem;
        border-top: 1px solid rgba(255,255,255,0.06);
        margin-top: 1rem;
    }

    /* ── 隱藏預設元素的技巧 ── */
    .starkdown hr { display: none; }
    section[data-testid="stSidebar"] { border-right: none; }
</style>
""", unsafe_allow_html=True)

# ===== 地點設定 =====
TAIWAN_LOCATIONS = {
    '新竹寶山': {'lat': 24.75, 'lon': 121.05},
    '苗栗': {'lat': 24.560, 'lon': 120.821},
    '台中南屯': {'lat': 24.125, 'lon': 120.625},
    '沙鹿': {'lat': 24.257, 'lon': 120.566},
    '龍井': {'lat': 24.192, 'lon': 120.545},
    '彰化': {'lat': 24.081, 'lon': 120.562},
    '埔里': {'lat': 23.968, 'lon': 120.967},
    '日月潭': {'lat': 23.881, 'lon': 120.908},
}

JAPAN_LOCATIONS = {
    '東京': {'lat': 35.676, 'lon': 139.650},
    '名古屋': {'lat': 35.181, 'lon': 136.906},
    '大阪': {'lat': 34.693, 'lon': 135.502},
    '京都': {'lat': 35.011, 'lon': 135.768},
    '沖繩_系滿': {'lat': 26.255, 'lon': 127.702},
    '沖繩_豐見': {'lat': 26.168, 'lon': 127.683},
    '沖繩_那霸': {'lat': 26.212, 'lon': 127.681},
    '沖繩_恩納': {'lat': 26.591, 'lon': 127.862},
    '沖繩_名護': {'lat': 26.591, 'lon': 127.978},
}

ALL_LOCATIONS = {**TAIWAN_LOCATIONS, **JAPAN_LOCATIONS}
TAIWAN_AQI_STATIONS = {
    '新竹寶山': '新竹市', '苗栗': '苗栗', '台中南屯': '台中',
    '沙鹿': '沙鹿', '龍井': '龍井', '彰化': '彰化', '埔里': '埔里', '日月潭': '日月潭',
}
DEFAULT_LOCATION = '台中南屯'

# ===== 動態天氣主題 =====
def get_weather_theme(code):
    """根據天氣代碼返回主題配色"""
    themes = {
        'sunny': {  # 晴朗 0,1
            'bg_start': '#1e3a5f', 'bg_mid': '#2563eb', 'bg_end': '#0f172a',
            'accent': '#fbbf24', 'text': '#ffffff'
        },
        'cloudy': {  # 多雲 2,3
            'bg_start': '#334155', 'bg_mid': '#475569', 'bg_end': '#1e293b',
            'accent': '#94a3b8', 'text': '#e2e8f0'
        },
        'rainy': {  # 雨天 51,53,55,61,63,65,80,81,82
            'bg_start': '#1e293b', 'bg_mid': '#334155', 'bg_end': '#0f172a',
            'accent': '#38bdf8', 'text': '#e0f2fe'
        },
        'stormy': {  # 雷雨 95,96,99
            'bg_start': '#0f0a1a', 'bg_mid': '#1e1033', 'bg_end': '#0a0612',
            'accent': '#fbbf24', 'text': '#fef3c7'
        },
        'snowy': {  # 雪天 71,73,75
            'bg_start': '#1e293b', 'bg_mid': '#64748b', 'bg_end': '#f8fafc',
            'accent': '#e2e8f0', 'text': '#1e293b'
        },
        'foggy': {  # 霧 45,48
            'bg_start': '#374151', 'bg_mid': '#6b7280', 'bg_end': '#1f2937',
            'accent': '#d1d5db', 'text': '#f3f4f6'
        },
        'default': {  # 預設
            'bg_start': '#0f0c29', 'bg_mid': '#302b63', 'bg_end': '#24243e',
            'accent': '#6C63FF', 'text': '#ffffff'
        }
    }
    if code in [0, 1]:
        return themes['sunny']
    elif code in [2, 3]:
        return themes['cloudy']
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return themes['rainy']
    elif code in [95, 96, 99]:
        return themes['stormy']
    elif code in [71, 73, 75]:
        return themes['snowy']
    elif code in [45, 48]:
        return themes['foggy']
    else:
        return themes['default']


# ===== API 函式 =====
def get_weather_data(lat, lon, retries=3, delay=2):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,weather_code,apparent_temperature&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia/Taipei&forecast_days=3"
    for attempt in range(retries):
        try:
            result = subprocess.run(['curl', '-s', '--max-time', '15', url], capture_output=True, text=True, timeout=20)
            raw = result.stdout.strip()
            if not raw:
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                return None
            data = json.loads(raw)
            if 'hourly' not in data or 'daily' not in data:
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                return None
            return data
        except json.JSONDecodeError:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            return None
    return None

def get_taiwan_aqi(city_name):
    try:
        url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Authorization': 'a75a9b46-160f-4724-b3a1-446633472310'
        }
        params = {'offset': '0', 'limit': '500'}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            text = response.text.strip()
            if not text: return None
            try:
                data = response.json()
                records = data.get('records', [])
                if not records: return None
                for record in records:
                    if city_name in record.get('SiteName', '') or city_name in record.get('County', ''):
                        return record
                return records[0] if records else None
            except json.JSONDecodeError:
                return None
    except: return None

def get_waqi_aqi(lat, lon):
    try:
        url = f"https://api.waqi.info/feed/geo:{lat};{lon}/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        params = {'token': 'f67a217b6e937a17498b19a39261aa9c90c6bbda'}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                return data.get('data')
        return None
    except: return None

def get_aqi_status(aqi):
    try:
        aqi_val = int(aqi) if aqi else None
        if aqi_val is None: return '未知', '⚪', 'gray', 0
        if aqi_val <= 50:   return '良好', '🟢', '#00e400', aqi_val
        elif aqi_val <= 100: return '中等', '🟡', '#ffff00', aqi_val
        elif aqi_val <= 150: return '對敏感族群不健康', '🟠', '#ff7e00', aqi_val
        elif aqi_val <= 200: return '不健康', '🔴', '#ff0000', aqi_val
        elif aqi_val <= 300: return '非常不健康', '🟣', '#8b5cf6', aqi_val
        else:                return '危害', '❤️‍🔥', '#7e0023', aqi_val
    except:
        return '未知', '⚪', 'gray', 0

def get_weather_icon(code):
    """SVG icon 替代 emoji（統一視覺語言）"""
    icons = {
        0: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#fbbf24" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',  # ☀️ sun
        1: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#fbbf24" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',  # 🌤️ sun+cloud
        2: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#94a3b8" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>',  # ⛅ cloud
        3: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#94a3b8" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>',  # ☁️ cloud
        45: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#cbd5e1" stroke-width="2"><path d="M3 10h18M7 16h10M5 6h14"/></svg>',  # 🌫️ fog
        48: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#cbd5e1" stroke-width="2"><path d="M3 10h18M7 16h10M5 6h14"/></svg>',  # fog
        51: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#38bdf8" stroke-width="2"><path d="M16 13v8M8 13v8M12 15v8"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>',  # 🌧️ drizzle
        53: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#38bdf8" stroke-width="2"><path d="M16 13v8M8 13v8M12 15v8"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>',  # drizzle
        55: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#38bdf8" stroke-width="2"><path d="M16 13v8M8 13v8M12 15v8"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>',  # drizzle
        61: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#38bdf8" stroke-width="2"><path d="M16 13v8M8 13v8M12 15v8"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>',  # 🌧️ rain
        63: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#38bdf8" stroke-width="2"><path d="M16 13v8M8 13v8M12 15v8"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>',  # rain
        65: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#38bdf8" stroke-width="2"><path d="M16 13v8M8 13v8M12 15v8"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>',  # heavy rain
        71: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#e2e8f0" stroke-width="2"><path d="M12 13v8M8 13v8M16 13v8"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>',  # 🌨️ snow
        73: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#e2e8f0" stroke-width="2"><path d="M12 13v8M8 13v8M16 13v8"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>',  # snow
        75: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#e2e8f0" stroke-width="2"><path d="M12 13v8M8 13v8M16 13v8"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>',  # heavy snow
        80: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#38bdf8" stroke-width="2"><path d="M12 14v6M8 14v6"/><circle cx="12" cy="8" r="4"/></svg>',  # 🌦️ showers
        81: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#38bdf8" stroke-width="2"><path d="M12 14v6M8 14v6"/><circle cx="12" cy="8" r="4"/></svg>',  # showers
        82: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#38bdf8" stroke-width="2"><path d="M12 14v6M8 14v6"/><circle cx="12" cy="8" r="4"/></svg>',  # heavy showers
        95: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#fbbf24" stroke-width="2"><path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/><path d="M13 11l-4 6h6l-4 6"/></svg>',  # ⛈️ thunderstorm
        96: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#fbbf24" stroke-width="2"><path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/><path d="M13 11l-4 6h6l-4 6"/></svg>',  # thunderstorm
        99: '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#fbbf24" stroke-width="2"><path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/><path d="M13 11l-4 6h6l-4 6"/></svg>',  # thunderstorm severe
    }
    return icons.get(code, '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#94a3b8" stroke-width="2"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>')  # 🌡️ default

def get_weather_desc(code):
    codes = {
        0: '晴朗', 1: '晴時多雲', 2: '多雲', 3: '陰天',
        45: '霧', 48: '霧',
        51: '小雨', 53: '小雨', 55: '小雨',
        61: '小雨', 63: '中雨', 65: '大雨',
        71: '小雪', 73: '中雪', 75: '大雪',
        80: '小陣雨', 81: '中陣雨', 82: '大陣雨',
        95: '雷陣雨', 96: '雷陣雨', 99: '強雷雨'
    }
    return codes.get(code, '未知')

def get_wind_level(speed):
    if speed < 1:   return '無風'
    elif speed < 6:  return '輕風'
    elif speed < 12: return '微風'
    elif speed < 20: return '和風'
    elif speed < 29: return '清風'
    elif speed < 39: return '強風'
    elif speed < 50: return '疾風'
    elif speed < 62: return '大風'
    else:            return '颶風'

def get_wind_emoji(speed):
    if speed < 6:   return '🍃'
    elif speed < 20: return '🌬️'
    elif speed < 39: return '💨'
    else:            return '🌀'


# ===== AQI 彩虹進度條 HTML =====
def render_aqi_bar(aqi_val, aqi_max=300):
    pct = min(aqi_val / aqi_max * 100, 100)
    status, emoji, color, _ = get_aqi_status(aqi_val)
    marker_left = pct
    return f"""
    <div class="aqi-section">
        <div class="aqi-header">
            <span class="aqi-badge">{emoji} AQI {aqi_val}</span>
            <span class="aqi-title">空氣品質</span>
            <span class="aqi-status-text">— {status}</span>
        </div>
        <div class="rainbow-bar-container">
            <div class="rainbow-bar" style="width: {pct}%"></div>
            <div class="aqi-marker" style="left: {marker_left}%"></div>
        </div>
        <div class="aqi-labels">
            <span>0</span><span>50</span><span>100</span><span>150</span><span>200</span><span>300</span>
        </div>
    </div>
    """

# ===== 主程式 =====
def main():
    VERSION = "5.0"

    # ── 初始化 session_state ──
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "domestic"
    if 'domestic_location' not in st.session_state:
        st.session_state.domestic_location = DEFAULT_LOCATION
    if 'international_location' not in st.session_state:
        st.session_state.international_location = list(JAPAN_LOCATIONS.keys())[0]
    if 'selected_region' not in st.session_state:
        st.session_state.selected_region = "domestic"

    now_str = datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y年%m月%d日 %H:%M')

    # ── 側邊欄 ──
    with st.sidebar:
        st.markdown("### 🌤️ 少爺的天氣")
        st.markdown(f"**V{VERSION}** | {datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y-%m-%d')}")
        st.markdown("---")

        # 區域切換（按鈕樣式）
        st.markdown("### 🗺️ 選擇區域")
        col_dom, col_jpn = st.columns(2)
        with col_dom:
            if st.button("🇹🇼 國內", use_container_width=True,
                         type="primary" if st.session_state.selected_region == "domestic" else "secondary"):
                st.session_state.selected_region = "domestic"
                st.rerun()
        with col_jpn:
            if st.button("🇯🇵 日本", use_container_width=True,
                         type="primary" if st.session_state.selected_region == "international" else "secondary"):
                st.session_state.selected_region = "international"
                st.rerun()

        st.markdown("---")

        if st.session_state.selected_region == "domestic":
            selected_location = st.selectbox(
                "📍 選擇地點（台灣）",
                list(TAIWAN_LOCATIONS.keys()),
                index=list(TAIWAN_LOCATIONS.keys()).index(st.session_state.domestic_location)
                if st.session_state.domestic_location in TAIWAN_LOCATIONS else 0
            )
            st.session_state.domestic_location = selected_location
        else:
            selected_location = st.selectbox(
                "📍 選擇地點（日本）",
                list(JAPAN_LOCATIONS.keys()),
                index=list(JAPAN_LOCATIONS.keys()).index(st.session_state.international_location)
                if st.session_state.international_location in JAPAN_LOCATIONS else 0
            )
            st.session_state.international_location = selected_location

        days_to_show = st.slider("📅 顯示天數", 1, 3, 2)
        show_aqi = st.checkbox("🌬️ 顯示空氣品質", value=True)
        show_charts = st.checkbox("📈 顯示圖表", value=True)

        st.markdown("---")
        st.markdown("**📊 資料來源**")
        st.caption("- Open-Meteo（天氣）")
        st.caption("- 環保署 / WAQI（AQI）")

    is_domestic = selected_location in TAIWAN_LOCATIONS

    # ── 動態主題注入 ──
    # 根據選擇城市的天氣動態調整主題
    main_data = get_weather_data(
        ALL_LOCATIONS[selected_location]['lat'],
        ALL_LOCATIONS[selected_location]['lon']
    )
    main_theme_code = 0
    if main_data and 'hourly' in main_data:
        main_theme_code = main_data['hourly']['weather_code'][0]
    theme = get_weather_theme(main_theme_code)
    
    # 注入動態 CSS
    st.markdown(f"""
    <style>
        :root {{
            --bg-start: {theme['bg_start']};
            --bg-mid: {theme['bg_mid']};
            --bg-end: {theme['bg_end']};
            --accent: {theme['accent']};
            --text-primary: {theme['text']};
        }}
        .stApp {{
            background: linear-gradient(135deg, {theme['bg_start']} 0%, {theme['bg_mid']} 50%, {theme['bg_end']} 100%) !important;
        }}
        .hero-title h1 {{
            background: linear-gradient(135deg, {theme['accent']}, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .weather-hero {{
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 12px 48px rgba(0,0,0,0.4), 0 0 60px {theme['accent']}22;
        }}
    </style>
    """, unsafe_allow_html=True)

    # ── 頂部抬頭 ──
    st.markdown(f"""
    <div class="hero-title">
        <h1>🌦️ 天氣概覽</h1>
        <div class="subtitle">⏰ 報告時間：{now_str} &nbsp;|&nbsp; V{VERSION} ✨</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 雙城市 Hero 卡片（新竹寶山 ⭐ + 台中南屯 ⭐）─
    PRIMARY_CITIES = ['新竹寶山', '台中南屯']
    hero_cols = st.columns(2)
    hero_data_list = []
    
    for idx, city_name in enumerate(PRIMARY_CITIES):
        city_data = get_weather_data(
            ALL_LOCATIONS[city_name]['lat'],
            ALL_LOCATIONS[city_name]['lon']
        )
        hero_data_list.append((city_name, city_data))
    
    for idx, (city_name, city_data) in enumerate(hero_data_list):
        with hero_cols[idx]:
            if city_data and 'hourly' in city_data and 'daily' in city_data:
                daily = city_data['daily']
                hourly = city_data['hourly']
                today_max = daily['temperature_2m_max'][0]
                today_min = daily['temperature_2m_min'][0]
                today_code = hourly['weather_code'][0]
                today_icon = get_weather_icon(today_code)
                today_desc = get_weather_desc(today_code)
                today_feels = hourly['apparent_temperature'][0]
                
                st.markdown(f"""
                <div class="weather-hero fade-in" style="padding:1.5rem;">
                    <div style="font-size:0.9rem;color:var(--text-muted);margin-bottom:0.5rem;">⭐ {city_name}</div>
                    <div class="big-emoji" style="font-size:4rem;">{today_icon}</div>
                    <div class="temp-display" style="font-size:3rem;">{today_max:.0f}°</div>
                    <div class="desc-text">{today_desc}</div>
                    <div class="temp-range">體感 {today_feels:.0f}° · {today_min:.0f}°</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="weather-hero fade-in" style="padding:1.5rem;">
                    <div style="font-size:0.9rem;color:var(--text-muted);margin-bottom:0.5rem;">⭐ {city_name}</div>
                    <div class="big-emoji" style="font-size:4rem;">🌡️</div>
                    <div class="temp-display" style="font-size:3rem;">--</div>
                    <div class="desc-text">無法取得資料</div>
                </div>
                """, unsafe_allow_html=True)

    # ── 當前選擇城市資料 ──
    st.markdown("---")
    st.markdown(f"### 📍 {selected_location} 詳細天氣")
    
    # ── 取得資料 ──
    data = get_weather_data(
        ALL_LOCATIONS[selected_location]['lat'],
        ALL_LOCATIONS[selected_location]['lon']
    )

    # AQI
    aqi_data = None
    if show_aqi:
        if is_domestic:
            city = TAIWAN_AQI_STATIONS.get(selected_location, selected_location)
            aqi_data = get_taiwan_aqi(city)
            if aqi_data is None:
                lat, lon = ALL_LOCATIONS[selected_location]['lat'], ALL_LOCATIONS[selected_location]['lon']
                aqi_data = get_waqi_aqi(lat, lon)
        else:
            lat, lon = ALL_LOCATIONS[selected_location]['lat'], ALL_LOCATIONS[selected_location]['lon']
            aqi_data = get_waqi_aqi(lat, lon)

    if data and 'hourly' in data and 'daily' in data:
        hourly = data['hourly']
        daily = data['daily']
    else:
        st.error("⚠️ 無法取得天氣資料（API 瞬斷或超時），請稍後再試。")
        st.stop()

        # ── 今日概覽 ──
        today_max    = daily['temperature_2m_max'][0]
        today_min    = daily['temperature_2m_min'][0]
        today_rain   = daily['precipitation_probability_max'][0]
        today_code   = hourly['weather_code'][0]
        today_icon   = get_weather_icon(today_code)
        today_desc   = get_weather_desc(today_code)
        today_feels  = hourly['apparent_temperature'][0]
        today_humid  = hourly['relative_humidity_2m'][0]
        today_wind   = hourly['wind_speed_10m'][0]

        # 明天
        tomorrow_max  = daily['temperature_2m_max'][1]
        tomorrow_min  = daily['temperature_2m_min'][1]
        tomorrow_rain = daily['precipitation_probability_max'][1]
        tomorrow_code = hourly['weather_code'][24]
        tomorrow_icon = get_weather_icon(tomorrow_code)
        tomorrow_desc = get_weather_desc(tomorrow_code)

        # 後天
        day3_max  = daily['temperature_2m_max'][2] if len(daily['temperature_2m_max']) > 2 else None
        day3_min  = daily['temperature_2m_min'][2] if len(daily['temperature_2m_min']) > 2 else None
        day3_rain = daily['precipitation_probability_max'][2] if len(daily['precipitation_probability_max']) > 2 else None
        day3_code = hourly['weather_code'][48] if len(hourly['weather_code']) > 48 else 0
        day3_icon = get_weather_icon(day3_code)
        day3_desc = get_weather_desc(day3_code)

        avg_wind = int(sum(hourly['wind_speed_10m'][:24]) / 24)

        # ── 主天氣 Hero 卡片 ──
        st.markdown(f"""
        <div class="weather-hero fade-in">
            <div class="big-emoji">{today_icon}</div>
            <div class="temp-display">{today_max:.0f}°</div>
            <div class="desc-text">{today_desc}</div>
            <div class="temp-range">體感 {today_feels:.0f}° · 今 {today_min:.0f}° / 明 {tomorrow_min:.0f}°</div>
        </div>
        """, unsafe_allow_html=True)

        # ── 每小時橫向滾動預報 ──
        st.markdown('<p class="section-title">⏰ <span>逐時預報</span></p>', unsafe_allow_html=True)
        hourly_html = '<div class="hourly-scroll">'
        current_hour = datetime.now(ZoneInfo('Asia/Taipei')).hour
        for i in range(24):
            idx = i
            if idx >= len(hourly['time']):
                idx = i % len(hourly['time'])
            h_time = hourly['time'][idx]
            h_code = hourly['weather_code'][idx]
            h_temp = hourly['temperature_2m'][idx]
            h_icon = get_weather_icon(h_code)
            hour_label = datetime.fromisoformat(h_time).strftime('%H:00') if isinstance(h_time, str) else h_time.strftime('%H:00')
            hourly_html += f"""
            <div class="hourly-card">
                <div class="hour-time">{hour_label}</div>
                <div class="hour-icon">{h_icon}</div>
                <div class="hour-temp">{h_temp:.0f}°</div>
            </div>"""
        hourly_html += '</div>'
        st.markdown(hourly_html, unsafe_allow_html=True)

        # ── 六宮格資訊卡 ──
        info_items = [
            ('💧', '濕度', f'{today_humid:.0f}%', '相對濕度'),
            ('🌡️', '體感', f'{today_feels:.0f}°C', today_desc),
            ('💨', '風速', f'{today_wind:.0f}', get_wind_level(today_wind)),
            ('☂️', '降雨機率', f'{today_rain}%', '今日'),
            ('🌅', '紫外線', '中等', 'UV Index'),
            ('⏱️', '氣壓', '正常', 'hPa'),
        ]
        ig = '<div class="info-grid">'
        for emoji, label, value, sub in info_items:
            ig += f"""
            <div class="info-card">
                <div class="info-emoji">{emoji}</div>
                <div class="info-label">{label}</div>
                <div class="info-value">{value}</div>
                <div class="info-sub">{sub}</div>
            </div>"""
        ig += '</div>'
        st.markdown(ig, unsafe_allow_html=True)

        # ── 每週預報卡片 (7天) ──
        st.markdown('<p class="section-title">📅 <span>一週天氣</span></p>', unsafe_allow_html=True)
        weekly_html = '<div class="weekly-grid">'
        day_names = ['週日', '週一', '週二', '週三', '週四', '週五', '週六']
        today_weekday = datetime.now(ZoneInfo('Asia/Taipei')).weekday()
        for i in range(7):
            if i < len(daily['temperature_2m_max']):
                w_max = daily['temperature_2m_max'][i]
                w_min = daily['temperature_2m_min'][i]
                w_rain = daily['precipitation_probability_max'][i] if i < len(daily['precipitation_probability_max']) else 0
                w_code = hourly['weather_code'][i*24] if i*24 < len(hourly['weather_code']) else 0
                w_icon = get_weather_icon(w_code)
                w_day = day_names[(today_weekday + i) % 7]
                rain_emoji = "☂️" if w_rain and w_rain > 50 else ("🌂" if w_rain else "☀️")
                weekly_html += f"""
                <div class="weekly-card">
                    <div class="day-name">{w_day}</div>
                    <div class="day-icon">{w_icon}</div>
                    <div class="day-temp">{w_min:.0f}° / {w_max:.0f}°</div>
                    <div class="day-rain">{rain_emoji} {w_rain if w_rain else 0}%</div>
                </div>"""
        weekly_html += '</div>'
        st.markdown(weekly_html, unsafe_allow_html=True)

        # ── AQI 彩虹進度條 ──
        if show_aqi and aqi_data:
            if isinstance(aqi_data, dict) and 'AQI' in aqi_data:
                aqi_val = aqi_data.get('AQI', 'N/A')
                pm25 = aqi_data.get('PM2.5', 'N/A')
                pm10 = aqi_data.get('PM10', 'N/A')
                o3   = aqi_data.get('O3', 'N/A')
                no2  = aqi_data.get('NO2', 'N/A')
                try: aqi_num = int(aqi_val)
                except: aqi_num = 0
                detail_items = [
                    ('PM2.5', f'{pm25} μg/m³'),
                    ('PM10',  f'{pm10} μg/m³'),
                    ('O₃',    f'{o3} ppb'),
                    ('NO₂',   f'{no2} ppb'),
                ]
            elif isinstance(aqi_data, dict):
                aqi_val = aqi_data.get('aqi', 'N/A')
                iaqi    = aqi_data.get('iaqi', {}) or {}
                pm25_v  = iaqi.get('pm25', {}).get('v', 'N/A') if isinstance(iaqi, dict) else 'N/A'
                pm10_v  = iaqi.get('pm10', {}).get('v', 'N/A') if isinstance(iaqi, dict) else 'N/A'
                try: aqi_num = int(aqi_val)
                except: aqi_num = 0
                detail_items = [
                    ('PM2.5', f'{pm25_v} μg/m³'),
                    ('PM10',  f'{pm10_v} μg/m³'),
                    ('資料來源', 'WAQI'),
                    ('AQI',   f'{aqi_val}'),
                ]
            else:
                aqi_num  = 0
                aqi_val  = 'N/A'
                detail_items = [('AQI', 'N/A')] * 4

            if isinstance(aqi_val, str) and aqi_val.isdigit():
                aqi_val_int = int(aqi_val)
            elif isinstance(aqi_val, (int, float)):
                aqi_val_int = int(aqi_val)
            else:
                aqi_val_int = 0

            aqi_bar_html = render_aqi_bar(aqi_val_int)

            dg = '<div class="aqi-detail-grid">'
            for label, val in detail_items:
                dg += f"""
                <div class="aqi-detail-card">
                    <div class="ad-label">{label}</div>
                    <div class="ad-value">{val}</div>
                </div>"""
            dg += '</div>'

            st.markdown(aqi_bar_html + dg, unsafe_allow_html=True)

        # ── 出門建議 ──
        suggestions = []
        if tomorrow_rain > 60:
            suggestions.append(('danger', '☂️', f'高降雨機率 {tomorrow_rain}%，建議攜帶雨具'))
        elif tomorrow_rain > 30:
            suggestions.append(('warn', '🌂', f'降雨機率 {tomorrow_rain}%，建議帶傘'))
        if avg_wind > 25:
            suggestions.append(('warn', '💨', f'風速較強 {avg_wind} km/h（{get_wind_level(avg_wind)}），注意防風'))
        if tomorrow_max > 32:
            suggestions.append(('danger', '🥵', f'高溫炎熱 {tomorrow_max:.0f}°C，請注意防曬'))
        if tomorrow_min < 18:
            suggestions.append(('warn', '🧥', f'早晚溫差大 {tomorrow_min:.0f}°C，建議帶外套'))
        if tomorrow_code in [95, 96, 99]:
            suggestions.append(('danger', '⛈️', '可能有雷雨，請留意天氣變化'))

        if show_aqi and aqi_data:
            try:
                if isinstance(aqi_data, dict) and 'AQI' in aqi_data:
                    aqi_check = int(aqi_data.get('AQI', 0))
                elif isinstance(aqi_data, dict):
                    aqi_check = int(aqi_data.get('aqi', 0))
                else:
                    aqi_check = 0
                if aqi_check > 150:
                    suggestions.append(('danger', '🌫️', f'空品不佳 AQI:{aqi_check}，建議戴口罩'))
                elif aqi_check > 100:
                    suggestions.append(('warn', '🫁', f'空品敏感注意 AQI:{aqi_check}'))
            except: pass

        if not suggestions:
            suggestions.append(('good', '✅', '天氣良好，出門沒問題！'))

        sg = '<div class="suggestions">'
        for level, emoji, text in suggestions:
            sg += f'<div class="sugg-card {level}"><span class="sugg-emoji">{emoji}</span><span>{text}</span></div>'
        sg += '</div>'
        st.markdown(sg, unsafe_allow_html=True)

        # ── 圖表區 ──
        if show_charts:
            hours  = min(days_to_show * 24, 48)
            times  = hourly['time'][:hours]
            temps  = hourly['temperature_2m'][:hours]
            feels  = hourly['apparent_temperature'][:hours]
            humid  = hourly['relative_humidity_2m'][:hours]
            rain_p = hourly['precipitation_probability'][:hours]
            wind   = hourly['wind_speed_10m'][:hours]

            # 溫度圖
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(
                x=times, y=temps, mode='lines+markers', name='氣溫',
                line=dict(color='#fbbf24', width=3), marker=dict(size=6, color='#fbbf24')
            ))
            fig_temp.add_trace(go.Scatter(
                x=times, y=feels, mode='lines+markers', name='體感溫度',
                line=dict(color='#f87171', width=2, dash='dash'), marker=dict(size=5, color='#f87171')
            ))
            fig_temp.update_layout(
                title=dict(text='🌡️ 溫度趨勢', font=dict(color='white', size=15)),
                xaxis=dict(title=dict(text='時間', font=dict(color='rgba(255,255,255,0.6)')),
                           showgrid=False, color='rgba(255,255,255,0.3)'),
                yaxis=dict(title=dict(text='°C', font=dict(color='rgba(255,255,255,0.6)')),
                           showgrid=True, gridcolor='rgba(255,255,255,0.06)', color='rgba(255,255,255,0.3)'),
                height=320, template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(255,255,255,0.8)'),
                hovermode='x unified',
                legend=dict(font=dict(color='rgba(255,255,255,0.7)'), bgcolor='rgba(0,0,0,0)'),
                autosize=True
            )

            # 濕度 + 降雨圖
            fig_hr = go.Figure()
            fig_hr.add_trace(go.Bar(
                x=times, y=rain_p, name='降雨機率%',
                marker_color='rgba(56,189,248,0.6)', width=1000*60*60
            ))
            fig_hr.add_trace(go.Scatter(
                x=times, y=humid, mode='lines', name='濕度%',
                line=dict(color='#a78bfa', width=2),
                yaxis='y2'
            ))
            fig_hr.update_layout(
                title=dict(text='💧 濕度與降雨機率', font=dict(color='white', size=15)),
                xaxis=dict(showgrid=False, color='rgba(255,255,255,0.3)'),
                yaxis=dict(title=dict(text='降雨機率 %', font=dict(color='rgba(255,255,255,0.6)')),
                           range=[0,100], showgrid=True,
                           gridcolor='rgba(255,255,255,0.06)', color='rgba(255,255,255,0.3)',
                           tickfont=dict(color='rgba(255,255,255,0.6)')),
                yaxis2=dict(title=dict(text='濕度 %', font=dict(color='rgba(255,255,255,0.6)')),
                            overlaying='y', side='right', range=[0,100],
                            color='rgba(255,255,255,0.3)',
                            tickfont=dict(color='rgba(255,255,255,0.6)')),
                height=320, template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(255,255,255,0.8)'),
                hovermode='x unified',
                legend=dict(font=dict(color='rgba(255,255,255,0.7)'), bgcolor='rgba(0,0,0,0)'),
                autosize=True
            )

            # 風速圖
            wind_colors = ['#4ade80' if w < 20 else '#fb923c' if w < 40 else '#f87171' for w in wind]
            fig_wind = go.Figure()
            fig_wind.add_trace(go.Bar(
                x=times, y=wind, name='風速 km/h',
                marker_color=wind_colors, width=1000*60*60
            ))
            fig_wind.update_layout(
                title=dict(text=f'{get_wind_emoji(avg_wind)} 風速趨勢（平均 {avg_wind} km/h）', font=dict(color='white', size=15)),
                xaxis=dict(showgrid=False, color='rgba(255,255,255,0.3)'),
                yaxis=dict(title=dict(text='km/h', font=dict(color='rgba(255,255,255,0.6)')),
                           showgrid=True, gridcolor='rgba(255,255,255,0.06)',
                           color='rgba(255,255,255,0.3)',
                           tickfont=dict(color='rgba(255,255,255,0.6)')),
                height=300, template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(255,255,255,0.8)'),
                hovermode='x unified',
                legend=dict(font=dict(color='rgba(255,255,255,0.7)'), bgcolor='rgba(0,0,0,0)'),
                autosize=True
            )

            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.plotly_chart(fig_temp, use_container_width=True)
            with col_chart2:
                st.plotly_chart(fig_hr, use_container_width=True)
            st.plotly_chart(fig_wind, use_container_width=True)

        # ── 詳細資料折疊 ──
        with st.expander("📋 詳細天氣資料（明日 + 後天）"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### 明天")
                st.write(f"- 天氣：{tomorrow_icon} {tomorrow_desc}")
                st.write(f"- 溫度：{tomorrow_min:.0f}°C ~ {tomorrow_max:.0f}°C")
                st.write(f"- 降雨機率：{tomorrow_rain}%")
                st.write(f"- 風速：{avg_wind} km/h（{get_wind_level(avg_wind)}）")
            with c2:
                if day3_max:
                    st.markdown("##### 後天")
                    st.write(f"- 天氣：{day3_icon} {day3_desc}")
                    st.write(f"- 溫度：{day3_min:.0f}°C ~ {day3_max:.0f}°C")
                    st.write(f"- 降雨機率：{day3_rain}%")

    else:
        st.error("無法取得天氣資料，請稍後再試 😔")

    # ── Footer ──
    st.markdown(f"""
    <div class="footer">
        📊 資料更新：{now_str} &nbsp;|&nbsp; V{VERSION}<br>
        本報告僅供參考
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
