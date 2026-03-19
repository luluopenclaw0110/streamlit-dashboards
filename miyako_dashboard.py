import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import json
import os

# 頁面設定
st.set_page_config(
    page_title="宮古島旅遊監控儀表板",
    page_icon="🏝️",
    layout="wide"
)

# 資料檔案路徑
DATA_FILE = "miyako_data.json"

# 載入資料
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "flights": [],
        "hotels": [],
        "notes": ""
    }

# 儲存資料
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 初始化
data = load_data()

# 標題
st.title("🏝️ 宮古島旅遊監控儀表板")
st.markdown("### ✈️ 少爺的宮古島之旅 - 2026年7月底")

# 分頁
tab1, tab2, tab3, tab4 = st.tabs(["✈️ 機票監控", "🏨 飯店推薦", "📋 行程筆記", "🔗 快速連結"])

# ====== 機票監控 ======
with tab1:
    st.header("✈️ 機票價格追蹤")
    st.caption("每週更新一次 - 上次更新：2026-03-18")
    
    # 機票價格表
    st.subheader("📊 機票價格一覽")
    
    flight_data = [
        {"航線": "台北 → 那霸", "航空公司": "星宇/華航/長榮", "參考價格": "TWD 8,000-12,000/人", "備註": "直飛約1.5小時"},
        {"航線": "台北 → 宮古島", "航空公司": "星宇航空", "參考價格": "TWD 10,000-15,000/人", "備註": "直飛約80分鐘"},
        {"航線": "台北 → 石垣島", "航空公司": "台灣虎航/華航", "參考價格": "TWD 8,000-12,000/人", "備註": "直飛約1小時"},
    ]
    
    df_flights = pd.DataFrame(flight_data)
    st.table(df_flights)
    
    st.divider()
    
    # Google Flights 快速搜尋
    st.subheader("🔔 設定價格提醒")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Google Flights 設定教學：**
        1. 打開 Google Flights 連結
        2. 輸入：台北/台中 → 目的地
        3. 選擇日期：7月下旬
        4. 點擊 🔔 追蹤價格
        5. 開啟 Email 通知
        """)
    with col2:
        st.markdown("**快速連結：**")
        st.link_button("🔍 台北→沖繩", "https://www.google.com/travel/flights?ts=CAEQCCICCg0vNzowGDEeRicCGg0vNzowaABqAkIlCir3mOH3OBCn4pooCJeyigMy95zq5_4EQBIIBCIIZA&cAE")
        st.link_button("🔍 台北→宮古島", "https://www.google.com/travel/flights?ts=CAEQCCICCg0vNzowaABqAkIlCir3mOH3OBCn4pooCJeyigMy95zq5_4EQBIIBCIIZA&cAE")
        st.link_button("🔍 Skyscanner", "https://www.skyscanner.com.tw/")

# ====== 飯店推薦 ======
with tab2:
    st.header("🏨 飯店推薦")
    
    # 沖繩本島
    st.subheader("🏨 沖繩本島 - BEB5 瀨良垣")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        **星野集團 BEB5 沖繩瀨良垣**
        - ⭐ 評分：8.5+
        - 📍 位置：恩納村瀨良垣
        - 🏷️ 特色：公寓式飯店，每間房有廚房、洗衣機
        - 👨‍👩‍👧‍👦 適合：親子、家庭
        - 💰 參考價：TWD 6,000-12,000/晚（暑假）
        """)
    with col2:
        st.link_button("🔗 Booking.com", "https://www.booking.com/hotel/jp/xing-ye-rizoto-beb5chong-nawa-lai-liang-yuan.html")
    
    st.divider()
    
    # 宮古島
    st.subheader("🏝️ 宮古島飯店")
    
    miyako_hotels = [
        {"排名": 1, "飯店": "繁花珊瑚度假村", "評分": "⭐ 8.0+", "房型": "4人 Villa", "價格": "TWD 8,700-15,000", "特色": "閣樓、按摩浴缸、兒童戲水區"},
        {"排名": 2, "飯店": "宮古島東涌", "評分": "⭐ 8.8", "房型": "海景房", "價格": "TWD 12,000+", "特色": "直通海灘、5間餐廳"},
        {"排名": 3, "飯店": "希爾頓宮古島", "評分": "⭐ 8.8", "房型": "標準房", "價格": "TWD 6,300+", "特色": "兒童俱樂部、無邊際泳池"},
        {"排名": 4, "飯店": "Hotel & Villa Seahorse", "評分": "⭐ 8.0+", "房型": "2房公寓", "價格": "TWD 3,100-6,000", "特色": "廚房、洗衣機、近海灘"},
    ]
    
    df_miyako = pd.DataFrame(miyako_hotels)
    st.table(df_miyako)
    
    st.divider()
    
    # 石垣島
    st.subheader("🏝️ 石垣島飯店")
    
    ishigaki_hotels = [
        {"排名": 1, "飯店": "石垣島Vessel飯店", "評分": "⭐ 8.5+", "房型": "家庭房", "價格": "TWD 5,000-8,000", "特色": "近石垣港、18歲以下不佔床免費"},
        {"排名": 2, "飯店": "石垣島陽光海灘飯店", "評分": "⭐ 8.0+", "房型": "海景房", "價格": "TWD 6,000-10,000", "特色": "直通海灘、泳池"},
        {"排名": 3, "飯店": "ANA Intercontinental 石垣島", "評分": "⭐ 9.0", "房型": "套房", "價格": "TWD 15,000+", "特色": "頂級度假村"},
        {"排名": 4, "飯店": "Fiore Club 石垣島", "評分": "⭐ 8.0+", "房型": "別墅", "價格": "TWD 7,000-12,000", "特色": "海灘 club"},
    ]
    
    df_ishigaki = pd.DataFrame(ishigaki_hotels)
    st.table(df_ishigaki)

