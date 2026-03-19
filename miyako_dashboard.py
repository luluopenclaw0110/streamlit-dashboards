import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import json
import os

# 頁面設定
st.set_page_config(
    page_title="少爺的旅遊監控儀表板",
    page_icon="🗾",
    layout="wide"
)

# 資料檔案路徑
DATA_FILE = "miyako_data.json"

# 載入資料
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"flights": [], "hotels": [], "notes": ""}

# 儲存資料
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# 地點定義
destinations = {
    "🏨 沖繩本島": {
        "emoji": "🏨",
        "airport": "OKA",
        "flight_time": "1h 45min",
        "description": "沖繩本島是沖繩縣最大的島嶼，結合了日本與美國文化，有美軍基地、免税購物、海灘度假村。"
    },
    "🏝️ 宮古島": {
        "emoji": "🏝️",
        "airport": "SHI",
        "flight_time": "80min",
        "description": "宮古島以其美麗的『宮古藍』海灘聞名，有日本最美的沙灘之一的與那霸前濱。"
    },
    "🏝️ 石垣島": {
        "emoji": "🏝️",
        "airport": "ISG",
        "flight_time": "1h",
        "description": "石垣島是八重山群島的主要島嶼，擁有豐富的自然景觀和清澈的海水。"
    },
    "🏯 名古屋": {
        "emoji": "🏯",
        "airport": "NGO",
        "flight_time": "2h 45min",
        "description": "名古屋是日本中部最大城市，以美食、城堡和主題樂園聞名。"
    },
    "🗼 東京": {
        "emoji": "🗼",
        "airport": "NRT/HND",
        "flight_time": "3h",
        "description": "東京是日本的首都，結合了傳統文化與現代都市風情，是親子旅遊的首選。"
    },
    "🏰 大阪": {
        "emoji": "🏰",
        "airport": "KIX",
        "flight_time": "3h",
        "description": "大阪以美食天堂和環球影城聞名，是關西地區最受歡迎的旅遊城市。"
    },
    "🍜 福岡": {
        "emoji": "🍜",
        "airport": "FUK",
        "flight_time": "2h 30min",
        "description": "福岡是九州最大城市，以豚骨拉麵、太宰府天滿宮和溫泉聞名。"
    }
}

# 建立地點映射（包含 emoji 的名稱對應到資料中的名稱）
dest_map = {
    "🏨 沖繩本島": "那霸",
    "🏝️ 宮古島": "宮古島",
    "🏝️ 石垣島": "石垣島",
    "🏯 名古屋": "名古屋",
    "🗼 東京": "東京",
    "🏰 大阪": "大阪",
    "🍜 福岡": "福岡"
}

# 側邊欄選擇地點
st.sidebar.title("🗾 少爺的旅遊監控")

# 加入超級比一比選項
all_options = ["📊 超級比一比"] + list(destinations.keys())
selected_dest = st.sidebar.radio("請問您想去哪個城市？", all_options)

