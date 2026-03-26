#!/usr/bin/env python3
"""
龍龍虛擬操盤每日檢查腳本
- 檢查持股狀況
- 計算損益
- 輸出報告
"""

import yfinance as yf
import json
from datetime import datetime

# 持股資料
positions = {
    '6669': {'name': '緯穎', 'shares': 10, 'buy_price': 3780},
    '2317': {'name': '鴻海', 'shares': 100, 'buy_price': 198.5},
    '2603': {'name': '長榮', 'shares': 200, 'buy_price': 204},
}

def check_positions():
    """檢查持股並輸出報告"""
    print(f"=== 🦞 龍龍虛擬操盤 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")
    
    total_cost = 0
    total_value = 0
    
    for code, pos in positions.items():
        try:
            ticker = yf.Ticker(f"{code}.TW")
            hist = ticker.history(period="1d")
            if len(hist) > 0:
                current_price = hist['Close'].iloc[-1]
                cost = pos['shares'] * pos['buy_price']
                value = pos['shares'] * current_price
                profit = value - cost
                profit_pct = (profit / cost) * 100
                
                total_cost += cost
                total_value += value
                
                emoji = "🔴" if profit >= 0 else "🟢"
                print(f"{code} {pos['name']}: ${pos['buy_price']} → ${current_price:.2f}")
                print(f"   {emoji} 損益: ${profit:+,.0f} ({profit_pct:+.1f}%)\n")
        except Exception as e:
            print(f"{code}: 無法取得資料 - {e}\n")
    
    total_profit = total_value - total_cost
    cash = 100000 - total_cost
    total_assets = cash + total_value
    
    print("-" * 40)
    print(f"總成本: ${total_cost:,.0f}")
    print(f"總市值: ${total_value:,.0f}")
    print(f"總損益: ${total_profit:+,.0f}")
    print(f"報酬率: {(total_profit/total_cost)*100:+.2f}%")
    print(f"\n💰 現金: ${cash:,.0f}")
    print(f"💎 總資產: ${total_assets:,.0f}")
    
    # 決策
    print("\n=== 🦞 龍龍的決策 ===")
    
    # 檢查是否需要停損
    for code, pos in positions.items():
        try:
            ticker = yf.Ticker(f"{code}.TW")
            hist = ticker.history(period="1d")
            if len(hist) > 0:
                current_price = hist['Close'].iloc[-1]
                profit_pct = ((current_price / pos['buy_price']) - 1) * 100
                
                if profit_pct < -15:
                    print(f"⚠️ {code} 跌幅超過15%，建議停損！")
                elif profit_pct < -10:
                    print(f"⚠️ {code} 跌幅超過10%，密切關注！")
                elif profit_pct > 20:
                    print(f"📢 {code} 漲幅超過20%，考慮部分獲利了結！")
        except:
            pass
    
    print("\n結論：繼續持有，等待反彈！💪")

if __name__ == "__main__":
    check_positions()