# ====== 行程筆記 ======
with tab3:
    st.header("📋 行程筆記")
    
    # 選擇目的地
    destination = st.radio("請問您想去哪個島？", 
        ["🏨 沖繩本島", "🏝️ 宮古島", "🏝️ 石垣島", "🏯 名古屋", "🗼 東京", "🏰 大阪", "🍜 福岡"], 
        horizontal=True)
    
    if "沖繩本島" in destination:
        st.subheader("🏨 沖繩本島 - 五天四夜行程")
        
        okinawa_itinerary = """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達那霸機場
- 🚗 租車前往恩納村
- 🏨 入住 BEB5 瀨良垣
- 🌅 下午：美國村黃昏
- 🍽️ 晚餐：恩納村附近料理

### 📅 Day 2（7/25 六）- 北部一日遊
- 🌊 上午：萬座毛（象鼻岩）
- 🐬 上午/下午：美ら海水族館
- 🍽️ 午餐：水族館附近
- 🏖️ 下午：部瀨名海灘
- 🌙 晚上：星空觀賞

### 📅 Day 3（7/26 日）- 中部文化遊
- 🏰 上午：首里城
- 🛒 上午/下午：AEON MALL 來客夢
- 🍜 午餐/晚餐：國際通

### 📅 Day 4（7/27 一）- 南部輕鬆遊
- 🌊 上午：南城 Kamikaze 海灘
- 🏛️ 下午：沖繩 Outlets
- 🍽️ 下午：奧武山公園
- 🎁 傍晚：購買伴手禮

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：飯店休息/最後玩水
- ✈️ 中午退房 → 還車 → 機場
- 🏠 返程
"""
        st.markdown(okinawa_itinerary)
        
        st.subheader("🗺️ 沖繩本島必去景點")
        okinawa_spots = [
            {"景點": "美ら海水族館", "特色": "世界第三大水族館", "適合": "親子"},
            {"景點": "首里城", "特色": "世界文化遺產", "適合": "歷史"},
            {"景點": "美國村", "特色": "購物、美食、日落", "適合": "all"},
            {"景點": "萬座毛", "特色": "象鼻岩、海景", "適合": "all"},
            {"景點": "AEON MALL來客夢", "特色": "最大購物中心", "適合": "購物"},
            {"景點": "國際通", "特色": "沖繩最熱鬧商圈", "適合": "購物、美食"},
            {"景點": "浦添大公園", "特色": "超長溜滑梯", "適合": "親子"},
            {"景點": "青之洞窟", "特色": "浮潛聖地", "適合": "水上活動"},
        ]
        st.table(pd.DataFrame(okinawa_spots))
        
    elif "宮古島" in destination:
        st.subheader("🏝️ 宮古島 - 五天四夜行程")
        
        miyako_itinerary = """
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
- 🛒 下午：AEON 超市購物 + 土產
- 🍽️ 晚餐：海鮮料理

### 📅 Day 4（7/27 一）- 環島遊
- 🌿 上午：下地島通池（夢幻海景）
- 🌉 下午：池間大橋兜風
- 🌅 傍晚：龍城觀景台看夕陽
- 🎁 傍晚：購買伴手禮

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：飯店休息/最後玩水
- ✈️ 10:35 退房 → 還車 → 機場
- 🏠 11:00 起飛 → 12:15 抵達台中
"""
        st.markdown(miyako_itinerary)
        
        st.subheader("🗺️ 宮古島必去景點")
        miyako_spots = [
            {"景點": "與那霸前濱", "特色": "日本最美海灘", "適合": "all"},
            {"景點": "伊良部大橋", "特色": "絕美跨海大橋、夕陽", "適合": "all"},
            {"景點": "下地島通池", "特色": "夢幻海景", "適合": "all"},
            {"景點": "砂山海灘", "特色": "浮潛聖地、可看海龜", "適合": "水上活動"},
            {"景點": "池間大橋", "特色": "第二大跨海橋", "適合": "兜風"},
            {"景點": "龍城觀景台", "特色": "拍攝來間大橋絕景", "適合": "all"},
            {"景點": "AEON宮古島", "特色": "購物中心", "適合": "購物"},
            {"景點": "宮古神社", "特色": "日本最南端神社", "適合": "歷史"},
        ]
        st.table(pd.DataFrame(miyako_spots))
        
    elif "石垣島" in destination:
        st.subheader("🏝️ 石垣島 - 五天四夜行程")
        
        ishigaki_itinerary = """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達石垣島機場
- 🚗 租車前往市區
- 🌅 下午：川平灣看海
- 🍽️ 晚餐：石垣牛燒肉

### 📅 Day 2（7/25 六）- 海灘日
- 🏖️ 上午：米子海灘（NANA 會員海灘）
- 🏊 下午：ANA InterContinental 海灘
- 🌊 傍晚：浮潛/潛水

### 📅 Day 3（7/26 日）- 北部探險
- 🌿 上午：平久保崎燈塔
- 🐢 上午/下午：SUP/浮潛看海龜
- 🍽️ 午餐：北部海鮮
- 🌅 傍晚：夕陽

### 📅 Day 4（7/27 一）- 購物日
- 🛒 上午：Maxvalu 超市
- 🍜 午餐：石垣島拉麵
- 🎁 下午：購買伴手禮
- 🌙 晚上：石垣港夜遊

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：最後海灘時間
- ✈️ 中午退房 → 還車 → 機場
- 🏠 返程
"""
        st.markdown(ishigaki_itinerary)
        
        st.subheader("🗺️ 石垣島必去景點")
        ishigaki_spots = [
            {"景點": "川平灣", "特色": "翡翠綠寶石海灘", "適合": "all"},
            {"景點": "平久保崎燈塔", "特色": "日本最北端燈塔", "適合": "all"},
            {"景點": "米子海灘", "特色": "透明果凍海灘", "適合": "水上活動"},
            {"景點": "石垣港", "特色": "購物、美食、夕陽", "適合": "all"},
            {"景點": "玉泉洞", "特色": "日本第二大鐘乳石洞", "適合": "all"},
            {"景點": "Fuu咖啡", "特色": "網紅打卡咖啡廳", "適合": "all"},
            {"景點": "Maxvalu超市", "特色": "最大超市", "適合": "購物"},
            {"景點": "觀光center", "特色": "伴手禮中心", "適合": "購物"},
        ]
        st.table(pd.DataFrame(ishigaki_spots))
        
    # ====== 名古屋 ======
    elif "名古屋" in destination:
        st.subheader("🏯 名古屋 - 五天四夜行程")
        
        nagoya_itinerary = """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達中部國際機場
- 🚗 搭乘名鐵前往名古屋車站
- 🏨 入住名古屋車站附近飯店
- 🌅 下午：名古屋城
- 🍽️ 晚餐：名古屋手羽先

### 📅 Day 2（7/25 六）- 樂高樂園日
- 🎢 上午：樂高樂園（LEGO LAND）
- 🍽️ 午餐：園區內
- 🏊 下午：飯店休息/溫泉
- 🌙 晚上：榮町商圈逛街

### 📅 Day 3（7/26 日）- 親子文化日
- 🐼 上午：名古屋港水族館/東山動植物園
- 🏰 下午：名古屋城
- 🍜 晚餐：味噌豬排

### 📅 Day 4（7/27 一）- 郊遊日
- 🌳 上午：磁浮鐵道館
- 🛒 下午：AEON 購物
- 🎁 傍晚：購買伴手禮

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：飯店休息
- ✈️ 中部國際機場返程
"""
        st.markdown(nagoya_itinerary)
        
        st.subheader("🗺️ 名古屋必去景點")
        nagoya_spots = [
            {"景點": "名古屋城", "特色": "日本三大名城", "適合": "歷史"},
            {"景點": "樂高樂園", "特色": "親子同樂", "適合": "親子"},
            {"景點": "榮町商圈", "特色": "購物、美食", "適合": "購物"},
            {"景點": "名古屋港水族館", "特色": "世界最大展示了", "適合": "親子"},
            {"景點": "磁浮鐵道館", "特色": "磁浮列車展示", "適合": "親子"},
            {"景點": "東山動植物園", "特色": "動物與植物", "適合": "親子"},
            {"景點": "熱田神宮", "特色": "日本三大神宮", "適合": "歷史"},
            {"景點": "大須觀音", "特色": "商業街", "適合": "購物"},
        ]
        st.table(pd.DataFrame(nagoya_spots))
        
        st.subheader("🏨 名古屋親子飯店推薦")
        nagoya_hotels = [
            {"排名": 1, "飯店": "名古屋JR門樓酒店", "評分": "⭐ 8.5+", "房型": "家庭房", "價格": "TWD 3,500-6,000", "特色": "直通JR車站、國小以下免費"},
            {"排名": 2, "飯店": "大和ROYNET飯店 名古屋", "評分": "⭐ 8.0+", "房型": "雙人房", "價格": "TWD 2,500-4,500", "特色": "近地鐵、免費早餐"},
            {"排名": 3, "飯店": "Dormy Inn高階 名古屋榮", "評分": "⭐ 8.5+", "房型": "溫泉客房", "價格": "TWD 4,000-7,000", "特色": "天然溫泉、宵夜拉麵"},
            {"排名": 4, "飯店": "GOLD STAY 名古屋", "評分": "⭐ 8.0+", "房型": "公寓", "價格": "TWD 3,000-5,000", "特色": "廚房、可住6人"},
        ]
        st.table(pd.DataFrame(nagoya_hotels))
        
    # ====== 東京 ======
    elif "東京" in destination:
        st.subheader("🗼 東京 - 五天四夜行程")
        
        tokyo_itinerary = """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達東京（羽田/成增）
- 🚗 前往上野/淺草
- 🏨 入住東京
- 🌅 下午：淺草雷門
- 🍽️ 晚餐：晴空塔

### 📅 Day 2（7/25 六）- 迪士尼日
- 🎢 上午：東京迪士尼樂園
- 🎆 晚上：迪士尼煙火

### 📅 Day 3（7/26 日）- 晴朗一日
- 🗼 上午：東京晴空塔
- 🛒 下午：上野阿美橫丁
- 🍜 晚餐：拉麵

### 📅 Day 4（7/27 一）- 購物日
- 🛍️ 上午：新宿/池袋
- 🎮 下午：秋葉原
- 🎁 傍晚：伴手禮

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：最後購物
- ✈️ 返程
"""
        st.markdown(tokyo_itinerary)
        
        st.subheader("🗺️ 東京必去景點")
        tokyo_spots = [
            {"景點": "東京迪士尼", "特色": "亞洲最夯樂園", "適合": "親子"},
            {"景點": "淺草雷門", "特色": "東京最古剎", "適合": "all"},
            {"景點": "東京晴空塔", "特色": "東京地標", "適合": "all"},
            {"景點": "上野恩賜公園", "特色": "博物館、动物园", "適合": "親子"},
            {"景點": "新宿御苑", "特色": "大温室", "適合": "all"},
            {"景點": "秋葉原", "特色": "電器動漫", "適合": "all"},
            {"景點": "澀谷十字路口", "特色": "潮流聖地", "適合": "購物"},
            {"景點": "台場", "特色": "彩虹橋、摩天輪", "適合": "all"},
        ]
        st.table(pd.DataFrame(tokyo_spots))
        
        st.subheader("🏨 東京親子飯店推薦")
        tokyo_hotels = [
            {"排名": 1, "飯店": "東京押上普瑞米爾里士滿", "評分": "⭐ 9.0+", "房型": "家庭房", "價格": "TWD 5,000-9,000", "特色": "近晴空塔、超市"},
            {"排名": 2, "飯店": "東京東武飯店", "評分": "⭐ 8.5+", "房型": "四人房", "價格": "TWD 4,500-8,000", "特色": "直通車站、兒童免費"},
            {"排名": 3, "飯店": "上野蒙特利拉蘇比茲", "評分": "⭐ 8.0+", "房型": "雙人房", "價格": "TWD 3,000-5,500", "特色": "近上野站"},
            {"排名": 4, "飯店": "東京灣希爾頓", "評分": "⭐ 8.5+", "房型": "海景房", "價格": "TWD 6,000-12,000", "特色": "近迪士尼、泳池"},
        ]
        st.table(pd.DataFrame(tokyo_hotels))
        
    # ====== 大阪 ======
    elif "大阪" in destination:
        st.subheader("🏰 大阪 - 五天四夜行程")
        
        osaka_itinerary = """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達關西國際機場
- 🚗 前往難波
- 🏨 入住難波
- 🌅 下午：道頓堀
- 🍽️ 晚餐：大阪燒

### 📅 Day 2（7/25 六）- 環球影城日
- 🎢 上午：大阪環球影城（USJ）
- 🎆 晚上：煙火表演

### 📅 Day 3（7/26 日）- 城堡日
- 🏰 上午：大阪城
- 🛒 下午：天王寺/阿倍野
- 🍜 晚餐：串炸

### 📅 Day 4（7/27 一）- 購物日
- 🛍️ 上午：心齋橋
- 🎁 下午：臨空城Outlets
- 🌙 晚上：梅田藍天大廈

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：最後購物
- ✈️ 關西機場返程
"""
        st.markdown(osaka_itinerary)
        
        st.subheader("🗺️ 大阪必去景點")
        osaka_spots = [
            {"景點": "環球影城 USJ", "特色": "哈利波特園區", "適合": "親子"},
            {"景點": "大阪城", "特色": "日本三名城", "適合": "歷史"},
            {"景點": "道頓堀", "特色": "美食天堂", "適合": "美食"},
            {"景點": "心齋橋", "特色": "購物天堂", "適合": "購物"},
            {"景點": "通天閣", "特色": "大阪地標", "適合": "all"},
            {"景點": "天王寺", "特色": "动物园美术馆", "適合": "親子"},
            {"景點": "臨空城Outlets", "特色": "機場旁購物", "適合": "購物"},
            {"景點": "梅田藍天大廈", "特色": "夜景展望台", "適合": "all"},
        ]
        st.table(pd.DataFrame(osaka_spots))
        
        st.subheader("🏨 大阪親子飯店推薦")
        osaka_hotels = [
            {"排名": 1, "飯店": "大阪南海輝盛庭", "評分": "⭐ 9.0+", "房型": "公寓", "價格": "TWD 5,000-10,000", "特色": "近難波3分鐘、廚房"},
            {"排名": 2, "飯店": "相鐵Fresa Inn 難波", "評分": "⭐ 8.5+", "房型": "雙人房", "價格": "TWD 2,500-4,500", "特色": "近地鐵、免費早餐"},
            {"排名": 3, "飯店": "御宿野乃 難波", "評分": "⭐ 8.5+", "房型": "溫泉客房", "價格": "TWD 3,500-6,000", "特色": "天然溫泉"},
            {"排名": 4, "飯店": "大阪蒙特利格拉斯米爾", "評分": "⭐ 8.0+", "房型": "直通車站", "價格": "TWD 3,000-5,500", "特色": "直通車站"},
        ]
        st.table(pd.DataFrame(osaka_hotels))
        
    # ====== 福岡 ======
    elif "福岡" in destination:
        st.subheader("🍜 福岡 - 五天四夜行程")
        
        fukuoka_itinerary = """
### 📅 Day 1（7/24 五）- 抵達日
- 🛬 抵達福岡機場
- 🚗 前往天神/博多
- 🏨 入住博多
- 🌅 下午：天神商圈
- 🍽️ 晚餐：屋台拉麵

### 📅 Day 2（7/25 六）- 親子遊戲日
- 🎮 上午：Pokemon Center
- 🏊 下午：海之中道海濱公園
- 🌙 晚上：博多運河城

### 📅 Day 3（7/26 日）- 太宰府日
- 🏛️ 上午：太宰府天滿宮
- 🛒 下午：AEON MALL
- 🍜 晚餐：豚骨拉麵

### 📅 Day 4（7/27 一）- 海岸日
- 🌊 上午：能古島
- 🛤️ 下午：柳橋連合市場
- 🎁 傍晚：伴手禮

### 📅 Day 5（7/28 二）- 返程日
- 🏨 上午：最後購物
- ✈️ 福岡機場返程
"""
        st.markdown(fukuoka_itinerary)
        
        st.subheader("🗺️ 福岡必去景點")
        fukuoka_spots = [
            {"景點": "太宰府天滿宮", "特色": "求學問之神", "適合": "歷史"},
            {"景點": "Pokemon Center", "特色": "寶可夢旗艦店", "適合": "親子"},
            {"景點": "天神商圈", "特色": "九州最大商圈", "適合": "購物"},
            {"景點": "博多運河城", "特色": "購物、看秀", "適合": "all"},
            {"景點": "海之中道海濱公園", "特色": "親子樂園", "適合": "親子"},
            {"景點": "柳橋連合市場", "特色": "海鮮市場", "適合": "美食"},
            {"景點": "能古島", "特色": "渡輪島嶼", "適合": "all"},
            {"景點": "麵包超人博物館", "特色": "親子必去", "適合": "親子"},
        ]
        st.table(pd.DataFrame(fukuoka_spots))
        
        st.subheader("🏨 福岡親子飯店推薦")
        fukuoka_hotels = [
            {"排名": 1, "飯店": "福岡天神光芒", "評分": "⭐ 9.0+", "房型": "家庭房", "價格": "TWD 5,000-9,000", "特色": "2025新開幕、近天神PARCO"},
            {"排名": 2, "飯店": "博多站前ROYNET", "評分": "⭐ 8.5+", "房型": "雙人房", "價格": "TWD 2,500-4,500", "特色": "近JR車站"},
            {"排名": 3, "飯店": "福岡海灣VIEW", "評分": "⭐ 8.0+", "房型": "海景房", "價格": "TWD 4,000-7,000", "特色": "海灘渡假村"},
            {"排名": 4, "飯店": "CLOC Courtyard", "評分": "⭐ 8.5+", "房型": "公寓", "價格": "TWD 4,000-7,000", "特色": "廚房、近天神"},
        ]
        st.table(pd.DataFrame(fukuoka_hotels))