# ====== 超級比一比 ======
if selected_dest == "📊 超級比一比":
    st.title("📊 超級比一比")
    st.markdown("### ✈️ 去程 (7/19) + 回程 (7/25) 比價")
    
    if data["flights"]:
        df = pd.DataFrame(data["flights"])
        
        # 去程：7/19，出發地是台北/桃園/台中
        df_outbound = df[df["flight_date"] == "2026-07-19"]
        # 回程：7/25，出發地是目的地（那霸、宮古島等）
        df_return = df[df["flight_date"] == "2026-07-25"]
        
        comparison_data = []
        for dest_option, dest_code in dest_map.items():
            # 去程 - 台北/桃園出發
            taipei_flights = df_outbound[
                (df_outbound["destination"].str.contains(dest_code, na=False)) & 
                (df_outbound["departure"].str.contains("台北|桃園", na=False, regex=True))
            ]
            taipei_price = taipei_flights['price'].min() if not taipei_flights.empty else None
            
            # 去程 - 台中出發
            taichung_flights = df_outbound[
                (df_outbound["destination"].str.contains(dest_code, na=False)) & 
                (df_outbound["departure"].str.contains("台中", na=False))
            ]
            taichung_price = taichung_flights['price'].min() if not taichung_flights.empty else None
            
            # 回程 - 台北
            return_taipei = df_return[(df_return["departure"].str.contains(dest_code, na=False)) & (df_return["destination"].str.contains("台北|桃園", na=False, regex=True))]
            rt_tp = return_taipei['price'].min() if not return_taipei.empty else None
            
            # 回程 - 台中  
            return_taichung = df_return[(df_return["departure"].str.contains(dest_code, na=False)) & (df_return["destination"].str.contains("台中", na=False))]
            rt_tc = return_taichung['price'].min() if not return_taichung.empty else None
            
            # 飯店價格
            hotel_price = data.get("hotel_prices", {}).get(dest_code, None)
            
            # 目的地名稱（去掉 emoji）
            dest_name = dest_option.replace("🏨", "").replace("🏝️", "").replace("🏯", "").replace("🗼", "").replace("🏰", "").replace("🍜", "").strip()
            
            comparison_data.append({
                "目的地": dest_name,
                "去程-台北": f"TWD {taipei_price:,}" if taipei_price else "-",
                "去程-台中": f"TWD {taichung_price:,}" if taichung_price else "-",
                "回程-台北": f"TWD {rt_tp:,}" if rt_tp else "-",
                "回程-台中": f"TWD {rt_tc:,}" if rt_tc else "-",
                "飯店/晚": f"TWD {hotel_price:,}" if hotel_price else "-"
            })
        
        comp_df = pd.DataFrame(comparison_data)
        st.dataframe(comp_df, hide_index=True, use_container_width=True)
        
        st.info("💡 去程7/19，回程7/25，機票2大2小 / 飯店每晚")
    else:
        st.warning("尚無機票資料")
    
    st.stop()

# 以下是選擇特定目的地時
if selected_dest != "📊 超級比一比":
    dest_info = destinations[selected_dest]
    dest_name = dest_map.get(selected_dest, selected_dest)

    # 標題
    st.title(f"{dest_info['emoji']} {selected_dest.replace(dest_info['emoji'], '').strip()} 旅遊監控")

# 分頁
tab1, tab2, tab3, tab4 = st.tabs(["✈️ 機票", "🏨 飯店", "📋 行程", "🔗 連結"])

