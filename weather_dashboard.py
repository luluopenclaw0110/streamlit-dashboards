#!/usr/bin/env python3
"""
少爺專用 - Modern Weather Dashboard V2 ✨
動態背景變色（根據天氣陰晴）
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
CITY_PHOTOS = {
    "新竹寶山": "https://images.unsplash.com/photo-1506806732259-39c2d0268423?w=800",
    "台中南屯": "https://images.unsplash.com/photo-1576078503712-f0ed8593d9ae?w=800",
    "台北信義": "https://images.unsplash.com/photo-1529655683826-a2405c0d321d?w=800",
    "高雄苓雅": "https://images.unsplash.com/photo-1568393691622-c7ba131d63b4?w=800",
    "桃園中壢": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800",
    "台南中西": "https://images.unsplash.com/photo-1597418693380-10de5c8a5838?w=800",
}

CITIES = {
    "新竹寶山": {"lat": 24.7385, "lon": 121.0197},
    "台中南屯": {"lat": 24.1387, "lon": 120.6451},
    "台北信義": {"lat": 25.0330, "lon": 121.5654},
    "高雄苓雅": {"lat": 22.6282, "lon": 120.3018},
    "桃園中壢": {"lat": 24.9639, "lon": 121.2213},
    "台南中西": {"lat": 22.9929, "lon": 120.1893},
}

# ===== 天氣主題配色 =====
def get_weather_theme(code):
    """根據天氣代碼返回配色"""
    if code == 0:  # 晴朗
        return {
            "bg_start": "#1e3a5f", "bg_mid": "#2d5a87", "bg_end": "#1a3a5c",
            "hero_start": "#FF6B35", "hero_end": "#F7931E", "accent": "#FFD93D",
            "name": "晴朗"
        }
    elif code in [1, 2]:  # 多雲
        return {
            "bg_start": "#4A5568", "bg_mid": "#718096", "bg_end": "#2D3748",
            "hero_start": "#667EEA", "hero_end": "#764BA2", "accent": "#A0AEC0",
            "name": "多雲"
        }
    elif code == 3:  # 陰天
        return {
            "bg_start": "#2D3748", "bg_mid": "#4A5568", "bg_end": "#1A202C",
            "hero_start": "#4A5568", "hero_end": "#2D3748", "accent": "#A0AEC0",
            "name": "陰天"
        }
    elif code in [45, 48]:  # 霧
        return {
            "bg_start": "#718096", "bg_mid": "#A0AEC0", "bg_end": "#CBD5E0",
            "hero_start": "#CBD5E0", "hero_end": "#A0AEC0", "accent": "#718096",
            "name": "霧"
        }
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:  # 雨天
        return {
            "bg_start": "#1A365D", "bg_mid": "#2C5282", "bg_end": "#1A202C",
            "hero_start": "#3182CE", "hero_end": "#4299E1", "accent": "#63B3ED",
            "name": "雨天"
        }
    elif code in [71, 73, 75]:  # 雪天
        return {
            "bg_start": "#E2E8F0", "bg_mid": "#F7FAFC", "bg_end": "#CBD5E0",
            "hero_start": "#BEE3F8", "hero_end": "#90CDF4", "accent": "#3182CE",
            "name": "雪天"
        }
    elif code in [95, 96, 99]:  # 雷暴
        return {
            "bg_start": "#1A202C", "bg_mid": "#2D3748", "bg_end": "#171923",
            "hero_start": "#9F7AEA", "hero_end": "#805AD5", "accent": "#B794F4",
            "name": "雷暴"
        }
    else:  # 預設
        return {
            "bg_start": "#1e3a5f", "bg_mid": "#2d5a87", "bg_end": "#1a3a5c",
            "hero_start": "#667EEA", "hero_end": "#764BA2", "accent": "#A0AEC0",
            "name": "天氣"
        }

# ===== 主程式 =====
def main():
    # Session state for favorites
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    
    # 側邊欄
    with st.sidebar:
        st.markdown("### 🌍 選擇城市")
        
        # 收藏快捷鍵
        if st.session_state.favorites:
            st.markdown("**⭐ 收藏城市**")
            fav_cols = st.columns([1, 1])
            for fav in st.session_state.favorites:
                with (fav_cols[0] if st.session_state.favorites.index(fav) % 2 == 0 else fav_cols[1]):
                    if st.button(fav, key=f"fav_{fav}"):
                        st.session_state.selected_city = fav
        
        selected_city = st.selectbox("城市", list(CITIES.keys()), index=1, key="city_select")
        
        # 收藏/取消收藏
        col_fav1, col_fav2 = st.columns(2)
        with col_fav1:
            if selected_city not in st.session_state.favorites:
                if st.button("⭐ 收藏"):
                    st.session_state.favorites.append(selected_city)
                    st.rerun()
        with col_fav2:
            if selected_city in st.session_state.favorites:
                if st.button("🗑️ 移除"):
                    st.session_state.favorites.remove(selected_city)
                    st.rerun()
        
        st.markdown("---")
        st.caption("🌤️ 資料來源：Open-Meteo")
        st.caption(f"📅 {datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y-%m-%d %H:%M')}")
    
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
            animation: bg-shift 20s ease-in-out infinite;
        }}
        @keyframes bg-shift {{
            0%, 100% {{ background-position: 0% 0%; }}
            50% {{ background-position: 0% 20%; }}
        }}
        
        .hero-section {{
            background: linear-gradient(135deg, {theme['hero_start']} 0%, {theme['hero_end']} 100%) !important;
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
            animation: hero-pulse 4s ease-in-out infinite;
        }}
        @keyframes hero-pulse {{
            0%, 100% {{ transform: scale(1); opacity: 0.8; }}
            50% {{ transform: scale(1.1); opacity: 1; }}
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
            border-color: {theme['accent']}66;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2), 0 0 20px {theme['accent']}33;
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
    
    # 城市照片 URL
    city_photo = CITY_PHOTOS.get(selected_city, "")
    
    # ===== Hero Section with City Photo =====
    if city_photo:
        st.markdown(f"""
        <div class="hero-section" style="background: linear-gradient(135deg, {theme['hero_start']}dd, {theme['hero_end']}ee) !important;">
            <img src="{city_photo}" style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;opacity:0.3;border-radius:24px;">
            <div style="position:relative;z-index:1;">
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
        </div>
        """, unsafe_allow_html=True)
    else:
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
    st.markdown(f"<div style='text-align:center;color:rgba(255,255,255,0.4);font-size:0.85rem'>🌤️ 少爺的天氣 | {theme['name']}模式 | {now.strftime('%Y-%m-%d %H:%M')} | V3.0</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()