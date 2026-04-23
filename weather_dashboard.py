#!/usr/bin/env python3
"""
少爺專用 - Modern Weather Dashboard V4.5 ✨
收藏城市連動 + 趨勢圖指標切換
版本：V4.5 | 更新時間：2026-04-24
"""

import streamlit as st
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 頁面設定
st.set_page_config(
    page_title="少爺的天氣 🌤️",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== API 函式 =====
@st.cache_data(ttl=3600)
def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
        "hourly": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation_probability",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max,uv_index_max,sunrise,sunset",
        "timezone": "Asia/Taipei",
        "forecast_days": 7
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# ===== 天氣圖示 =====
def weather_icon(code):
    icons = {0:"☀️",1:"🌤️",2:"⛅",3:"☁️",45:"🌫️",48:"🌫️",51:"🌦️",53:"🌧️",55:"🌧️",61:"🌧️",63:"🌧️",65:"🌧️",71:"🌨️",73:"🌨️",75:"🌨️",80:"🌦️",81:"🌧️",82:"⛈️",95:"⛈️",96:"⛈️",99:"⛈️"}
    return icons.get(code, "🌤️")

def weather_desc(code):
    descs = {0:"晴朗",1:"大致晴朗",2:"局部多雲",3:"陰天",45:"霧",48:"霜霧",51:"輕微降雨",53:"中等降雨",55:"大雨",61:"小雨",63:"中雨",65:"大雨",71:"小雪",73:"中雪",75:"大雪",80:"陣雨",81:"中陣雨",82:"大陣雨",95:"雷暴",96:"雷暴加冰雹",99:"強雷暴"}
    return descs.get(code, "天氣")

# ===== 城市資料 =====
CITIES = {
    "台北信義": {"lat": 25.0330, "lon": 121.5654},
    "新竹寶山": {"lat": 24.7385, "lon": 121.0197},
    "新竹五峰": {"lat": 24.5033, "lon": 121.1135},
    "苗栗南庄": {"lat": 24.5964, "lon": 121.0106},
    "苗栗通霄": {"lat": 24.4489, "lon": 120.6778},
    "台中沙鹿": {"lat": 24.2333, "lon": 120.5667},
    "台中龍井": {"lat": 24.1958, "lon": 120.5297},
    "台中西屯": {"lat": 24.1788, "lon": 120.6400},
    "台中大肚": {"lat": 24.1617, "lon": 120.5439},
    "台中南屯": {"lat": 24.1387, "lon": 120.6451},
    "南投仁愛": {"lat": 24.0206, "lon": 121.1744},
    "南投埔里": {"lat": 23.9715, "lon": 120.9676},
    "南投魚池": {"lat": 23.8938, "lon": 120.9203},
    "南投信義": {"lat": 23.7545, "lon": 120.8517},
    "高雄楠梓": {"lat": 22.7205, "lon": 120.3258},
    "高雄鹽埕": {"lat": 22.6163, "lon": 120.2830},
    "屏東恆春": {"lat": 22.0034, "lon": 120.7461},
}

# ===== 天氣主題配色 =====
def get_weather_theme(code):
    """根據天氣代碼返回配色"""
    if code == 0:
        return {"bg_start": "#1e3a5f", "bg_mid": "#2d5a87", "bg_end": "#1a3a5c", "hero_start": "#FF6B35", "hero_end": "#F7931E", "accent": "#FFD93D", "name": "晴朗"}
    elif code in [1, 2]:
        return {"bg_start": "#4A5568", "bg_mid": "#718096", "bg_end": "#2D3748", "hero_start": "#667EEA", "hero_end": "#764BA2", "accent": "#A0AEC0", "name": "多雲"}
    elif code == 3:
        return {"bg_start": "#2D3748", "bg_mid": "#4A5568", "bg_end": "#1A202C", "hero_start": "#4A5568", "hero_end": "#2D3748", "accent": "#A0AEC0", "name": "陰天"}
    elif code in [45, 48]:
        return {"bg_start": "#718096", "bg_mid": "#A0AEC0", "bg_end": "#CBD5E0", "hero_start": "#CBD5E0", "hero_end": "#A0AEC0", "accent": "#718096", "name": "霧"}
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return {"bg_start": "#1A365D", "bg_mid": "#2C5282", "bg_end": "#1A202C", "hero_start": "#3182CE", "hero_end": "#4299E1", "accent": "#63B3ED", "name": "雨天"}
    elif code in [71, 73, 75]:
        return {"bg_start": "#E2E8F0", "bg_mid": "#F7FAFC", "bg_end": "#CBD5E0", "hero_start": "#BEE3F8", "hero_end": "#90CDF4", "accent": "#3182CE", "name": "雪天"}
    elif code in [95, 96, 99]:
        return {"bg_start": "#1A202C", "bg_mid": "#2D3748", "bg_end": "#171923", "hero_start": "#9F7AEA", "hero_end": "#805AD5", "accent": "#B794F4", "name": "雷暴"}
    else:
        return {"bg_start": "#1e3a5f", "bg_mid": "#2d5a87", "bg_end": "#1a3a5c", "hero_start": "#667EEA", "hero_end": "#764BA2", "accent": "#A0AEC0", "name": "天氣"}

# ===== 主程式 =====
def main():
    # Session state 初始化
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    if 'selected_city' not in st.session_state:
        st.session_state.selected_city = "台中南屯"
    if 'chart_metric' not in st.session_state:
        st.session_state.chart_metric = "temperature"
    
    # 側邊欄
    with st.sidebar:
        st.markdown("### 🌍 選擇城市")
        
        # 收藏快捷鍵 - 修復：加入 rerun
        if st.session_state.favorites:
            st.markdown("**⭐ 收藏城市**")
            for fav in st.session_state.favorites:
                if st.button(f"📍 {fav}", key=f"fav_{fav}"):
                    st.session_state.selected_city = fav
                    st.rerun()
        
        # 城市下拉選單
        city_names = list(CITIES.keys())
        current_index = city_names.index(st.session_state.selected_city) if st.session_state.selected_city in city_names else 0
        selected_city = st.selectbox("城市", city_names, index=current_index, key="city_select")
        
        # 更新當前城市
        if selected_city != st.session_state.selected_city:
            st.session_state.selected_city = selected_city
            st.rerun()
        
        # 收藏/取消收藏
        col_fav1, col_fav2 = st.columns(2)
        with col_fav1:
            if st.session_state.selected_city not in st.session_state.favorites:
                if st.button("⭐ 收藏"):
                    st.session_state.favorites.append(st.session_state.selected_city)
                    st.rerun()
        with col_fav2:
            if st.session_state.selected_city in st.session_state.favorites:
                if st.button("🗑️ 移除"):
                    st.session_state.favorites.remove(st.session_state.selected_city)
                    st.rerun()
        
        st.markdown("---")
        st.caption("🌤️ 資料來源：Open-Meteo")
        st.caption(f"📅 {datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y-%m-%d %H:%M')}")
        st.markdown("---")
        st.caption("**🔖 V4.5** | 收藏連動 + 趨勢圖")
    
    # 使用 session_state 的城市
    selected_city = st.session_state.selected_city
    
    # 取得資料
    lat = CITIES[selected_city]['lat']
    lon = CITIES[selected_city]['lon']
    data = get_weather(lat, lon)
    
    if not data or 'current' not in data:
        st.error("無法取得天氣資料")
        return
    
    current = data['current']
    hourly = data['hourly']
    daily = data['daily']
    
    code = current['weather_code']
    theme = get_weather_theme(code)
    
    now = datetime.now(ZoneInfo('Asia/Taipei'))
    days_tw = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日']
    
    # ===== 動態 CSS =====
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
        * {{ font-family: 'Inter', 'Noto Sans TC', sans-serif; }}
        
        .stApp {{
            background: linear-gradient(180deg, {theme['bg_start']} 0%, {theme['bg_mid']} 50%, {theme['bg_end']} 100%) !important;
            min-height: 100vh;
        }}
        
        .hero-section {{
            background: linear-gradient(135deg, {theme['hero_start']}dd, {theme['hero_end']}cc) !important;
            border-radius: 24px;
            padding: 40px;
            margin-bottom: 24px;
            position: relative;
            overflow: hidden;
        }}
        .hero-section::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
            border-radius: 50%;
        }}
        
        .hero-city {{ font-size: 1.8rem; font-weight: 700; color: white; margin-bottom: 8px; display: flex; align-items: center; gap: 10px; }}
        .hero-temp {{ font-size: 6rem; font-weight: 900; color: white; line-height: 1; text-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
        .hero-desc {{ font-size: 1.5rem; color: rgba(255,255,255,0.9); margin: 12px 0; }}
        .hero-meta {{ display: flex; gap: 24px; margin-top: 16px; color: rgba(255,255,255,0.8); font-size: 1rem; }}
        .hero-meta span {{ display: flex; align-items: center; gap: 6px; }}
        .weather-icon-big {{ font-size: 8rem; position: absolute; right: 40px; top: 50%; transform: translateY(-50%); opacity: 0.3; }}
        
        .info-card {{
            background: rgba(255,255,255,0.1) !important;
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.15);
            text-align: center;
            transition: all 0.3s ease;
        }}
        .info-card:hover {{
            background: rgba(255,255,255,0.15) !important;
            transform: translateY(-4px);
        }}
        .info-card .icon {{ font-size: 2.5rem; margin-bottom: 8px; }}
        .info-card .label {{ color: rgba(255,255,255,0.6); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }}
        .info-card .value {{ color: white; font-size: 1.8rem; font-weight: 700; margin-top: 4px; }}
        .info-card .unit {{ color: rgba(255,255,255,0.5); font-size: 0.9rem; }}
        
        .hourly-scroll {{ display: flex; gap: 16px; overflow-x: auto; padding: 16px 0; scroll-snap-type: x mandatory; }}
        .hourly-scroll::-webkit-scrollbar {{ height: 6px; }}
        .hourly-scroll::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.1); border-radius: 3px; }}
        .hourly-scroll::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.3); border-radius: 3px; }}
        .hourly-card {{ min-width: 90px; background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border-radius: 16px; padding: 16px; text-align: center; scroll-snap-align: start; border: 1px solid rgba(255,255,255,0.1); flex-shrink: 0; }}
        .hourly-card .time {{ color: rgba(255,255,255,0.6); font-size: 0.85rem; }}
        .hourly-card .icon {{ font-size: 2rem; margin: 8px 0; }}
        .hourly-card .temp {{ color: white; font-size: 1.2rem; font-weight: 600; }}
        
        .daily-card {{ background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border-radius: 16px; padding: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease; }}
        .daily-card:hover {{ background: rgba(255,255,255,0.12); }}
        .daily-card .day {{ color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-bottom: 8px; }}
        .daily-card .icon {{ font-size: 2.5rem; margin: 8px 0; }}
        .daily-card .high {{ color: white; font-weight: 700; font-size: 1.1rem; }}
        .daily-card .low {{ color: rgba(255,255,255,0.5); font-size: 0.95rem; }}
        .daily-card .rain {{ color: #60a5fa; font-size: 0.8rem; margin-top: 6px; }}
        
        .section-title {{ color: white; font-size: 1.3rem; font-weight: 700; margin: 32px 0 16px; padding-left: 8px; border-left: 4px solid {theme['accent']}; }}
        
        [data-testid="stSidebar"] {{ background: rgba(15, 15, 35, 0.95) !important; backdrop-filter: blur(20px) !important; }}
        
        /* 指標按鈕選中狀態 */
        .metric-btn {{ background: rgba(255,255,255,0.1) !important; border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 12px !important; padding: 12px 20px !important; color: rgba(255,255,255,0.7) !important; transition: all 0.3s ease !important; }}
        .metric-btn:hover {{ background: rgba(255,255,255,0.15) !important; }}
        .metric-btn.active {{ background: {theme['accent']}33 !important; border-color: {theme['accent']} !important; color: white !important; box-shadow: 0 0 20px {theme['accent']}44 !important; }}
        
        /* 圖表容器 */
        .chart-container {{ background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1); }}
        
        /* 當前指標顯示 */
        .current-metric {{ background: linear-gradient(135deg, {theme['accent']}44, {theme['accent']}22); border: 2px solid {theme['accent']}; border-radius: 12px; padding: 12px 24px; text-align: center; margin-bottom: 16px; }}
        .current-metric .label {{ color: rgba(255,255,255,0.7); font-size: 0.85rem; }}
        .current-metric .value {{ color: white; font-size: 1.5rem; font-weight: 700; }}
        
        /* 圖表時間軸 */
        .chart-labels {{ display: flex; justify-content: space-between; padding: 8px 10px 0; color: rgba(255,255,255,0.5); font-size: 0.75rem; }}
        .chart-labels span {{ flex: 1; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)
    
    # 取得資料
    temp = int(current['temperature_2m'])
    humidity = current['relative_humidity_2m']
    feels = int(current['apparent_temperature'])
    wind = current['wind_speed_10m']
    uv_max = daily['uv_index_max'][0] if 'uv_index_max' in daily else 0
    rain_prob = hourly['precipitation_probability'][0]
    
    # 日出日落
    sunrise = daily['sunrise'][0][11:16] if 'sunrise' in daily else "06:00"
    sunset = daily['sunset'][0][11:16] if 'sunset' in daily else "18:00"
    
    # ===== Hero Section =====
    st.markdown(f"""
    <div class="hero-section">
        <div class="weather-icon-big">{weather_icon(code)}</div>
        <div class="hero-city">📍 {selected_city}</div>
        <div class="hero-temp">{temp}°</div>
        <div class="hero-desc">{weather_icon(code)} {weather_desc(code)}</div>
        <div class="hero-meta">
            <span>🌅 日出 {sunrise}</span>
            <span>🌇 日落 {sunset}</span>
        </div>
        <div class="hero-meta" style="margin-top:8px;">
            <span>💧 濕度 {humidity}%</span>
            <span>🌡️ 體感 {feels}°</span>
            <span>💨 風速 {wind} km/h</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== 6 欄資訊卡 =====
    info_items = [
        ("💧", "濕度", f"{humidity}", "%"),
        ("🌡️", "體感", f"{feels}", "°C"),
        ("💨", "風速", f"{wind}", "km/h"),
        ("☀️", "UV指數", f"{uv_max:.1f}", ""),
        ("🌧️", "降雨機率", f"{rain_prob}", "%"),
        ("🌤️", "能見度", "10", "km"),
    ]
    
    cols = st.columns(6)
    for i, (icon, label, value, unit) in enumerate(info_items):
        with cols[i]:
            st.markdown(f"""
            <div class="info-card">
                <div class="icon">{icon}</div>
                <div class="label">{label}</div>
                <div class="value">{value}<span class="unit">{unit}</span></div>
            </div>
            """, unsafe_allow_html=True)
    
    # ===== 趨勢圖區塊（新增） =====
    st.markdown(f'<div class="section-title">📈 趨勢圖</div>', unsafe_allow_html=True)
    
    # 指標選擇按鈕
    metric_options = {
        "temperature": ("🌡️ 溫度", "°C", [int(t) for t in hourly['temperature_2m'][:24]]),
        "humidity": ("💧 濕度", "%", hourly['relative_humidity_2m'][:24]),
        "wind": ("💨 風速", "km/h", [int(w) for w in hourly['wind_speed_10m'][:24]]),
        "rain": ("🌧️ 降雨", "%", hourly['precipitation_probability'][:24]),
    }
    
    # 顯示當前選擇
    current_metric_label, current_metric_unit, current_metric_data = metric_options[st.session_state.chart_metric]
    
    # 指標按鈕列
    btn_cols = st.columns(4)
    for i, (key, (label, unit, data)) in enumerate(metric_options.items()):
        with btn_cols[i]:
            is_active = key == st.session_state.chart_metric
            btn_style = "metric-btn active" if is_active else "metric-btn"
            if st.button(label, key=f"metric_btn_{key}"):
                st.session_state.chart_metric = key
                st.rerun()
    
    # 顯示當前指標和數值
    current_val = current_metric_data[0]
    st.markdown(f"""
    <div class="current-metric">
        <div class="label">當前 {current_metric_label.replace('💧','').replace('🌡️','').replace('💨','').replace('🌧️','')}</div>
        <div class="value">{current_val}{current_metric_unit}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 繪製簡單的柱狀圖（用 HTML/CSS）
    # 繪製柱狀圖 + X軸時間 + 變色提醒
    chart_html = '<div class="chart-container">'
    
    # 根據指標設定顏色區間
    metric_key = st.session_state.chart_metric
    if metric_key == 'temperature':
        def get_temp_color(val, max_v, min_v):
            ratio = (val - min_v) / (max_v - min_v + 0.1)
            if ratio > 0.7:
                return f'rgba(255,{int(100+155*(ratio-0.7)/0.3)},50,0.85)'
            elif ratio > 0.4:
                return f'rgba(255,{int(200-50*(ratio-0.4)/0.3)},{int(200*(ratio-0.4)/0.3)},0.85)'
            else:
                return f'rgba(50,{int(150+(max_v-val)/(max_v-min_v+0.1)*105)},255,0.85)'
        color_func = get_temp_color
        thresholds = {'high': 32, 'low': 20}
    elif metric_key == 'humidity':
        def get_humidity_color(val, max_v, min_v):
            ratio = (val - min_v) / (max_v - min_v + 0.1)
            return f'rgba(50,{int(150-ratio*100)},255,{0.5+ratio*0.5})'
        color_func = get_humidity_color
        thresholds = {'high': 80, 'low': 40}
    elif metric_key == 'wind':
        def get_wind_color(val, max_v, min_v):
            ratio = (val - min_v) / (max_v - min_v + 0.1)
            if ratio > 0.6:
                return f'rgba(180,50,255,{0.6+ratio*0.4})'
            elif ratio > 0.3:
                return f'rgba(100,{int(200-ratio*100)},180,0.8)'
            else:
                return f'rgba(50,200,180,0.8)'
        color_func = get_wind_color
        thresholds = {'high': 30, 'low': 10}
    else:
        def get_rain_color(val, max_v, min_v):
            ratio = (val - min_v) / (max_v - min_v + 0.1)
            return f'rgba(30,{int(120+135*(1-ratio))},255,{0.4+ratio*0.6})'
        color_func = get_rain_color
        thresholds = {'high': 70, 'low': 20}
    
    chart_html += '<div style="display:flex;gap:0px;height:200px;padding:0 10px 0 50px;position:relative;">'
    # Y軸標籤
    max_val = max(current_metric_data) if max(current_metric_data) > 0 else 1
    min_val = min(current_metric_data)
    mid_val = (max_val + min_val) / 2
    chart_html += '<div style="position:absolute;left:0;top:0;height:100%;display:flex;flex-direction:column;justify-content:space-between;text-align:right;padding-right:8px;color:rgba(255,255,255,0.5);font-size:0.7rem;">'
    chart_html += f'<span>{int(max_val)}</span>'
    chart_html += f'<span>{int(mid_val)}</span>'
    chart_html += f'<span>{int(min_val)}</span>'
    chart_html += '</div>'
    # 柱狀圖區塊
    chart_html += '<div style="flex:1;display:flex;align-items:flex-end;gap:4px;padding-bottom:20px;">'
    max_val = max(current_metric_data) if max(current_metric_data) > 0 else 1
    min_val = min(current_metric_data)
    
    for j, val in enumerate(current_metric_data):
        height = max(8, int((val - min_val) / (max_val - min_val + 0.1) * 140))
        color = color_func(val, max(current_metric_data), min(current_metric_data))
        
        warn_marker = ""
        if metric_key == 'temperature':
            if val >= thresholds['high']:
                warn_marker = "🔥"
            elif val <= thresholds['low']:
                warn_marker = "❄️"
        elif metric_key == 'wind' and val >= thresholds['high']:
            warn_marker = "⚠️"
        elif metric_key == 'rain' and val >= thresholds['high']:
            warn_marker = "🌧️"
        
        chart_html += f'''
        <div style="flex:1;display:flex;flex-direction:column;align-items:center;position:relative;">
            <div style="position:absolute;top:-20px;color:{"#ff6b35" if warn_marker=="🔥" else "#60a5fa" if warn_marker=="❄️" else "#a855f7" if warn_marker=="⚠️" else "#3b82f6" if warn_marker=="🌧️" else "transparent"};font-size:0.7rem;font-weight:bold;">{warn_marker}</div>
            <div style="width:100%;height:{height}px;background:{color};border-radius:4px 4px 0 0;min-height:8px;" title="{val}{current_metric_unit}"></div>
        </div>'''
    chart_html += '</div></div>'
    
    # X軸時間標籤
    chart_html += '<div style="display:flex;justify-content:space-between;padding:8px 10px 0;color:rgba(255,255,255,0.5);font-size:0.6rem;">'
    for j in range(0, 24, 1):
        hour_label = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=j+1)).strftime('%H:00')
        chart_html += f'<span style="flex:1;text-align:center;">{hour_label}</span>'
    chart_html += '</div>'
    chart_html += '</div>'
    st.markdown(chart_html, unsafe_allow_html=True)
    
    # ===== 每小時預報 =====
    st.markdown(f'<div class="section-title">⏰ 每小時預報</div>', unsafe_allow_html=True)
    
    hourly_html = '<div class="hourly-scroll">'
    for i in range(24):
        hour = (now + timedelta(hours=i)).strftime('%H:00')
        h_temp = int(hourly['temperature_2m'][i])
        h_code = hourly['weather_code'][i]
        hourly_html += f'''
        <div class="hourly-card">
            <div class="time">{hour}</div>
            <div class="icon">{weather_icon(h_code)}</div>
            <div class="temp">{h_temp}°</div>
        </div>'''
    hourly_html += '</div>'
    st.markdown(hourly_html, unsafe_allow_html=True)
    
    # ===== 每週預報 =====
    st.markdown(f'<div class="section-title">📅 本週天氣</div>', unsafe_allow_html=True)
    
    daily_cols = st.columns(7)
    for i in range(7):
        day_name = days_tw[(now.weekday() + i) % 7]
        d_high = int(daily['temperature_2m_max'][i])
        d_low = int(daily['temperature_2m_min'][i])
        d_code = daily['weather_code'][i]
        d_rain = daily['precipitation_probability_max'][i] if 'precipitation_probability_max' in daily else 0
        
        with daily_cols[i]:
            st.markdown(f"""
            <div class="daily-card">
                <div class="day">{day_name if i == 0 else day_name[2:]}</div>
                <div class="icon">{weather_icon(d_code)}</div>
                <div class="high">{d_high}°</div>
                <div class="low">{d_low}°</div>
                <div class="rain">🌧️ {d_rain}%</div>
            </div>
            """, unsafe_allow_html=True)
    
    # ===== Footer =====
    st.markdown("---")
    st.markdown(f"<div style='text-align:center;color:rgba(255,255,255,0.4);font-size:0.85rem'>🌤️ 少爺的天氣 | {theme['name']}模式 | {now.strftime('%Y-%m-%d %H:%M')} | V4.5</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