# 自訂 CSS 讓分頁標題更大
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 18px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ====== 機票 ======
with tab1:
    st.header("✈️ 機票價格")
    
    st.markdown(f"""
    **目的地機場：** {dest_info['airport']}
    - 飛行時間：{dest_info['flight_time']}
    - 建議出發地：台北/台中
    """)
    
    st.subheader("🔔 設定價格提醒")
    st.markdown("""
    1. 打開 [Google Flights](https://www.google.com/travel/flights)
    2. 輸入出發地 → 目的地
    3. 選擇日期
    4. 點擊 🔔 追蹤價格
    5. 開啟 Email 通知
    """)
    
    st.link_button("🔍 Google Flights 搜尋", "https://www.google.com/travel/flights")
    st.link_button("🔍 Skyscanner 比價", "https://www.skyscanner.com.tw/")
    
    st.divider()
    
    # 手動記錄
    st.subheader("📝 手動記錄票價")
    
    with st.form("add_flight"):
        col1, col2, col3 = st.columns(3)
        with col1:
            departure = st.selectbox("出發地", ["台北", "台中"])
        with col2:
            airline = st.selectbox("航空公司", ["星宇航空", "中華航空", "長榮航空", "台灣虎航", "其他"])
        with col3:
            price = st.number_input("票價 (TWD)", min_value=0, step=1000, value=10000)
        
        submitted = st.form_submit_button("➕ 加入記錄")
        if submitted:
            data["flights"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "departure": departure,
                "destination": dest_name,  # 使用過濾後的名稱
                "airline": airline,
                "flight_date": str(date(2026, 7, 24)),
                "price": price,
                "note": "手動記錄"
            })
            save_data(data)
            st.success("✅ 已加入記錄！")
    
    # 顯示記錄
    if data["flights"]:
        # 過濾顯示目前選擇的目的地機票
        df = pd.DataFrame(data["flights"])
        # 檢查是否有符合的記錄
        matching_flights = df[df["destination"].str.contains(dest_name, na=False)]
        
        if not matching_flights.empty:
            # 按日期排序
            matching_flights = matching_flights.sort_values("flight_date")
            
            st.subheader("📋 機票記錄")
            
            # 分離去程和回程，只顯示7/19去程和7/25回程
            outbound_flights = matching_flights[
                (matching_flights['departure'].str.contains('台北|桃園|台中', na=False, regex=True)) &
                (matching_flights['flight_date'] == '2026-07-19')
            ]
            return_flights = matching_flights[
                (~(matching_flights['departure'].str.contains('台北|桃園|台中', na=False, regex=True))) &
                (matching_flights['flight_date'] == '2026-07-25')
            ]
            
            # ====== 去程 ======
            st.markdown("### ✈️ 去程")
            
            if not outbound_flights.empty:
                out_dates = outbound_flights['flight_date'].unique()
                for flight_date in out_dates:
                    day_flights = outbound_flights[outbound_flights['flight_date'] == flight_date]
                    
                    # 找到台中和桃園的價格
                    taichung_flights = []
                    taipei_flights = []
                    
                    for idx, flight in day_flights.iterrows():
                        if '台中' in flight['departure']:
                            taichung_flights.append(flight)
                        elif '桃園' in flight['departure'] or '台北' in flight['departure']:
                            taipei_flights.append(flight)
                    
                    # 顯示
                    col1, col2, col3 = st.columns([2, 3, 3])
                    with col1:
                        st.write(f"**📅 {flight_date}**")
                    with col2:
                        if taichung_flights:
                            for f in taichung_flights:
                                st.caption(f"🛫 台中: {f['airline']} → TWD {f['price']:,}")
                        else:
                            st.caption("🛫 台中: -")
                    with col3:
                        if taipei_flights:
                            for f in taipei_flights:
                                st.caption(f"🛫 桃園: {f['airline']} → TWD {f['price']:,}")
                        else:
                            st.caption("🛫 桃園: -")
                    st.divider()
            else:
                st.info("尚無去程資料")
            
            # ====== 回程 ======
            st.markdown("### ✈️ 回程")
            
            if not return_flights.empty:
                ret_dates = return_flights['flight_date'].unique()
                for flight_date in ret_dates:
                    day_flights = return_flights[return_flights['flight_date'] == flight_date]
                    
                    # 分離返回台北和台中
                    ret_taipei = []
                    ret_taichung = []
                    for idx, flight in day_flights.iterrows():
                        if '台北' in flight['destination'] or '桃園' in flight['destination']:
                            ret_taipei.append(flight)
                        elif '台中' in flight['destination']:
                            ret_taichung.append(flight)
                    
                    col1, col2, col3 = st.columns([2, 3, 3])
                    with col1:
                        st.write(f"**📅 {flight_date}**")
                    with col2:
                        if ret_taipei:
                            for f in ret_taipei:
                                st.caption(f"→ 台北: {f['airline']} TWD {f['price']:,}")
                        else:
                            st.caption("→ 台北: -")
                    with col3:
                        if ret_taichung:
                            for f in ret_taichung:
                                st.caption(f"→ 台中: {f['airline']} TWD {f['price']:,}")
                        else:
                            st.caption("→ 台中: -")
                    st.divider()
            else:
                st.info("尚無回程資料")
        else:
            st.info(f"還沒有 {dest_name} 的機票記錄，請按「➕ 加入記錄」新增！")

