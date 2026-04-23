#!/usr/bin/env python3
"""
少爺專用 - Modern Weather Dashboard V4.6 ✨
收藏城市連動 + 趨勢圖指標切換 + 本週天氣卡片連動
版本：V4.6 | 更新時間：2026-04-24
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
    if 'selected_day' not in st.session_state:
        st.session_state.selected_day = 0
    
    # 側邊欄
    with st.sidebar:
        st.markdown("### 🌍 選擇城市")
        
        if st.session_state.favorites:
            st.markdown("**⭐ 收藏城市**")
            for fav in st.session_state.favorites:
                if st.button(f"📍 {fav}", key=f"fav_{fav}"):
                    st.session_state.selected_city = fav
                    st.session_state.selected_day = 0  # 重置到今天
                    st.rerun()
        
        city_names = list(CITIES.keys())
        current_index = city_names.index(st.session_state.selected_city) if st.session_state.selected_city in city_names else 0
        selected_city = st.selectbox("城市", city_names, index=current_index, key="city_select")
        
        if selected_city != st.session_state.selected_city:
            st.session_state.selected_city = selected_city
            st.session_state.selected_day = 0
            st.rerun()
        
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
        st.caption("**🔖 V4.6** | 週卡片連動")
    
    selected_city = st.session_state.selected_city
    selected_day = st.session_state.selected_day
    
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
    
    now = datetime.now(ZoneInfo('Asia/Taipei'))
    days_tw = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日']
    
    # 根據選擇的日期取得資料
    # 取得該天的日期
    target_date = now + timedelta(days=selected_day)
    target_date_str = target_date.strftime('%Y-%m-%d')
    
    # 該天的天氣代碼
    d_code = daily['weather_code'][selected_day] if selected_day < len(daily['weather_code']) else daily['weather_code'][0]
    theme = get_weather_theme(d_code)
    
    # 該天的溫度
    d_high = int(daily['temperature_2m_max'][selected_day]) if selected_day < len(daily['temperature_2m_max']) else 0
    d_low = int(daily['temperature_2m_min'][selected_day]) if selected_day < len(daily['temperature_2m_min']) else 0
    
    # 日出日落
    sunrise = daily['sunrise'][selected_day][11:16] if selected_day < len(daily.get('sunrise', [])) else "06:00"
    sunset = daily['sunset'][selected_day][11:16] if selected_day < len(daily.get('sunset', [])) else "18:00"
    
    # 取得該天的每小時資料（24小時）
    hour_start = selected_day * 24
    hour_end = hour_start + 24
    day_hourly_temps = [int(t) for t in hourly['temperature_2m'][hour_start:hour_end]] if hour_start < len(hourly['temperature_2m']) else hourly['temperature_2m'][:24]
    day_hourly_humidity = hourly['relative_humidity_2m'][hour_start:hour_end] if hour_start < len(hourly['relative_humidity_2m']) else hourly['relative_humidity_2m'][:24]
    day_hourly_wind = [int(w) for w in hourly['wind_speed_10m'][hour_start:hour_end]] if hour_start < len(hourly['wind_speed_10m']) else hourly['wind_speed_10m'][:24]
    day_hourly_rain = hourly['precipitation_probability'][hour_start:hour_end] if hour_start < len(hourly['precipitation_probability']) else hourly['precipitation_probability'][:24]
    day_hourly_codes = hourly['weather_code'][hour_start:hour_end] if hour_start < len(hourly['weather_code']) else hourly['weather_code'][:24]
    
    # 該天的平均/總計指標
    avg_humidity = int(sum(day_hourly_humidity) / len(day_hourly_humidity)) if day_hourly_humidity else 0
    max_wind = max(day_hourly_wind) if day_hourly_wind else 0
    max_rain = max(day_hourly_rain) if day_hourly_rain else 0
    uv_max = daily['uv_index_max'][selected_day] if selected_day < len(daily.get('uv_index_max', [])) else 0
    avg_temp = int(sum(day_hourly_temps) / len(day_hourly_temps)) if day_hourly_temps else 0
    
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
        .hero-date {{ color: rgba(255,255,255,0.6); font-size: 0.9rem; margin-bottom: 8px; }}
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
        
        .daily-card {{ background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border-radius: 16px; padding: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease; cursor: pointer; }}
        .daily-card:hover {{ background: rgba(255,255,255,0.12); }}
        .daily-card.selected {{ background: rgba(255,255,255,0.2) !important; border-color: {theme['accent']} !important; box-shadow: 0 0 20px {theme['accent']}44; }}
        .daily-card .day {{ color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-bottom: 8px; }}
        .daily-card .icon {{ font-size: 2.5rem; margin: 8px 0; }}
        .daily-card .high {{ color: white; font-weight: 700; font-size: 1.1rem; }}
        .daily-card .low {{ color: rgba(255,255,255,0.5); font-size: 0.95rem; }}
        .daily-card .rain {{ color: #60a5fa; font-size: 0.8rem; margin-top: 6px; }}
        
        .section-title {{ color: white; font-size: 1.3rem; font-weight: 700; margin: 32px 0 16px; padding-left: 8px; border-left: 4px solid {theme['accent']}; }}
        
        [data-testid="stSidebar"] {{ background: rgba(15, 15, 35, 0.95) !important; backdrop-filter: blur(20px) !important; }}
        
        .metric-btn {{ background: rgba(255,255,255,0.1) !important; border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 12px !important; padding: 12px 20px !important; color: rgba(255,255,255,0.7) !important; transition: all 0.3s ease !important; }}
        .metric-btn:hover {{ background: rgba(255,255,255,0.15) !important; }}
        .metric-btn.active {{ background: {theme['accent']}33 !important; border-color: {theme['accent']} !important; color: white !important; box-shadow: 0 0 20px {theme['accent']}44 !important; }}
        
        .chart-container {{ background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1); }}
        .current-metric {{ background: linear-gradient(135deg, {theme['accent']}44, {theme['accent']}22); border: 2px solid {theme['accent']}; border-radius: 12px; padding: 12px 24px; text-align: center; margin-bottom: 16px; }}
        .current-metric .label {{ color: rgba(255,255,255,0.7); font-size: 0.85rem; }}
        .current-metric .value {{ color: white; font-size: 1.5rem; font-weight: 700; }}
        .chart-labels {{ display: flex; justify-content: space-between; padding: 8px 10px 0; color: rgba(255,255,255,0.5); font-size: 0.6rem; }}
    </style>
    """, unsafe_allow_html=True)
    
    # ===== Hero Section =====
    hero_date_display = target_date.strftime("%Y年%m月%d日") + " " + days_tw[target_date.weekday()]
    st.markdown(f"""
    <div class="hero-section">
        <div class="weather-icon-big">{weather_icon(d_code)}</div>
        <div class="hero-city">📍 {selected_city}</div>
        <div class="hero-date">{hero_date_display}</div>
        <div class="hero-temp">{avg_temp}°</div>
        <div class="hero-desc">{weather_icon(d_code)} {weather_desc(d_code)} | 高{d_high}° 低{d_low}°</div>
        <div class="hero-meta">
            <span>🌅 日出 {sunrise}</span>
            <span>🌇 日落 {sunset}</span>
        </div>
        <div class="hero-meta" style="margin-top:8px;">
            <span>💧 平均濕度 {avg_humidity}%</span>
            <span>💨 最大風速 {max_wind} km/h</span>
            <span>🌧️ 最高降雨 {max_rain}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== 6 欄資訊卡 =====
    info_items = [
        ("💧", "平均濕度", f"{avg_humidity}", "%"),
        ("🌡️", "平均體感", f"{avg_temp}", "°C"),
        ("💨", "最大風速", f"{max_wind}", "km/h"),
        ("☀️", "UV指數", f"{uv_max:.1f}", ""),
        ("🌧️", "最高降雨", f"{max_rain}", "%"),
        ("🌤️", "溫差", f"{d_high-d_low}", "°"),
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
    
    # ===== 趨勢圖區塊 =====
    st.markdown(f'<div class="section-title">📈 趨勢圖</div>', unsafe_allow_html=True)
    
    metric_options = {
        "temperature": ("🌡️ 溫度", "°C", day_hourly_temps),
        "humidity": ("💧 濕度", "%", day_hourly_humidity),
        "wind": ("💨 風速", "km/h", day_hourly_wind),
        "rain": ("🌧️ 降雨", "%", day_hourly_rain),
    }
    
    current_metric_label, current_metric_unit, current_metric_data = metric_options[st.session_state.chart_metric]
    
    btn_cols = st.columns(4)
    for i, (key, (label, unit, data)) in enumerate(metric_options.items()):
        with btn_cols[i]:
            is_active = key == st.session_state.chart_metric
            if st.button(label, key=f"metric_btn_{key}"):
                st.session_state.chart_metric = key
                st.rerun()
    
    current_val = current_metric_data[12] if len(current_metric_data) > 12 else (current_metric_data[0] if current_metric_data else 0)
    st.markdown(f"""
    <div class="current-metric">
        <div class="label">當日 {current_metric_label.replace('💧','').replace('🌡️','').replace('💨','').replace('🌧️','')}（中午）</div>
        <div class="value">{current_val}{current_metric_unit}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 繪製柱狀圖
    chart_html = '<div class="chart-container">'
    
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
        thresholds = {'high': 32, 'low': 10}
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
    max_val = max(current_metric_data) if max(current_metric_data) > 0 else 1
    min_val = min(current_metric_data)
    mid_val = (max_val + min_val) / 2
    chart_html += '<div style="position:absolute;left:0;top:0;height:100%;display:flex;flex-direction:column;justify-content:space-between;text-align:right;padding-right:8px;color:rgba(255,255,255,0.5);font-size:0.7rem;">'
    chart_html += f'<span>{int(max_val)}</span>'
    chart_html += f'<span>{int(mid_val)}</span>'
    chart_html += f'<span>{int(min_val)}</span>'
    chart_html += '</div>'
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
    # 該天的時間（從0點開始）
    day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    for j in range(0, 24, 1):
        hour_label = (day_start + timedelta(hours=j)).strftime('%H:00')
        chart_html += f'<span style="flex:1;text-align:center;">{hour_label}</span>'
    chart_html += '</div>'
    chart_html += '</div>'
    st.markdown(chart_html, unsafe_allow_html=True)
    
    # ===== 每小時預報 =====
    st.markdown(f'<div class="section-title">⏰ {hero_date_display} 每小時預報</div>', unsafe_allow_html=True)
    
    hourly_html = '<div class="hourly-scroll">'
    day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    for i in range(24):
        hour = (day_start + timedelta(hours=i)).strftime('%H:00')
        h_temp = day_hourly_temps[i] if i < len(day_hourly_temps) else 0
        h_code = day_hourly_codes[i] if i < len(day_hourly_codes) else 0
        hourly_html += f'''
        <div class="hourly-card">
            <div class="time">{hour}</div>
            <div class="icon">{weather_icon(h_code)}</div>
            <div class="temp">{h_temp}°</div>
        </div>'''
    hourly_html += '</div>'
    st.markdown(hourly_html, unsafe_allow_html=True)
    
    # ===== 本週天氣（可點選連動） =====
    st.markdown(f'<div class="section-title">📅 本週天氣（點選卡片連動全頁）</div>', unsafe_allow_html=True)
    
    daily_cols = st.columns(7)
    for i in range(7):
        day_name = days_tw[(now.weekday() + i) % 7]
        d_high = int(daily['temperature_2m_max'][i])
        d_low = int(daily['temperature_2m_min'][i])
        d_code = daily['weather_code'][i]
        d_rain = daily['precipitation_probability_max'][i] if 'precipitation_probability_max' in daily else 0
        is_selected = i == selected_day
        
        with daily_cols[i]:
            if st.button(f"{day_name}\n{d_high}°/{d_low}°\n{weather_icon(d_code)}\n🌧️{d_rain}%", key=f"day_btn_{i}", type="primary" if is_selected else "secondary"):
                st.session_state.selected_day = i
                st.rerun()
            
            # 用HTML顯示卡片樣式（同步 Streamlit 按鈕的 selected 狀態）
            card_class = "daily-card selected" if is_selected else "daily-card"
            st.markdown(f"""
            <div class="{card_class}" style="margin-top:8px;">
                <div class="day">{'今日' if i == 0 else day_name[2:]}</div>
                <div class="icon">{weather_icon(d_code)}</div>
                <div class="high">{d_high}°</div>
                <div class="low">{d_low}°</div>
                <div class="rain">🌧️ {d_rain}%</div>
            </div>
            """, unsafe_allow_html=True)
    
    # ===== Footer =====
    st.markdown("---")
    st.markdown(f"<div style='text-align:center;color:rgba(255,255,255,0.4);font-size:0.85rem'>🌤️ 少爺的天氣 | {theme['name']}模式 | {now.strftime('%Y-%m-%d %H:%M')} | V4.6 | 檢視{hero_date_display}資料</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
