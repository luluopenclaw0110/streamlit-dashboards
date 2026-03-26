#!/usr/bin/env python3
"""
龍龍虛擬操盤記錄
記錄每次買賣決策
"""

import json
import os
from datetime import datetime

LOG_FILE = "/Users/yhlut_tsmc/.openclaw/workspace/streamlit-dashboards/trading_history.json"

def load_history():
    """載入歷史記錄"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(history):
    """儲存歷史記錄"""
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_record(action, code, name, price, shares, reason):
    """新增記錄"""
    history = load_history()
    record = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'action': action,  # 買入/賣出/持有
        'code': code,
        'name': name,
        'price': price,
        'shares': shares,
        'reason': reason,
    }
    history.append(record)
    save_history(history)
    return record

# 測試
if __name__ == "__main__":
    # 模擬今日決策記錄
    add_record('買入', '6669', '緯穎', 3780, 10, 'AI伺服器需求旺，ROE 48%')
    add_record('買入', '2317', '鴻海', 198.5, 100, 'AI伺服器龍頭')
    add_record('買入', '2603', '長榮', 204, 200, '航運低點')
    
    print("=== 🦞 龍龍操盤歷史記錄 ===")
    for h in load_history():
        print(f"{h['date']} - {h['action']} {h['code']} {h['name']} ${h['price']} x {h['shares']}")
        print(f"   理由: {h['reason']}")
