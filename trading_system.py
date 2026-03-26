#!/usr/bin/env python3
"""
龍龍虛擬操盤系統
- 讀取目前持股和現金
- 記錄每次買賣
"""

import json
import os
from datetime import datetime

POSITIONS_FILE = "/Users/yhlut_tsmc/.openclaw/workspace/streamlit-dashboards/positions.json"
HISTORY_FILE = "/Users/yhlut_tsmc/.openclaw/workspace/streamlit-dashboards/trading_history.json"

def load_positions():
    """載入目前持股"""
    if os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"cash": 100000, "positions": {}}

def save_positions(data):
    """儲存持股"""
    data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    with open(POSITIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_history():
    """載入歷史記錄"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(history):
    """儲存歷史記錄"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def buy(code, name, price, shares, reason):
    """買入"""
    data = load_positions()
    history = load_history()
    
    total_cost = price * shares
    
    if total_cost > data['cash']:
        return False, "現金不足"
    
    # 扣掉現金
    data['cash'] -= total_cost
    
    # 更新持股
    if code in data['positions']:
        # 加權平均
        old_shares = data['positions'][code]['shares']
        old_price = data['positions'][code]['avg_price']
        new_shares = old_shares + shares
        new_price = (old_shares * old_price + shares * price) / new_shares
        data['positions'][code] = {"name": name, "shares": new_shares, "avg_price": new_price}
    else:
        data['positions'][code] = {"name": name, "shares": shares, "avg_price": price}
    
    # 記錄歷史
    history.append({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'action': '買入',
        'code': code,
        'name': name,
        'price': price,
        'shares': shares,
        'reason': reason,
    })
    
    save_positions(data)
    save_history(history)
    return True, f"買入 {code} {shares}股 @ ${price}"

def sell(code, price, shares):
    """賣出"""
    data = load_positions()
    history = load_history()
    
    if code not in data['positions']:
        return False, "沒有持股"
    
    if data['positions'][code]['shares'] < shares:
        return False, "持股不足"
    
    # 賣出變現
    total_value = price * shares
    data['cash'] += total_value
    
    # 更新持股
    data['positions'][code]['shares'] -= shares
    if data['positions'][code]['shares'] == 0:
        del data['positions'][code]
    
    # 記錄歷史
    name = data['positions'].get(code, {}).get('name', code)
    history.append({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'action': '賣出',
        'code': code,
        'name': name,
        'price': price,
        'shares': shares,
        'reason': '',
    })
    
    save_positions(data)
    save_history(history)
    return True, f"賣出 {code} {shares}股 @ ${price}"

def get_status():
    """取得目前狀態"""
    data = load_positions()
    return data

# 測試
if __name__ == "__main__":
    status = get_status()
    print(f"=== 🦞 龍龍目前狀態 ===")
    print(f"現金: ${status['cash']:,}")
    print(f"持股:")
    for code, pos in status['positions'].items():
        print(f"  {code} {pos['name']}: {pos['shares']}股 @ ${pos['avg_price']}")
