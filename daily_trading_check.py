#!/usr/bin/env python3
"""
龍龍虛擬操盤 - 進階版
- 讀取 positions.json 的持股和現金
- 技術分析買賣點判斷
- 自動交易決策
- Discord 推播通知
"""

import yfinance as yf
import json
import os
import math
from datetime import datetime

POSITIONS_FILE = "/Users/yhlut_tsmc/.openclaw/workspace/streamlit-dashboards/positions.json"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")

def load_positions():
    """載入持股資料"""
    if os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"cash": 100000, "positions": {}}

def save_positions(data):
    """儲存持股資料"""
    with open(POSITIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_stock_info(code):
    """取得股票資料"""
    try:
        ticker = yf.Ticker(f"{code}.TW")
        hist = ticker.history(period="5d")
        if len(hist) == 0:
            return None
        
        current_price = hist['Close'].iloc[-1]
        
        # 計算簡單均線
        if len(hist) >= 5:
            ma5 = hist['Close'].tail(5).mean()
        else:
            ma5 = current_price
            
        if len(hist) >= 20:
            ma20 = hist['Close'].tail(20).mean()
        else:
            ma20 = current_price
            
        # 計算 RSI (14天)
        if len(hist) >= 15:
            delta = hist['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
            if loss != 0:
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 100
        else:
            rsi = 50
            
        return {
            'price': current_price,
            'ma5': ma5,
            'ma20': ma20,
            'rsi': rsi,
            'hist': hist
        }
    except Exception as e:
        print(f"  ⚠️ {code} 取得資料失敗: {e}")
        return None

def should_buy(code, info, pos_data):
    """判斷是否應該買入"""
    price = info['price']
    ma5 = info['ma5']
    ma20 = info['ma20']
    rsi = info['rsi']
    
    # 買入條件：
    # 1. 股價站上 MA5 且 MA5 > MA20 (多頭排列)
    # 2. RSI < 40 (超賣，反彈機會)
    # 3. 股價低於成本價 5% 以上 (撿便宜)
    
    conditions = []
    if price > ma5 and ma5 > ma20:
        conditions.append("多頭排列")
    if rsi < 40:
        conditions.append(f"RSI 超賣({rsi:.0f})")
    if pos_data and price < pos_data['avg_price'] * 0.95:
        conditions.append("低於成本價")
        
    return conditions

def should_sell(code, info, pos_data):
    """判斷是否應該賣出"""
    price = info['price']
    ma5 = info['ma5']
    ma20 = info['ma20']
    rsi = info['rsi']
    cost = pos_data['avg_price'] if pos_data else price
    profit_pct = ((price / cost) - 1) * 100
    
    conditions = []
    
    # 賣出條件：
    # 1. RSI > 70 (超買)
    # 2. 股價跌破 MA5 且 MA5 < MA20 (空頭排列)
    # 3. 獲利超過 20%
    # 4. 虧損超過 15% (停損)
    
    if rsi > 70:
        conditions.append(f"RSI 超買({rsi:.0f})")
    if price < ma5 and ma5 < ma20:
        conditions.append("空頭排列")
    if profit_pct > 20:
        conditions.append(f"獲利了結({profit_pct:.1f}%)")
    if profit_pct < -15:
        conditions.append(f"停損({profit_pct:.1f}%)")
        
    return conditions

def execute_trade(data, action, code, name, shares, price):
    """執行交易"""
    if action == 'buy':
        cost = shares * price
        if data['cash'] >= cost:
            data['cash'] -= cost
            if code in data['positions']:
                old_pos = data['positions'][code]
                total_shares = old_pos['shares'] + shares
                new_avg = (old_pos['shares'] * old_pos['avg_price'] + cost) / total_shares
                data['positions'][code] = {
                    'name': name,
                    'shares': total_shares,
                    'avg_price': new_avg
                }
            else:
                data['positions'][code] = {
                    'name': name,
                    'shares': shares,
                    'avg_price': price
                }
            return True, f"✅ 買入 {code} {name} {shares}股 @ ${price}"
        return False, f"❌ 現金不足，無法買入 {code}"
    
    elif action == 'sell':
        if code in data['positions'] and data['positions'][code]['shares'] >= shares:
            data['positions'][code]['shares'] -= shares
            revenue = shares * price
            data['cash'] += revenue
            if data['positions'][code]['shares'] == 0:
                del data['positions'][code]
            return True, f"✅ 賣出 {code} {name} {shares}股 @ ${price}"
        return False, f"❌ 持股不足，無法賣出 {code}"
    
    return False, "未知動作"

def send_discord_message(message):
    """發送 Discord 訊息"""
    if not DISCORD_WEBHOOK:
        return
    
    import urllib.request
    import json as json_lib
    
    data = {
        "content": message
    }
    req = urllib.request.Request(
        DISCORD_WEBHOOK,
        data=json_lib.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as e:
        print(f"Discord 發送失敗: {e}")

def check_and_trade():
    """檢查持股並執行交易"""
    data = load_positions()
    positions = data.get("positions", {})
    cash = data.get("cash", 100000)
    
    report = f"=== 🦞 龍龍虛擬操盤 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n\n"
    
    total_cost = 0
    total_value = cash
    trades = []
    
    for code, pos in positions.items():
        info = get_stock_info(code)
        if info is None:
            continue
            
        current_price = info['price']
        cost = pos['shares'] * pos['avg_price']
        value = pos['shares'] * current_price
        profit = value - cost
        profit_pct = (profit / cost) * 100
        
        total_cost += cost
        total_value += value
        
        emoji = "🔴" if profit >= 0 else "🟢"
        report += f"{code} {pos['name']}: ${pos['avg_price']} → ${current_price:.0f}\n"
        report += f"   {emoji} 損益: ${profit:+,.0f} ({profit_pct:+.1f}%)\n"
        report += f"   📊 RSI: {info['rsi']:.0f}, MA5: ${info['ma5']:.0f}, MA20: ${info['ma20']:.0f}\n\n"
        
        # 檢查賣出信號
        sell_reason = should_sell(code, info, pos)
        if sell_reason:
            report += f"   ⚠️ 賣出信號: {', '.join(sell_reason)}\n"
            # 如果跌幅超過 15%，建議停損
            if profit_pct < -15:
                trades.append(('sell', code, pos['name'], pos['shares'], current_price))
                report += f"   🚨 執行停損！\n"
        
        # 檢查買入信號
        buy_conditions = should_buy(code, info, pos)
        if buy_conditions:
            report += f"   💡 買入關注: {', '.join(buy_conditions)}\n"
    
    # 現金加碼買入強勢股
    # 如果有閒置現金且市場有機會，考慮加碼
    available_cash = cash
    
    # 這裡可以擴充：從財報資料庫找出被低估的股票
    # 目前先記錄下來
    
    stock_profit = total_value - cash
    total_profit = stock_profit - total_cost
    report += "-" * 40 + "\n"
    report += f"💰 現金: ${cash:,.0f}\n"
    report += f"💎 總市值: ${total_value:,.0f}\n"
    report += f"📊 未實現損益: ${total_profit:+,.0f}\n"
    report += f"📈 總報酬率: {((total_value / 200000) - 1) * 100:+.2f}%\n\n"
    
    # 龍龍的決策
    report += "=== 🦞 龍龍的決策 ===\n"
    
    # 根據綜合判斷給出建議
    if total_profit < -5000:
        report += "⚠️ 虧損過大，維持觀望，不輕舉妄動\n"
    elif total_profit > 5000:
        report += "📢 獲利不錯，可以考慮部分收割\n"
    else:
        report += "💪 持續持有，等待最佳時機\n"
    
    report += "\n結論：繼續持有，等待反彈！💪"
    
    # 執行交易
    for action, code, name, shares, price in trades:
        success, msg = execute_trade(data, action, code, name, shares, price)
        report += f"\n{msg}"
        if success:
            save_positions(data)
    
    print(report)
    send_discord_message(report)
    
    return data

if __name__ == "__main__":
    check_and_trade()