# ====== 飯店 ======
with tab2:
    st.header("🏨 飯店推薦")
    
    # 根據不同地點顯示不同飯店
    hotels_data = {
        "🏨 沖繩本島": [
            {"排名": 1, "飯店": "BEB5 瀨良垣（星野集團）", "評分": "⭐ 8.5+", "房型": "公寓", "價格": "TWD 6,000-12,000", "特色": "廚房、洗衣機、兒童設施"},
            {"排名": 2, "飯店": "沖繩萬座毛洲際度假村", "評分": "⭐ 9.0+", "房型": "海景房", "價格": "TWD 15,000+", "特色": "海灘、泳池、兒童俱樂部"},
            {"排名": 3, "飯店": "Vessel 恩納", "評分": "⭐ 8.5+", "房型": "海景房", "價格": "TWD 5,000-8,000", "特色": "近海灘"},
        ],
        "🏝️ 宮古島": [
            {"排名": 1, "飯店": "繁花珊瑚度假村", "評分": "⭐ 8.0+", "房型": "4人 Villa", "價格": "TWD 8,700-15,000", "特色": "閣樓、按摩浴缸、兒童戲水區"},
            {"排名": 2, "飯店": "宮古島東涌", "評分": "⭐ 8.8", "房型": "海景房", "價格": "TWD 12,000+", "特色": "直通海灘、5間餐廳"},
            {"排名": 3, "飯店": "希爾頓宮古島", "評分": "⭐ 8.8", "房型": "標準房", "價格": "TWD 6,300+", "特色": "兒童俱樂部、無邊際泳池"},
            {"排名": 4, "飯店": "Hotel & Villa Seahorse", "評分": "⭐ 8.0+", "房型": "2房公寓", "價格": "TWD 3,100-6,000", "特色": "廚房、洗衣機"},
        ],
        "🏝️ 石垣島": [
            {"排名": 1, "飯店": "石垣島 Vessel 飯店", "評分": "⭐ 8.5+", "房型": "家庭房", "價格": "TWD 5,000-8,000", "特色": "近港口、18歲以下不佔床免費"},
            {"排名": 2, "飯店": "ANA Intercontinental 石垣島", "評分": "⭐ 9.0", "房型": "套房", "價格": "TWD 15,000+", "特色": "頂級度假村、海灘"},
            {"排名": 3, "飯店": "Fiore Club 石垣島", "評分": "⭐ 8.0+", "房型": "別墅", "價格": "TWD 7,000-12,000", "特色": "海灘 club"},
        ],
        "🏯 名古屋": [
            {"排名": 1, "飯店": "名古屋JR門樓酒店", "評分": "⭐ 8.5+", "房型": "家庭房", "價格": "TWD 3,500-6,000", "特色": "直通JR車站、國小以下免費"},
            {"排名": 2, "飯店": "大和ROYNET飯店 名古屋", "評分": "⭐ 8.0+", "房型": "雙人房", "價格": "TWD 2,500-4,500", "特色": "近地鐵、免費早餐"},
            {"排名": 3, "飯店": "Dormy Inn高階 名古屋榮", "評分": "⭐ 8.5+", "房型": "溫泉客房", "價格": "TWD 4,000-7,000", "特色": "天然溫泉、宵夜拉麵"},
        ],
        "🗼 東京": [
            {"排名": 1, "飯店": "東京押上普瑞米爾里士滿", "評分": "⭐ 9.0+", "房型": "家庭房", "價格": "TWD 5,000-9,000", "特色": "近晴空塔、超市"},
            {"排名": 2, "飯店": "東京東武飯店", "評分": "⭐ 8.5+", "房型": "四人房", "價格": "TWD 4,500-8,000", "特色": "直通車站、兒童免費"},
            {"排名": 3, "飯店": "上野蒙特利拉蘇比茲", "評分": "⭐ 8.0+", "房型": "雙人房", "價格": "TWD 3,000-5,500", "特色": "近上野站"},
            {"排名": 4, "飯店": "東京灣希爾頓", "評分": "⭐ 8.5+", "房型": "海景房", "價格": "TWD 6,000-12,000", "特色": "近迪士尼、泳池"},
        ],
        "🏰 大阪": [
            {"排名": 1, "飯店": "大阪南海輝盛庭", "評分": "⭐ 9.0+", "房型": "公寓", "價格": "TWD 5,000-10,000", "特色": "近難波3分鐘、廚房"},
            {"排名": 2, "飯店": "相鐵Fresa Inn 難波", "評分": "⭐ 8.5+", "房型": "雙人房", "價格": "TWD 2,500-4,500", "特色": "近地鐵、免費早餐"},
            {"排名": 3, "飯店": "御宿野乃 難波", "評分": "⭐ 8.5+", "房型": "溫泉客房", "價格": "TWD 3,500-6,000", "特色": "天然溫泉"},
            {"排名": 4, "飯店": "大阪蒙特利格拉斯米爾", "評分": "⭐ 8.0+", "房型": "直通車站", "價格": "TWD 3,000-5,500", "特色": "直通車站"},
        ],
        "🍜 福岡": [
            {"排名": 1, "飯店": "福岡天神光芒", "評分": "⭐ 9.0+", "房型": "家庭房", "價格": "TWD 5,000-9,000", "特色": "2025新開幕、近天神PARCO"},
            {"排名": 2, "飯店": "博多站前ROYNET", "評分": "⭐ 8.5+", "房型": "雙人房", "價格": "TWD 2,500-4,500", "特色": "近JR車站"},
            {"排名": 3, "飯店": "福岡海灣VIEW", "評分": "⭐ 8.0+", "房型": "海景房", "價格": "TWD 4,000-7,000", "特色": "海灘渡假村"},
        ]
    }
    
    if selected_dest in hotels_data:
        df_hotels = pd.DataFrame(hotels_data[selected_dest])
        st.table(df_hotels)
        
        st.subheader("🔗 查詢空房")
        col1, col2 = st.columns(2)
        with col1:
            st.link_button("Booking.com", "https://www.booking.com/")
        with col2:
            st.link_button("Agoda", "https://www.agoda.com/")