# ====== 快速連結 ======
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
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🚗 租車")
        st.link_button("OTS 租車", "https://www.otsrentacar.com.tw/")
        st.link_button("Times 租車", "https://www.times-rentacar.com.tw/")
        st.link_button("Toyota 租車", "https://www.toyota-rentacar.com.tw/")
    
    with col4:
        st.subheader("📱 其他")
        st.link_button("沖繩觀光官網", "https://visitokinawajapan.com/")
        st.link_button("宮古島觀光", "https://www.miyako-islands.com/")
        st.link_button("石垣島觀光", "https://www.ishigaki.travel/")
        st.link_button("天氣查詢", "https://www.weather.gov.jp/")

# 側邊欄
st.sidebar.title("👤 旅遊資訊")
st.sidebar.markdown("""
**出發日期：** 2026年7月24日(五)  
**回程日期：** 2026年7月28日(二)  
**人數：** 一家四口（2大2小）  
**天數：** 5天4夜  
**預算：** TWD 100,000-150,000
""")

st.sidebar.title("📍 目的地選擇")
st.sidebar.info("請到「行程筆記」分頁選擇想去的地點")

st.sidebar.title("🕐 更新頻率")
st.sidebar.caption("機票價格：每週更新")
st.sidebar.caption("最後更新：2026-03-18")
