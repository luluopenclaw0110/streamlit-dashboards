#!/usr/bin/env python3
"""
少爺專用 - 專業天氣儀表板 V2
使用方式: streamlit run weather_dashboard.py
"""

import streamlit as st
import plotly.graph_objects as go
import subprocess
import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 頁面設定
st.set_page_config(
    page_title="少爺的天氣儀表板",
    page_icon="🌤️",
    layout="wide"
)

# ===== 地點設定（從北到南排序：台灣 → 日本）=====
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

# AQI 測站對應（台灣）
TAIWAN_AQI_STATIONS = {
    '新竹寶山': '新竹市',
    '苗栗': '苗栗',
    '台中南屯': '台中',
    '沙鹿': '沙鹿',
    '龍井': '龍井',
    '彰化': '彰化',
    '埔里': '埔里',
    '日月潭': '日月潭',
}

# 自動化通報地點（不動！）
AUTO_NOTIFY_LOCATIONS = ['新竹寶山', '台中南屯']

# 頁面預設地點
DEFAULT_LOCATION = '台中南屯'


# ===== API 函式 =====
def get_weather_data(lat, lon):
    """從 Open-Meteo API 取得天氣資料"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,weather_code,apparent_temperature&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia/Taipei&forecast_days=3"
    try:
        result = subprocess.run(['curl', '-s', url], capture_output=True, text=True, timeout=10)
        return json.loads(result.stdout)
    except Exception as e:
        st.error(f"天氣 API 錯誤: {e}")
        return None


def get_taiwan_aqi(city_name):
    """從台灣環保署 AQI API 取得空氣品質資料"""
    try:
        # 台灣環保署開放資料 AQI API (需要 API key)
        # 正確端點格式: https://data.moenv.gov.tw/api/v2/aqx_p_432
        # 若無 API key，回傳 None 並在 UI 顯示提示
        url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        params = {
            'offset': '0',
            'limit': '500'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # 檢查是否需要 API key
        if response.status_code == 200:
            text = response.text.strip()
            if not text:
                st.warning("⚠️ 台灣 AQI API 回傳空值，可能需要 API key")
                return None
            try:
                data = response.json()
                records = data.get('records', [])
                if not records:
                    st.warning("⚠️ AQI API 無資料回傳")
                    return None
                # 搜尋符合城市名稱的測站
                for record in records:
                    if city_name in record.get('SiteName', '') or city_name in record.get('County', ''):
                        return record
                # 取第一筆（如果沒找到精確匹配）
                if records:
                    return records[0]
            except json.JSONDecodeError as je:
                # API 回傳非 JSON 格式（可能是錯誤頁面）
                st.warning(f"⚠️ AQI API 回傳非 JSON 格式: {str(je)[:50]}")
                return None
        else:
            st.warning(f"⚠️ AQI API 連線失敗 (HTTP {response.status_code})，可能需要 API key")
            return None
            
    except requests.exceptions.ConnectionError:
        st.warning("⚠️ 無法連線到台灣 AQI API")
        return None
    except requests.exceptions.Timeout:
        st.warning("⚠️ AQI API 連線逾時")
        return None
    except Exception as e:
        st.warning(f"⚠️ AQI 取得失敗: {str(e)[:100]}")
        return None


def get_waqi_aqi(lat, lon):
    """從 WAQI API 取得空氣品質資料（國外用）"""
    try:
        # WAQI API - 使用地理座標查詢
        # 免費 token 可用於測試，但有流量限制
        url = f"https://api.waqi.info/feed/geo:{lat};{lon}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        params = {'token': 'demo'}  # 測試用 token，正式需申請
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            text = response.text.strip()
            if not text:
                return None
            data = response.json()
            if data.get('status') == 'ok':
                return data.get('data')
        return None
    except Exception as e:
        return None


def get_aqi_status(aqi):
    """根據 AQI 值回傳狀態描述"""
    try:
        aqi_val = int(aqi) if aqi else None
        if aqi_val is None:
            return '未知', '⚪', 'gray'
        elif aqi_val <= 50:
            return '良好', '🟢', 'green'
        elif aqi_val <= 100:
            return '中等', '🟡', 'yellow'
        elif aqi_val <= 150:
            return '對敏感族群不健康', '🟠', 'orange'
        elif aqi_val <= 200:
            return '不健康', '🔴', 'red'
        elif aqi_val <= 300:
            return '非常不健康', '🟣', 'purple'
        else:
            return '危害', '❤️‍🔥', 'darkred'
    except:
        return '未知', '⚪', 'gray'


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


# ===== 主程式 =====
def main():
    # ===== 版本設定 =====
    VERSION = "2.1"
    
    # ===== 初始化 session_state =====
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "domestic"
    if 'domestic_location' not in st.session_state:
        st.session_state.domestic_location = DEFAULT_LOCATION
    if 'international_location' not in st.session_state:
        st.session_state.international_location = list(JAPAN_LOCATIONS.keys())[0]
    
    # ===== 側邊欄 =====
    st.sidebar.title(f"🌤️ 少爺的天氣儀表板")
    st.sidebar.markdown(f"**V{VERSION}** | {datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y-%m-%d')}")
    st.sidebar.markdown("---")
    
    # ===== Tab 切換按鈕（側邊欄）=====
    st.sidebar.markdown("### 🗺️ 切換區域")
    tab_choice = st.sidebar.radio(
        "選擇區域",
        ["🇹🇼 國內 (台灣)", "🇯🇵 國外 (日本)"],
        index=0 if st.session_state.current_tab == "domestic" else 1,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # 更新當前 Tab
    new_tab = "domestic" if "國內" in tab_choice else "international"
    tab_changed = (new_tab != st.session_state.current_tab)
    st.session_state.current_tab = new_tab
    
    # ===== 根據當前 Tab 顯示對應的地點選擇 =====
    if st.session_state.current_tab == "domestic":
        selected_location = st.sidebar.selectbox(
            "選擇地點",
            list(TAIWAN_LOCATIONS.keys()),
            index=list(TAIWAN_LOCATIONS.keys()).index(st.session_state.domestic_location),
            key="domestic_selectbox"
        )
        # 如果 Tab 改變了或是新選擇，更新 session_state
        if selected_location != st.session_state.domestic_location:
            st.session_state.domestic_location = selected_location
    else:
        selected_location = st.sidebar.selectbox(
            "選擇地點",
            list(JAPAN_LOCATIONS.keys()),
            index=list(JAPAN_LOCATIONS.keys()).index(st.session_state.international_location),
            key="international_selectbox"
        )
        if selected_location != st.session_state.international_location:
            st.session_state.international_location = selected_location
    
    # 選擇天數
    days_to_show = st.sidebar.slider(
        "顯示天數",
        min_value=1,
        max_value=3,
        value=2
    )
    
    # 是否顯示 AQI
    show_aqi = st.sidebar.checkbox("顯示空氣品質 (AQI)", value=True)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 資料來源")
    st.sidebar.markdown("- Open-Meteo API（天氣）")
    st.sidebar.markdown("- 環保署 AQI（國內）")
    st.sidebar.markdown("- WAQI AQI（國外）")
    
    # ===== 版次資訊（側邊欄底部）=====
    st.sidebar.markdown("---")
    st.sidebar.caption(f"📌 V{VERSION} | {datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y-%m-%d')}")
    
    # ===== 主頁面：統一天氣顯示 =====
    st.title(f"🌤️ {selected_location} 天氣預報")
    st.markdown(f"**報告時間：** {datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y年%m月%d日 %H:%M')}")
    
    # 判斷是國內還是國外
    is_domestic = selected_location in TAIWAN_LOCATIONS
    
    # 直接渲染當前選擇的天氣內容
    render_weather_content(selected_location, show_aqi, days_to_show, is_domestic=is_domestic)


def render_weather_content(location_name, show_aqi, days_to_show, is_domestic=True):
    """渲染天氣內容（可復用於不同 Tab）"""
    
    # 取得天氣資料
    data = get_weather_data(
        ALL_LOCATIONS[location_name]['lat'],
        ALL_LOCATIONS[location_name]['lon']
    )
    
    # ===== AQI 資料取得 =====
    aqi_data = None
    if show_aqi:
        if is_domestic:
            # 台灣 AQI - 先嘗試 EPA API，失敗則用 WAQI
            city = TAIWAN_AQI_STATIONS.get(location_name, location_name)
            aqi_data = get_taiwan_aqi(city)
            if aqi_data is None:
                # EPA API 失敗時，使用 WAQI 作為備案
                lat = ALL_LOCATIONS[location_name]['lat']
                lon = ALL_LOCATIONS[location_name]['lon']
                aqi_data = get_waqi_aqi(lat, lon)
        else:
            # 國外 WAQI AQI
            lat = ALL_LOCATIONS[location_name]['lat']
            lon = ALL_LOCATIONS[location_name]['lon']
            aqi_data = get_waqi_aqi(lat, lon)
    
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
        
        # ===== 天氣卡片（響應式：手機優先）=====
        # 使用 columns 的響應式設計
        if is_domestic:
            # 國內：4 欄 → 2 欄 → 1 欄（視窗大小）
            cols = st.columns(4)
        else:
            cols = st.columns(4)
        
        with cols[0]:
            st.metric("今天", f"{today_icon} {today_desc}", f"{today_min:.0f}° ~ {today_max:.0f}°C")
        with cols[1]:
            st.metric("明天", f"{tomorrow_icon} {tomorrow_desc}", f"{tomorrow_min:.0f}° ~ {tomorrow_max:.0f}°C")
        with cols[2]:
            if day3_max:
                st.metric("後天", f"{day3_icon} {day3_desc}", f"{day3_min:.0f}° ~ {day3_max:.0f}°C")
        with cols[3]:
            st.metric("降雨機率", f"明天 {tomorrow_rain}%", f"今天 {today_rain}%")
        
        # ===== AQI 卡片（如果有）=====
        if show_aqi and aqi_data:
            st.markdown("#### 🌬️ 空氣品質 (AQI)")
            
            # 檢測資料格式：EPA 使用 'AQI'，WAQI 使用 'aqi'
            if isinstance(aqi_data, dict) and 'AQI' in aqi_data:
                # 台灣 EPA AQI 格式
                aqi_val = aqi_data.get('AQI', 'N/A')
                pm25 = aqi_data.get('PM2.5', 'N/A')
                pm10 = aqi_data.get('PM10', 'N/A')
                o3 = aqi_data.get('O3', 'N/A')
                no2 = aqi_data.get('NO2', 'N/A')
                status, emoji, color = get_aqi_status(aqi_val)
                
                aqi_cols = st.columns(4)
                with aqi_cols[0]:
                    st.metric("AQI 指數", f"{emoji} {status}", f"AQI: {aqi_val}")
                with aqi_cols[1]:
                    st.metric("PM2.5", f"{pm25} μg/m³")
                with aqi_cols[2]:
                    st.metric("PM10", f"{pm10} μg/m³")
                with aqi_cols[3]:
                    st.metric("O3", f"{o3} ppb")
            elif isinstance(aqi_data, dict):
                # WAQI AQI 格式
                aqi_val = aqi_data.get('aqi', 'N/A')
                iaqi = aqi_data.get('iaqi', {})
                pm25 = iaqi.get('pm25', {}).get('v', 'N/A') if isinstance(iaqi, dict) else 'N/A'
                pm10 = iaqi.get('pm10', {}).get('v', 'N/A') if isinstance(iaqi, dict) else 'N/A'
                status, emoji, color = get_aqi_status(aqi_val)
                
                aqi_cols = st.columns(4)
                with aqi_cols[0]:
                    st.metric("AQI 指數", f"{emoji} {status}", f"AQI: {aqi_val}")
                with aqi_cols[1]:
                    st.metric("PM2.5", f"{pm25} μg/m³")
                with aqi_cols[2]:
                    st.metric("PM10", f"{pm10} μg/m³")
                with aqi_cols[3]:
                    st.metric("資料來源", "WAQI")
        
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
        
        # AQI 建議
        if show_aqi and aqi_data:
            if isinstance(aqi_data, dict) and 'AQI' in aqi_data:
                aqi_val = aqi_data.get('AQI', 'N/A')
            else:
                aqi_val = aqi_data.get('aqi', 'N/A') if isinstance(aqi_data, dict) else 'N/A'
            
            try:
                aqi_num = int(aqi_val)
                if aqi_num > 100:
                    suggestions.append(f"🌫️ 空氣品質不佳 (AQI: {aqi_val})，建議戴口罩")
                elif aqi_num > 50:
                    suggestions.append(f"🫁 空氣品質普通 (AQI: {aqi_val})，敏感族群注意")
            except:
                pass
        
        if not suggestions:
            suggestions.append("✅ 天氣狀況良好，出門沒問題！")
        
        for sug in suggestions:
            if "✅" in sug:
                st.success(sug)
            elif "☂️" in sug or "⛈️" in sug or "🌫️" in sug:
                st.error(sug)
            elif "🌦️" in sug or "🧥" in sug or "🫁" in sug:
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


if __name__ == "__main__":
    main()