# ====== 行程 ======
with tab3:
    st.header("📋 五天四夜行程")
    
    itineraries = {
        "🏨 沖繩本島": """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達那霸機場
- 🚗 租車前往恩納村
- 🏨 入住 BEB5 瀨良垣
- 🌅 下午：美國村黃昏

### 📅 Day 2（7/25 六）- 北部一日遊
- 🌊 上午：萬座毛（象鼻岩）
- 🐬 上午/下午：美ら海水族館
- 🏖️ 下午：部瀨名海灘
- 🌙 晚上：星空觀賞

### 📅 Day 3（7/26 日）- 中部文化遊
- 🏰 上午：首里城
- 🛒 上午/下午：AEON MALL 來客夢
- 🍜 午餐/晚餐：國際通

### 📅 Day 4（7/27 一）- 南部輕鬆遊
- 🌊 上午：南城 Kamikaze 海灘
- 🏛️ 下午：沖繩 Outlets
- 🎁 傍晚：購買伴手禮

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：飯店休息
- ✈️ 返程
""",
        "🏝️ 宮古島": """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達宮古島機場
- 🚗 租車前往飯店
- 🌅 下午：伊良部大橋（看夕陽）
- 🍽️ 晚餐：宮古牛燒肉

### 📅 Day 2（7/25 六）- 海灘日
- 🏖️ 上午：與那霸前濱沙灘（日本最美海灘）
- 🏊 下午：飯店泳池/海灘玩水
- 🌊 傍晚：浮潛體驗

### 📅 Day 3（7/26 日）- 浮潛日
- 🐢 上午：砂山海灘（浮潛看海龜）
- 🛒 下午：AEON 超市購物
- 🍽️ 晚餐：海鮮料理

### 📅 Day 4（7/27 一）- 環島遊
- 🌿 上午：下地島通池（夢幻海景）
- 🌉 下午：池間大橋兜風
- 🌅 傍晚：龍城觀景台看夕陽

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：飯店休息
- ✈️ 返程
""",
        "🏝️ 石垣島": """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達石垣島機場
- 🚗 租車前往市區
- 🌅 下午：川平灣看海
- 🍽️ 晚餐：石垣牛燒肉

### 📅 Day 2（7/25 六）- 海灘日
- 🏖️ 上午：米子海灘
- 🏊 下午：ANA InterContinental 海灘
- 🌊 傍晚：浮潛/潛水

### 📅 Day 3（7/26 日）- 北部探險
- 🌿 上午：平久保崎燈塔
- 🐢 上午/下午：SUP/浮潛看海龜
- 🌅 傍晚：夕陽

### 📅 Day 4（7/27 一）- 購物日
- 🛒 上午：Maxvalu 超市
- 🍜 午餐：石垣島拉麵
- 🎁 下午：購買伴手禮

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：最後海灘時間
- ✈️ 返程
""",
        "🏯 名古屋": """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達中部國際機場
- 🚗 搭乘名鐵前往名古屋車站
- 🏨 入住名古屋車站附近飯店
- 🌅 下午：名古屋城

### 📅 Day 2（7/25 六）- 樂高樂園日
- 🎢 上午：樂高樂園（LEGO LAND）
- 🏊 下午：飯店休息/溫泉

### 📅 Day 3（7/26 日）- 親子文化日
- 🐼 上午：名古屋港水族館
- 🏰 下午：名古屋城

### 📅 Day 4（7/27 一）- 郊遊日
- 🌳 上午：磁浮鐵道館
- 🛒 下午：AEON 購物

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：飯店休息
- ✈️ 返程
""",
        "🗼 東京": """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達東京（羽田/成增）
- 🚗 前往上野/淺草
- 🏨 入住東京
- 🌅 下午：淺草雷門

### 📅 Day 2（7/25 六）- 迪士尼日
- 🎢 上午：東京迪士尼樂園
- 🎆 晚上：迪士尼煙火

### 📅 Day 3（7/26 日）- 晴朗一日
- 🗼 上午：東京晴空塔
- 🛒 下午：上野阿美橫丁

### 📅 Day 4（7/27 一）- 購物日
- 🛍️ 上午：新宿/池袋
- 🎮 下午：秋葉原

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：最後購物
- ✈️ 返程
""",
        "🏰 大阪": """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達關西國際機場
- 🚗 前往難波
- 🏨 入住難波
- 🌅 下午：道頓堀

### 📅 Day 2（7/25 六）- 環球影城日
- 🎢 上午：大阪環球影城（USJ）
- 🎆 晚上：煙火表演

### 📅 Day 3（7/26 日）- 城堡日
- 🏰 上午：大阪城
- 🛒 下午：天王寺/阿倍野

### 📅 Day 4（7/27 一）- 購物日
- 🛍️ 上午：心齋橋
- 🎁 下午：臨空城 Outlets

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：最後購物
- ✈️ 返程
""",
        "🍜 福岡": """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達福岡機場
- 🚗 前往天神/博多
- 🏨 入住博多
- 🌅 下午：天神商圈

### 📅 Day 2（7/25 六）- 親子遊戲日
- 🎮 上午：Pokemon Center
- 🏊 下午：海之中道海濱公園

### 📅 Day 3（7/26 日）- 太宰府日
- 🏛️ 上午：太宰府天滿宮
- 🛒 下午：AEON MALL

### 📅 Day 4（7/27 一）- 海岸日
- 🌊 上午：能古島
- 🛤️ 下午：柳橋連合市場

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：最後購物
- ✈️ 返程
"""
    }
    
    if selected_dest in itineraries:
        st.markdown(itineraries[selected_dest])
        
        # 景點
        spots_data = {
            "🏨 沖繩本島": [
                {"景點": "美ら海水族館", "特色": "世界第三大水族館", "適合": "親子"},
                {"景點": "首里城", "特色": "世界文化遺產", "適合": "歷史"},
                {"景點": "美國村", "特色": "購物、美食、日落", "適合": "all"},
                {"景點": "萬座毛", "特色": "象鼻岩、海景", "適合": "all"},
            ],
            "🏝️ 宮古島": [
                {"景點": "與那霸前濱", "特色": "日本最美海灘", "適合": "all"},
                {"景點": "伊良部大橋", "特色": "絕美跨海大橋、夕陽", "適合": "all"},
                {"景點": "下地島通池", "特色": "夢幻海景", "適合": "all"},
                {"景點": "砂山海灘", "特色": "浮潛聖地、可看海龜", "適合": "水上活動"},
            ],
            "🏝️ 石垣島": [
                {"景點": "川平灣", "特色": "翡翠綠寶石海灘", "適合": "all"},
                {"景點": "平久保崎燈塔", "特色": "日本最北端燈塔", "適合": "all"},
                {"景點": "米子海灘", "特色": "透明果凍海灘", "適合": "水上活動"},
                {"景點": "玉泉洞", "特色": "日本第二大鐘乳石洞", "適合": "all"},
            ],
            "🏯 名古屋": [
                {"景點": "名古屋城", "特色": "日本三大名城", "適合": "歷史"},
                {"景點": "樂高樂園", "特色": "親子同樂", "適合": "親子"},
                {"景點": "榮町商圈", "特色": "購物、美食", "適合": "購物"},
                {"景點": "名古屋港水族館", "特色": "世界最大展示", "適合": "親子"},
            ],
            "🗼 東京": [
                {"景點": "東京迪士尼", "特色": "亞洲最夯樂園", "適合": "親子"},
                {"景點": "淺草雷門", "特色": "東京最古剎", "適合": "all"},
                {"景點": "東京晴空塔", "特色": "東京地標", "適合": "all"},
                {"景點": "上野恩賜公園", "特色": "博物館、動物園", "適合": "親子"},
            ],
            "🏰 大阪": [
                {"景點": "環球影城 USJ", "特色": "哈利波特園區", "適合": "親子"},
                {"景點": "大阪城", "特色": "日本三名城", "適合": "歷史"},
                {"景點": "道頓堀", "特色": "美食天堂", "適合": "美食"},
                {"景點": "心齋橋", "特色": "購物天堂", "適合": "購物"},
            ],
            "🍜 福岡": [
                {"景點": "太宰府天滿宮", "特色": "求學問之神", "適合": "歷史"},
                {"景點": "Pokemon Center", "特色": "寶可夢旗艦店", "適合": "親子"},
                {"景點": "天神商圈", "特色": "九州最大商圈", "適合": "購物"},
                {"景點": "海之中道海濱公園", "特色": "親子樂園", "適合": "親子"},
            ]
        }
        
        st.subheader("🗺️ 必去景點")
        if selected_dest in spots_data:
            st.table(pd.DataFrame(spots_data[selected_dest]))

