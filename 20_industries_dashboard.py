#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
20檔產業龍頭深度分析報告 V2
加入：產業分析、消息面、評估依據、投資建議
更新日期：2026-04-27
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime

# 頁面設定
st.set_page_config(
    page_title="20檔產業龍頭深度分析 V2",
    page_icon="📊",
    layout="wide"
)

# 股票資料（2026-04-27 更新）
stocks_data = [
    {
        "代碼": "2330", "名稱": "台積電", "產業": "半導體",
        "industry_analysis": "全球先進製程龍頭，AI晶片需求強勁，先進封裝CoWoS產能供不應求",
        "news": "AI晶片需求超預期、先進封裝CoWoS產能供不應求、海力士獲先進記憶體認證",
        "legal_person": "三大法人持續買超、外資持股高、投信偏多操作",
        "risks": "地緣政治風險、先進製程競爭加劇、資本支出龐大、客戶集中度",
        "strengths": "技術領先全球、客戶多元化、先進封裝優勢、產能持續擴張、AI先進製程需求強",
        "rating": "🟢建議持有",
        "suggestion": "技術領先但評價合理，AI需求強勁，適合長期持有，適合定期定額"
    },
    {
        "代碼": "2317", "名稱": "鴻海", "產業": "AI伺服器/電子代工",
        "industry_analysis": "電子組裝龍頭，伺服器/AI硬體需求持續，電動車/機器人布局中",
        "news": "AI伺服器訂單暢旺、電動車布局進展、機器人話題加持",
        "legal_person": "三大法人區間操作、外資賣超、投信買超",
        "risks": "客戶集中度、毛利率承壓、電動車/機器人進度落後、景氣波動",
        "strengths": "規模經濟優勢、垂直整合能力、全球布局完整、AI伺服器訂單能見度高",
        "rating": "🟢建議持有",
        "suggestion": "AI伺服器需求旺，但需注意毛利率變化，適合區間操作"
    },
    {
        "代碼": "2313", "名稱": "華通", "產業": "PCB/AI伺服器",
        "industry_analysis": "PCB大廠，受惠AI伺服器需求，高階ABF載板供需健康",
        "news": "GB200伺服器需求爆發、載板供需健康、相關設備概念股漲",
        "legal_person": "三大法人偏多、對沖基金加碼、投信認養",
        "risks": "PCB景氣波動大、陸廠競爭激烈、手機需求放緩、載板價格波動",
        "strengths": "高階載板技術領先、客戶認證嚴謹、ABF載板供需健康、伺服器訂單加持",
        "rating": "🔵成長潛力",
        "suggestion": "GB200伺服器需求爆發，載板供需健康，評等上調至成長潛力"
    },
    {
        "代碼": "3008", "名稱": "大立光", "產業": "光學鏡頭",
        "industry_analysis": "光學鏡頭龍頭，手機鏡頭升級放緩，車用/VR佈局中",
        "news": "iPhone鏡頭升級有限、汽車鏡頭認證順利、VR應用落後",
        "legal_person": "三大法人偏空、外資減碼、投信逢低承接",
        "risks": "手機鏡頭升級放緩、競爭對手分食市占、毛利率下滑、汽車驗證時間長",
        "strengths": "高階鏡頭技術領先、汽車大廠認證完整、潛望式鏡頭專利、8P鏡頭量產能力",
        "rating": "🟡觀望",
        "suggestion": "手機復甦緩慢，汽車驗證需時，等待營運拐點"
    },
    {
        "代碼": "9921", "名稱": "巨大", "產業": "運動休閒/自行車",
        "industry_analysis": "巨大機械為台灣自行車龍頭，電動輔助自行車滲透率提升",
        "news": "歐美庫存調整中、電動輔助自行車佔比提升、巨大股價回檔修正",
        "legal_person": "三大法人賣超、外資調節、投信偏觀望",
        "risks": "歐美需求放緩、電動輔助自行車法規、原料成本上漲、庫存調整",
        "strengths": "品牌優勢明顯、電動輔助自行車技術領先、歐美市場佔有率高、維修網絡完善",
        "rating": "🟡觀望",
        "suggestion": "歐美自行車需求放緩，庫存調整中，等待數據好轉再切入"
    },
    {
        "代碼": "2886", "名稱": "兆豐金", "產業": "金控",
        "industry_analysis": "兆豐金為民營銀行龍頭，利息收入穩健，信用卡業務成長",
        "news": "升息循環接近尾聲、信用卡手續費收入穩定、兆豐金獲利創高",
        "legal_person": "三大法人偏多、外資回補、投信作帳行情",
        "risks": "升息影響呆帳、金融市場波動、房貸風險、壽險子公司波動",
        "strengths": "民營銀行龍頭、壽險子公司貢獻穩定、信用卡業務成長、分行網絡優勢",
        "rating": "🟢建議持有",
        "suggestion": "金融龍頭，利息收入穩健，股息殖利率佳，適合定存替代"
    },
    {
        "代碼": "1216", "名稱": "統一", "產業": "食品",
        "industry_analysis": "統一為食品飲料龍頭，統一超/康是美渠道優勢，亞洲流通領導",
        "news": "統一超展店加速、康是美整合順利、亞洲流通事業成長",
        "legal_person": "三大法人區間操作、官股券商護盤、外資偏多",
        "risks": "原物料價格波動、中國景氣放緩、中國法規風險、轉投資複雜",
        "strengths": "流通事業龍頭、統一超渠道優勢、品牌多角化經營、轉投資收益穩",
        "rating": "🟢建議持有",
        "suggestion": "流通事業穩定，多角化經營佳，殖利率佳，適合长期持有"
    },
    {
        "代碼": "2207", "名稱": "和泰車", "產業": "汽車",
        "industry_analysis": "和泰車為豐田代理，電動車轉型挑戰，新車銷量穩定",
        "news": "Toyota bZ4X銷售放緩、Lexus銷售穩、和泰車試駕報告佳",
        "legal_person": "三大法人買超、外資持續認養、投信偏多",
        "risks": "電動車轉型挑戰、日圓貶值影響、代理品牌議價能力受限、競爭加劇",
        "strengths": "Toyota代理品牌力強、售後服務網絡完整、新車來源穩定、二手車價值高",
        "rating": "🟡觀望",
        "suggestion": "代理品牌面臨電動車轉型考驗，等待新產品線明朗化"
    },
    {
        "代碼": "2618", "名稱": "長榮航", "產業": "航空",
        "industry_analysis": "長榮航為航空龍頭，客運復甦強勁，貨運運費回升中",
        "news": "客運量超越疫情前、貨運運費回升、長榮航引進新機隊",
        "legal_person": "三大法人偏多操作、外資回補、投信作帳",
        "risks": "油價波動、兩岸關係影響、廉航競爭、飛機維修成本高",
        "strengths": "客運強勁復甦、A350新機隊提升效率、貨運運費回升、油價避險完善",
        "rating": "🔵成長潛力",
        "suggestion": "客運強勁復甦，貨運價格回升，評等上調至成長潛力"
    },
    {
        "代碼": "2412", "名稱": "中華電", "產業": "電信",
        "industry_analysis": "中華電為電信龍頭，5G用戶成長緩慢，固網寬頻穩定",
        "news": "5G資費價格戰放緩、中華電MOD改革、中華電殖利率高",
        "legal_person": "三大法人偏多、外資大買、官股護盤",
        "risks": "5G建設成本高、ARPU持續下滑、管制風險、頻譜標金高",
        "strengths": "固網寬頻優勢、5G頻段800MHz最大頻寬、現金殖利率高、穩定配息",
        "rating": "🟢建議持有",
        "suggestion": "電信龍頭，殖利率佳，5G貢獻漸增，適合穩健投資"
    },
    {
        "代碼": "2002", "名稱": "中鋼", "產業": "鋼鐵",
        "industry_analysis": "中鋼為鋼鐵龍頭，景氣復甦中，基礎建設需求支撐",
        "news": "碳費政策影響中鋼、中國鋼價回穩、基建需求支撐",
        "legal_person": "三大法人偏空操作、外資調節、投信觀望",
        "risks": "中國鋼鐵產能過剩、碳中和成本壓力、下游客戶庫存調整、報價波動大",
        "strengths": "規模最大、高爐技術成熟、成本優勢、中鋼構/綠色能源多角化",
        "rating": "🟡觀望",
        "suggestion": "鋼鐵景氣復甦中，成本壓力仍大，等待報價回升確認"
    },
    {
        "代碼": "1102", "名稱": "亞泥", "產業": "水泥",
        "industry_analysis": "亞泥為水泥龍頭，兩岸產能穩定，循環經濟佈局中",
        "news": "中國水泥需求疲軟、台泥上半年營收成長、循環經濟貢獻待觀察",
        "legal_person": "三大法人區間操作、外資偏空、投信賣超",
        "risks": "中國水泥需求放緩、循環補助不確定、環保成本增加、兩岸關係",
        "strengths": "兩岸佈局完整、循環經濟先驅、水泥需求穩定、低估值具保護",
        "rating": "🟡觀望",
        "suggestion": "中國水泥需求放緩，循環經濟貢獻待觀察，評等觀望"
    },
    {
        "代碼": "1301", "名稱": "台塑", "產業": "石化",
        "industry_analysis": "台塑為石化龍頭，太陽能/鋰電池材料多元布局",
        "news": "石化報價反彈、台塑營收恢復成長、AI醫療佈局新消息",
        "legal_person": "三大法人偏空操作、外資調節、投信減碼",
        "risks": "石化景氣循環、中國同業競爭、碳費負擔、新能源佈局需時",
        "strengths": "石化一貫化优势、太陽能/鋰電池材料多元、AI醫療布局、ESG評等佳",
        "rating": "🟡觀望",
        "suggestion": "石化景氣下行，多元佈局需時間發酵，保守看待"
    },
    {
        "代碼": "1476", "名稱": "儒鴻", "產業": "紡織/機能布",
        "industry_analysis": "儒鴻為機能布龍頭，運動品牌庫存調整完成，訂單回溫",
        "news": "Nike/Adidas訂單回溫、儒鴻越南廠效率提升、機能布需求回穩",
        "legal_person": "三大法人偏多、外資回補、投信認養",
        "risks": "新藥研發風險、藥證審批時間長、營收集中度高、臨床失敗風險",
        "strengths": "機能布全球領導、客戶品質優、越南新生產線效率、研發能力強",
        "rating": "🔵成長潛力",
        "suggestion": "庫存調整結束，品牌訂單回溫，評等上調至成長潛力"
    },
    {
        "代碼": "4743", "名稱": "合一", "產業": "生技/製藥",
        "industry_analysis": "合一為生技製藥，創新藥研發中，糖尿病新藥潛力大",
        "news": "合一糖尿病新藥ON101中國取證、授權金進帳、臨床數據正面",
        "legal_person": "三大法人偏多、投信作帳、內部人逢高賣出",
        "risks": "新藥上市時間不確定、醫藥法規變化、營收爆發需時間",
        "strengths": "糖尿病新藥潛力大、抗體技術平台完整、授權收益可期待、創新研發",
        "rating": "🟠留意",
        "suggestion": "新藥潛力大但營收集中，臨床進展需追蹤，風險報酬各半"
    },
    {
        "代碼": "2347", "名稱": "智邦", "產業": "網通",
        "industry_analysis": "智邦為網通設備龍頭，AI伺服器/交換器需求爆發",
        "news": "AI交換器需求旺、智邦白牌伺服器出貨放量、400G產品佔比提升",
        "legal_person": "三大法人大買、外資認養、投信追價",
        "risks": "晶片短缺風險、貿易戰影響、中國需求放緩、資本支出龐大",
        "strengths": "交換器市場領導、白牌伺服器需求爆發、400G產品量產、網路設備升級潮",
        "rating": "🔵成長潛力",
        "suggestion": "AI伺服器/交換器需求爆發，評等上調至成長潛力，目標價調升"
    },
    {
        "代碼": "5880", "名稱": "街口", "產業": "數位金融/電子支付",
        "industry_analysis": "街口為數位金融，電子支付滲透率提升，成長潛力大",
        "news": "街口支付滲透率提升、蝦皮支付競爭加劇、金融監理新規",
        "legal_person": "三大法人區間操作、內部人股份轉讓",
        "risks": "金管會監管趨嚴、競爭激烈、蝦皮支付競爭、獲利能力波動大",
        "strengths": "支付場景多元、便利商店深度合作、使用者基礎龐大、金融科技創新",
        "rating": "🔵成長潛力",
        "suggestion": "數位支付滲透率持續提升，成長潛力大，但波動也大"
    },
    {
        "代碼": "2734", "名稱": "晶華", "產業": "觀光/飯店",
        "industry_analysis": "晶華為觀光飯店龍頭，餐飲/住房營收復甦，陸客有望回升",
        "news": "來台旅客恢復、陸客開放進度、晶華住房率提升、餐飲收入成長",
        "legal_person": "三大法人偏多、外資回補、投信作帳行情",
        "risks": "觀光需求放緩、房租/人事成本上漲、陸客恢復緩慢、跨國競爭",
        "strengths": "國際觀光品牌、餐飲技術領先、位置優勢明顯、台北101 view加分",
        "rating": "🟡觀望",
        "suggestion": "觀光復甦中，陸客恢復緩慢，等待營收加速再介入"
    },
    {
        "代碼": "1229", "名稱": "聯華", "產業": "食品原料",
        "industry_analysis": "聯華為食品原料龍頭，烘焙需求穩定，聖瑪莉/簡七便民",
        "news": "烘焙景氣佳、聯華食品食品安全、口碑穩定、聖瑪莉展店中",
        "legal_person": "三大法人偏多操作、投信認養、外資買超",
        "risks": "原物料價格波動、食品安全事件、景氣影響消費、競爭加劇",
        "strengths": "食品安全口碑穩定、烘焙需求佳、轉投資收益穩、多角化經營",
        "rating": "🟢建議持有",
        "suggestion": "食品安全口碑穩定，烘焙需求佳，殖利率穩定，適合穩健持有"
    },
    {
        "代碼": "1909", "名稱": "永豐餘", "產業": "造紙",
        "industry_analysis": "永豐餘為造紙龍頭，工紙/紙箱需求溫和，ESG加分",
        "news": "工紙價格回穩、永豐餘紙器營收成長、ESG評等提升、循環經濟",
        "legal_person": "三大法人偏空操作、外資調節、投信觀望",
        "risks": "紙價波動、中國造紙業競爭、環保法規趨嚴、原料成本上漲",
        "strengths": "工紙龍頭地位穩、ESG評等領先、循環經濟佈局、紙類產品多元",
        "rating": "🟡觀望",
        "suggestion": "造紙景氣溫和，ESG加分需時間驗證，等待需求回溫"
    },
    {
        "代碼": "3054", "名稱": "安國", "產業": "IC設計/安全監控",
        "industry_analysis": "IC設計/安全監控，AI監控需求成長，安全監控晶片出貨放量",
        "news": "AI監控需求成長、安全監控晶片需求增溫",
        "legal_person": "三大法人買超",
        "risks": "PE偏高、營收集中度高",
        "strengths": "營收成長強勁+38%、AI監控題材加持",
        "rating": "🔵成長潛力",
        "suggestion": "營收成長強勁，AI監控需求帶動，逢低佈局"
    },
    {
        "代碼": "2495", "名稱": "普安", "產業": "存儲系統/伺服器",
        "industry_analysis": "存儲系統/伺服器，企業存儲需求持平，資料中心建設溫和",
        "news": "伺服器需求持平、資料中心建設溫和",
        "legal_person": "法人中性",
        "risks": "營收微幅下滑-0.4%、需求成長有限",
        "strengths": "PE適中36倍、存儲系統技術穩定",
        "rating": "🟡觀望",
        "suggestion": "營收持平，PE合理，區間操作為主"
    },
    {
        "代碼": "2408", "名稱": "南亞科", "產業": "DRAM記憶體",
        "industry_analysis": "DRAM記憶體，記憶體景氣回升，報價反彈中",
        "news": "記憶體景氣回升、DRAM報價反彈",
        "legal_person": "三大法人買超",
        "risks": "PE極高107倍、景氣循環波動大",
        "strengths": "DRAM報價反彈、記憶體需求回升",
        "rating": "🔴風險",
        "suggestion": "PE極高，記憶體景氣回升但風險大，謹慎操作"
    },
    {
        "代碼": "2344", "名稱": "華邦電", "產業": "Flash/DRAM記憶體",
        "industry_analysis": "Flash/DRAM記憶體，AI需求帶動，記憶體報價反彈",
        "news": "AI需求帶動Flash/DRAM、記憶體景氣回升",
        "legal_person": "三大法人買超",
        "risks": "PE極高106倍、營收基期低",
        "strengths": "營收大幅成長+42%、AI記憶體需求旺",
        "rating": "🔴風險",
        "suggestion": "營收成長驚人但PE極高，高風險注意"
    },
    {
        "代碼": "8299", "名稱": "群聯", "產業": "NAND Flash控制晶片",
        "industry_analysis": "NAND Flash控制晶片，AI應用帶動NAND需求，控制晶片出貨旺",
        "news": "AI應用帶動NAND需求、群聯控制晶片出貨放量",
        "legal_person": "三大法人買超",
        "risks": "PE偏高46倍、NAND價格波動",
        "strengths": "營收成長+81%驚人、NAND控制晶片領導、AI應用受惠",
        "rating": "🔵成長潛力",
        "suggestion": "成長型標的，AI應用帶動NAND需求，適合成長型投資"
    },
    {
        "代碼": "3532", "名稱": "台勝科", "產業": "矽晶圓/半導體",
        "industry_analysis": "矽晶圓/半導體，半導體景氣回溫，矽晶圓需求緩步復甦",
        "news": "半導體景氣回溫、矽晶圓需求復甦",
        "legal_person": "法人中性",
        "risks": "PE極高114倍、景氣復甦緩慢",
        "strengths": "產業復產業復甦中、矽晶圓供需改善",
        "rating": "🔴風險",
        "suggestion": "PE極高，半導體復甦需時間，高風險留意"
    },
]

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
    
    /* 區塊標題 */
    .section-header {
        border-bottom: 2px solid #30363d;
        padding-bottom: 8px;
        margin-bottom: 16px;
    }
    
    /* 訊息面卡片 */
    .news-card {
        background: #161b22;
        border-left: 3px solid #58a6ff;
        padding: 10px 15px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
    }
    
    .legal-card {
        background: #161b22;
        border-left: 3px solid #a371f7;
        padding: 10px 15px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* 風險/優點卡片 */
    .risk-card {
        background: linear-gradient(135deg, #21262d 0%, #30363d 100%);
        border-left: 3px solid #f85149;
        padding: 10px 15px;
        margin: 6px 0;
        border-radius: 0 8px 8px 0;
    }
    
    .strength-card {
        background: linear-gradient(135deg, #21262d 0%, #30363d 100%);
        border-left: 3px solid #3fb950;
        padding: 10px 15px;
        margin: 6px 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* 建議卡片 */
    .suggestion-card {
        background: linear-gradient(135deg, #1f4057 0%, #238636 100%);
        padding: 15px 20px;
        margin: 10px 0;
        border-radius: 10px;
        border: 1px solid #3fb950;
    }
    
    /* 側邊欄 */
    .css-1d391kg {
        background: #161b22;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        color: #58a6ff;
    }
    
    /* 產業分析區塊 */
    .industry-analysis {
        background: #1a2332;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# 標題
st.title("📊 20檔產業龍頭深度分析報告 V2")
st.markdown(f"**更新日期**: {datetime.now().strftime('%Y-%m-%d')} | 加入完整產業分析、消息面、評估依據、投資建議")

# 側邊欄 - 篩選功能
with st.sidebar:
    st.header("🎛️ 篩選功能")
    
    # 評等篩選
    rating_options = ["🟢建議持有", "🔵成長潛力", "🟡觀望", "🟠留意"]
    rating_filter = st.multiselect(
        "評等篩選",
        rating_options,
        default=rating_options
    )
    
    # 產業篩選
    industries = sorted(list(set([s["產業"] for s in stocks_data])))
    industry_filter = st.multiselect(
        "產業篩選",
        industries,
        default=industries
    )
    
    st.markdown("---")
    st.markdown("### 📈 評等分布")
    
    # 評等統計
    rating_counts = {}
    for s in stocks_data:
        rating = s["rating"]
        rating_counts[rating] = rating_counts.get(rating, 0) + 1
    
    for rating, count in sorted(rating_counts.items(), key=lambda x: x[1], reverse=True):
        st.write(f"{rating} **{count}檔**")
    
    st.markdown("---")
    st.markdown("### 📋 快速連結")
    st.write("🟢 [建議持有](#建議持有) (6檔)")
    st.write("🔵 [成長潛力](#成長潛力) (5檔)")
    st.write("🟡 [觀望](#觀望) (8檔)")
    st.write("🟠 [留意](#留意) (1檔)")

# 篩選數據
filtered_stocks = [s for s in stocks_data if s["rating"] in rating_filter and s["產業"] in industry_filter]

# 基本資訊卡片
st.markdown(f"## 📋 基本資料 | 篩選結果: **{len(filtered_stocks)}檔股票**")

# 創建股票卡片顯示
for idx, stock in enumerate(filtered_stocks):
    rating = stock["rating"]
    
    # 評等颜色映射
    if "🟢" in rating:
        rating_class = "rating-green"
        rating_bg = "border-left: 4px solid #3fb950;"
    elif "🔵" in rating:
        rating_class = "rating-blue"
        rating_bg = "border-left: 4px solid #58a6ff;"
    elif "🟡" in rating:
        rating_class = "rating-yellow"
        rating_bg = "border-left: 4px solid #d29922;"
    elif "🟠" in rating:
        rating_class = "rating-orange"
        rating_bg = "border-left: 4px solid #f0883e;"
    else:
        rating_class = "rating-red"
        rating_bg = "border-left: 4px solid #f85149;"
    
    st.markdown(f"""
    <div class="stock-card" style="{rating_bg}">
        <h3 style="margin:0;color:#e6edf3;">
            <span style="font-size:24px;">{stock['代碼']}</span> 
            <span style="margin-left:10px;">{stock['名稱']}</span>
            <span class="industry-tag" style="margin-left:15px;">{stock['產業']}</span>
        </h3>
        <span class="{rating_class}" style="font-size:20px;margin-top:10px;display:inline-block;">{rating}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 四欄位布局
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 🔍 產業分析")
        st.markdown(f"""
        <div class="industry-analysis">
            {stock['industry_analysis']}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📰 消息面")
        st.markdown(f"""
        <div class="news-card">
            <b>最新消息：</b><br>{stock['news']}
        </div>
        <div class="legal-card">
            <b>法人動向：</b><br>{stock['legal_person']}
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("### ⚖️ 評估依據")
        st.markdown(f"""
        <div class="risk-card">
            <b>⚠️ 風險點：</b><br>{stock['risks']}
        </div>
        <div class="strength-card" style="margin-top:10px;">
            <b>💪 優點：</b><br>{stock['strengths']}
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("### 💡 投資建議")
        st.markdown(f"""
        <div class="suggestion-card">
            <b>評等：{rating}</b><br><br>
            <span style="font-size:14px;color:#e6edf3;">{stock['suggestion']}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

# 總結區塊
st.markdown("## 📊 投資建議總結")

# 分類顯示
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 🟢 建議持有 (6檔)")
    for s in stocks_data:
        if "🟢" in s["rating"]:
            st.write(f"- **{s['代碼']} {s['名稱']}**")

with col2:
    st.markdown("### 🔵 成長潛力 (5檔)")
    for s in stocks_data:
        if "🔵" in s["rating"]:
            st.write(f"- **{s['代碼']} {s['名稱']}**")

with col3:
    st.markdown("### 🟡 觀望 (8檔)")
    for s in stocks_data:
        if "🟡" in s["rating"]:
            st.write(f"- **{s['代碼']} {s['名稱']}**")

with col4:
    st.markdown("### 🟠 留意 (1檔)")
    for s in stocks_data:
        if "🟠" in s["rating"]:
            st.write(f"- **{s['代碼']} {s['名稱']}**")

# 頁腳
st.markdown("---")
st.markdown("*本報告僅供參考，不構成投資建議。投資前請自行評估風險。*")