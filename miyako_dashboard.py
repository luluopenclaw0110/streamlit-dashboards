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
        {"航線": "台中 → 那霸", "航空公司": "星宇航空", "參考價格": "TWD 12,000/人", "備註": "暑假旺季"},
        {"航線": "台中 → 宮古島", "航空公司": "星宇航空 JX308", "參考價格": "TWD 14,000/人", "備註": "7/24 出發"},
        {"航線": "台中 → 石垣島", "航空公司": "需轉機", "參考價格": "TWD 15,000/人", "備註": "無直飛"},
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
        2. 輸入：台中 → 宮古島/那霸
        3. 選擇日期：7月下旬
        4. 點擊 🔔 追蹤價格
        5. 開啟 Email 通知
        """)
    with col2:
        st.markdown("**快速連結：**")
        st.link_button("🔍 台中→宮古島", "https://www.google.com/travel/flights?ts=CAEQCCICCg0vNzowGDEeRicCGg0vNzowaABqAkIlCir3mOH3OBCn4pooCJeyigMy95zq5_4EQBIIBCIIZA&cAE")
        st.link_button("🔍 台中→那霸", "https://www.google.com/travel/flights?ts=CAEQCCICCg0vNzowGDEeRicCGg0vNzowaABqAkIlCir3mOH3OBCn4pooCJeyigMy95zq5_4EQBIIBCIIZA&cAE")
        st.link_button("🔍 Skyscanner 比價", "https://www.skyscanner.com.tw/transport/flights-to/mmy/")
    
    st.divider()
    
    # 手動記錄票價
    st.subheader("📝 手動記錄票價")
    
    with st.form("add_flight"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            departure = st.selectbox("出發地", ["台中", "台北"])
        with col2:
            destination = st.selectbox("目的地", ["那霸", "宮古島", "石垣島"])
        with col3:
            airline = st.selectbox("航空公司", ["星宇航空", "中華航空", "長榮航空", "台灣虎航", "其他"])
        with col4:
            price = st.number_input("票價 (TWD)", min_value=0, step=1000, value=10000)
        
        submitted = st.form_submit_button("➕ 加入記錄")
        if submitted:
            data["flights"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "departure": departure,
                "destination": destination,
                "airline": airline,
                "flight_date": str(date(2026, 7, 24)),
                "price": price,
                "note": "手動記錄"
            })
            save_data(data)
            st.success("✅ 已加入記錄！")

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
        - 💰 參考價：TWD 4,000-8,000/晚
        """)
    with col2:
        st.link_button("🔗 查看房價", "https://www.booking.com/hotel/jp/xing-ye-rizoto-beb5chong-nawa-lai-liang-yuan.html")
        st.link_button("🔗 Agoda", "https://www.agoda.com/partners/partnersearch.aspx?pcs=1&cid=1799922&hid=92882999")
    
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
    
    st.markdown("**快速查詢空房：**")
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("🏨 繁花珊瑚 (Booking)", "https://www.booking.com/hotel/jp/imgya-coral-vllage-kids-paradise.zh-tw.html?checkin=2026-07-24&checkout=2026-07-28&group_adults=4")
    with col2:
        st.link_button("🏨 宮古島東涌 (Booking)", "https://www.booking.com/hotel/jp/miyakojima-tokyu-resort.zh-tw.html?checkin=2026-07-24&checkout=2026-07-28&group_adults=4")
    
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
    
    st.markdown("**快速查詢空房：**")
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("🏨 石垣島Vessel (Booking)", "https://www.booking.com/hotel/jp/vessel-ishigaki.html")
    with col2:
        st.link_button("🏨 石垣島 (Booking總覽)", "https://www.booking.com/city/jp/ishigaki-okinawa-ken.html")

# ====== 行程筆記 ======
with tab3:
    st.header("📋 行程筆記")
    
    notes = st.text_area(
        "記錄您的行程規劃、想法、待辦事項...", 
        value=data.get("notes", ""),
        height=400,
        placeholder="""=== 機票 ===
- 出發日期：7/24(五)
- 回程日期：7/28(二)
- 出發地：台中
- 星宇 JX308 台中→宮古島：07:20-09:35
- 星宇 JX309 宮古島→台中：10:35-11:00

=== 飯店優先順序 ===
1. 沖繩本島：BEB5 瀨良垣
2. 宮古島：繁花珊瑚度假村
3. 石垣島：Vessel 飯店

=== 想去的地方 ===
- 與那霸前濱沙灘
- 伊良部大橋
- AEON 超市
- 下地島通池"""
    )
    
    if st.button("💾 儲存筆記"):
        data["notes"] = notes
        save_data(data)
        st.success("✅ 筆記已儲存！")

# ====== 快速連結 ======
with tab4:
    st.header("🔗 實用連結")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✈️ 機票")
        st.link_button("星宇航空官網", "https://www.starlux-airlines.com/zh-TW")
        st.link_button("Google Flights", "https://www.google.com/travel/flights")
        st.link_button("Skyscanner", "https://www.skyscanner.com.tw/")
        st.link_button("KAYAK", "https://www.tw.kayak.com/")
    
    with col2:
        st.subheader("🏨 住宿")
        st.link_button("Agoda", "https://www.agoda.com/")
        st.link_button("Booking.com", "https://www.booking.com/")
        st.link_button("Klook 訂房", "https://www.klook.com/zh-TW/hotels/")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🚗 租車")
        st.link_button("OTS 租車", "https://www.otsrentacar.com.tw/")
        st.link_button("Times 租車", "https://www.times-rentacar.com.tw/")
    
    with col4:
        st.subheader("📱 其他")
        st.link_button("宮古島觀光官網", "https://visitokinawajapan.com/")
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

**目的地：**
- 沖繩本島
- 宮古島
- 石垣島
""")

st.sidebar.title("💡 顯示狀態")
if data["flights"]:
    st.sidebar.success(f"✈️ 已記錄 {len(data['flights'])} 筆票價")
else:
    st.sidebar.info("✈️ 尚未記錄票價")

st.sidebar.title("🕐 更新頻率")
st.sidebar.caption("機票價格：每週更新")
st.sidebar.caption("最後更新：2026-03-18")
