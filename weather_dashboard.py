#!/usr/bin/env python3
"""
少爺專用 - 專業天氣儀表板
使用方式: streamlit run weather_dashboard.py
"""

import streamlit as st
import plotly.graph_objects as go
import subprocess
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 頁面設定
st.set_page_config(
    page_title="少爺的天氣儀表板",
    page_icon="🌤️",
    layout="wide"
)

# 地點設定
LOCATIONS = {
    '新竹寶山': {'lat': 24.75, 'lon': 121.05},
    '台中南屯': {'lat': 24.125, 'lon': 120.625},
    '台北': {'lat': 25.033, 'lon': 121.565},
    '高雄': {'lat': 22.627, 'lon': 120.301},
}

def get_weather_data(lat, lon):
    """從 Open-Meteo API 取得天氣資料"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,weather_code,apparent_temperature&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia/Taipei&forecast_days=3"
    result = subprocess.run(['curl', '-s', url], capture_output=True, text=True)
    return json.loads(result.stdout)

def get_weather_icon(code):
    icons = {
        0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
        45: '🌫️', 48: '🌫️',
        51: '🌧️', 53: '🌧️', 55: '🌧️',
        61: '🌧️', 63: '🌧️', 65: '🌧️',
        71: '🌨️', 73: '🌨️', 75: '🌨️',
        80: '🌦️', 81: '🌦️', 82: '🌦️',
        95: '⛈️', 96: '⛈️', 99: '⛈️'
    }
    return icons.get(code, '🌡️')

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
    if speed < 1: return '無風'
    elif speed < 6: return '輕風'
    elif speed < 12: return '微風'
    elif speed < 20: return '和風'
    elif speed < 29: return '清風'
    elif speed < 39: return '強風'
    elif speed < 50: return '疾風'
    elif speed < 62: return '大風'
    else: return '颶風'

# ===== 側邊欄 =====
st.sidebar.title("🌤️ 少爺的天氣儀表板")
st.sidebar.markdown("---")

# 選擇地點
selected_location = st.sidebar.selectbox(
    "選擇地點",
    list(LOCATIONS.keys())
)

# 選擇天數
days_to_show = st.sidebar.slider(
    "顯示天數",
    min_value=1,
    max_value=3,
    value=2
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 資料來源")
st.sidebar.markdown("- Open-Meteo API")

# ===== 主頁面 =====
st.title(f"🌤️ {selected_location} 天氣預報")
st.markdown(f"**報告時間：** {datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y年%m月%d日 %H:%M')}")

# 取得天氣資料
data = get_weather_data(
    LOCATIONS[selected_location]['lat'],
    LOCATIONS[selected_location]['lon']
)

if data:
    hourly = data['hourly']
    daily = data['daily']
    
    # ===== 今日天氣概覽 =====
    today_max = daily['temperature_2m_max'][0]
    today_min = daily['temperature_2m_min'][0]
    today_rain = daily['precipitation_probability_max'][0]
    today_code = hourly['weather_code'][0]
    today_icon = get_weather_icon(today_code)
    today_desc = get_weather_desc(today_code)
    
    # 明天
    tomorrow_max = daily['temperature_2m_max'][1]
    tomorrow_min = daily['temperature_2m_min'][1]
    tomorrow_rain = daily['precipitation_probability_max'][1]
    tomorrow_code = hourly['weather_code'][24]
    tomorrow_icon = get_weather_icon(tomorrow_code)
    tomorrow_desc = get_weather_desc(tomorrow_code)
    
    # 後天
    day3_max = daily['temperature_2m_max'][2] if len(daily['temperature_2m_max']) > 2 else None
    day3_min = daily['temperature_2m_min'][2] if len(daily['temperature_2m_min']) > 2 else None
    day3_rain = daily['precipitation_probability_max'][2] if len(daily['precipitation_probability_max']) > 2 else None
    day3_code = hourly['weather_code'][48] if len(hourly['weather_code']) > 48 else 0
    day3_icon = get_weather_icon(day3_code)
    day3_desc = get_weather_desc(day3_code)
    
    # ===== 天氣卡片 =====
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("今天", f"{today_icon} {today_desc}", f"{today_min:.0f}° ~ {today_max:.0f}°C")
    with col2:
        st.metric("明天", f"{tomorrow_icon} {tomorrow_desc}", f"{tomorrow_min:.0f}° ~ {tomorrow_max:.0f}°C")
    with col3:
        if day3_max:
            st.metric("後天", f"{day3_icon} {day3_desc}", f"{day3_min:.0f}° ~ {day3_max:.0f}°C")
    with col4:
        st.metric("降雨機率", f"明天 {tomorrow_rain}%", f"今天 {today_rain}%")
    
    # ===== 溫度趨勢圖 =====
    st.markdown("### 📈 溫度趨勢")
    
    hours = min(days_to_show * 24, 48)
    times = hourly['time'][:hours]
    temps = hourly['temperature_2m'][:hours]
    feels_like = hourly['apparent_temperature'][:hours]
    
    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(
        x=times, y=temps,
        mode='lines+markers',
        name='氣溫',
        line=dict(color='orange', width=3),
        marker=dict(size=6)
    ))
    fig_temp.add_trace(go.Scatter(
        x=times, y=feels_like,
        mode='lines+markers',
        name='體感溫度',
        line=dict(color='red', width=2, dash='dash'),
        marker=dict(size=5)
    ))
    
    fig_temp.update_layout(
        xaxis_title="時間",
        yaxis_title="溫度 (°C)",
        height=400,
        template="plotly_dark",
        hovermode="x unified"
    )
    st.plotly_chart(fig_temp, use_container_width=True)
    
    # ===== 濕度與降雨 =====
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💧 濕度趨勢")
        humidity = hourly['relative_humidity_2m'][:hours]
        
        fig_hum = go.Figure()
        fig_hum.add_trace(go.Bar(
            x=times, y=humidity,
            name='濕度%',
            marker_color='blue',
            opacity=0.6
        ))
        fig_hum.update_layout(
            xaxis_title="時間",
            yaxis_title="濕度 (%)",
            height=350,
            template="plotly_dark",
            yaxis_range=[0, 100]
        )
        st.plotly_chart(fig_hum, use_container_width=True)
    
    with col2:
        st.markdown("### 🌧️ 降雨機率")
        rain_prob = hourly['precipitation_probability'][:hours]
        
        fig_rain = go.Figure()
        fig_rain.add_trace(go.Scatter(
            x=times, y=rain_prob,
            mode='lines+markers',
            name='降雨機率%',
            line=dict(color='green', width=3),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 0, 0.2)'
        ))
        fig_rain.update_layout(
            xaxis_title="時間",
            yaxis_title="降雨機率 (%)",
            height=350,
            template="plotly_dark",
            yaxis_range=[0, 100]
        )
        st.plotly_chart(fig_rain, use_container_width=True)
    
    # ===== 風速 =====
    st.markdown("### 💨 風速趨勢")
    wind = hourly['wind_speed_10m'][:hours]
    
    fig_wind = go.Figure()
    colors = ['green' if w < 20 else 'orange' if w < 40 else 'red' for w in wind]
    fig_wind.add_trace(go.Bar(
        x=times, y=wind,
        name='風速',
        marker_color=colors
    ))
    fig_wind.update_layout(
        xaxis_title="時間",
        yaxis_title="風速 (km/h)",
        height=350,
        template="plotly_dark"
    )
    st.plotly_chart(fig_wind, use_container_width=True)
    
    # ===== 出門建議 =====
    st.markdown("---")
    st.markdown("### 💡 出門建議")
    
    avg_wind = sum(wind) // len(wind)
    suggestions = []
    
    if tomorrow_rain > 60:
        suggestions.append("☂️ 高降雨機率，建議攜帶雨具")
    elif tomorrow_rain > 30:
        suggestions.append("🌦️ 建議帶傘，有備無患")
    if avg_wind > 25:
        suggestions.append(f"💨 風速較強 ({avg_wind} km/h)，注意防風")
    if tomorrow_max > 32:
        suggestions.append("🥵 高溫炎熱，請注意防曬補充水分")
    if tomorrow_min < 18:
        suggestions.append("🧥 早晚溫差大，建議帶外套")
    if tomorrow_code in [95, 96, 99]:
        suggestions.append("⛈️ 可能有雷雨，請留意天氣變化")
    
    if not suggestions:
        suggestions.append("✅ 天氣狀況良好，出門沒問題！")
    
    for sug in suggestions:
        if "✅" in sug:
            st.success(sug)
        elif "☂️" in sug or "⛈️" in sug:
            st.error(sug)
        elif "🌦️" in sug or "🧥" in sug:
            st.warning(sug)
        else:
            st.info(sug)
    
    # ===== 詳細資料 =====
    st.markdown("---")
    st.markdown("### 📋 詳細天氣資料")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 明天 ( Tomorrow )")
        st.write(f"- **天氣：** {tomorrow_icon} {tomorrow_desc}")
        st.write(f"- **溫度：** {tomorrow_min:.0f}°C ~ {tomorrow_max:.0f}°C")
        st.write(f"- **降雨機率：** {tomorrow_rain}%")
        st.write(f"- **平均風速：** {avg_wind} km/h ({get_wind_level(avg_wind)})")
    
    with col2:
        if day3_max:
            st.markdown("#### 後天 ( Day After Tomorrow )")
            st.write(f"- **天氣：** {day3_icon} {day3_desc}")
            st.write(f"- **溫度：** {day3_min:.0f}°C ~ {day3_max:.0f}°C")
            st.write(f"- **降雨機率：** {day3_rain}%")

else:
    st.error("無法取得天氣資料，請稍後再試")

# ===== 底部資訊 =====
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "📊 資料更新時間：" + datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S') + "<br>"
    "本報告僅供參考，不構成投資建議"
    "</div>",
    unsafe_allow_html=True
)