# ====== 連結 ======
with tab4:
    st.header("🔗 實用連結")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✈️ 機票")
        st.link_button("星宇航空官網", "https://www.starlux-airlines.com/zh-TW")
        st.link_button("台灣虎航", "https://www.tigerair.com/tw/zh/")
        st.link_button("Google Flights", "https://www.google.com/travel/flights")
        st.link_button("Skyscanner", "https://www.skyscanner.com.tw/")
    
    with col2:
        st.subheader("🏨 住宿")
        st.link_button("Booking.com", "https://www.booking.com/")
        st.link_button("Agoda", "https://www.agoda.com/")
        st.link_button("Klook 訂房", "https://www.klook.com/zh-TW/hotels/")
    
    st.divider()
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🚗 租車")
        st.link_button("OTS 租車", "https://www.otsrentacar.com.tw/")
        st.link_button("Times 租車", "https://www.times-rentacar.com.tw/")
    
    with col4:
        st.subheader("📱 其他")
        st.link_button("天氣查詢", "https://www.weather.gov.jp/")

# 側邊欄資訊
st.sidebar.title("💡 旅遊資訊")
st.sidebar.markdown(f"""
**出發日期：** 2026年7月24日(五)  
**回程日期：** 2026年7月28日(二)  
**人數：** 一家四口（2大2小）  
**天數：** 5天4夜
""")

st.sidebar.title("🕐 更新")
st.sidebar.caption("機票價格：每週更新")
