#!/usr/bin/env python3
"""台股每日推薦報告 - 靜態 HTML 生成器"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import json

# ============== 股票清單（20檔）=============
STOCKS = [
    ('2330.TW', '台積電'), ('2317.TW', '鴻海'), ('2313.TW', '華通'), ('2887.TW', '台新金'),
    ('2454.TW', '聯發科'), ('2303.TW', '聯電'), ('2377.TW', '聯米'), ('2451.TW', '研華'),
    ('2474.TW', '世紀'), ('2603.TW', '長榮'), ('2881.TW', '元大金'), ('2882.TW', '國泰金'),
    ('2891.TW', '中信金'), ('2002.TW', '中鋼'), ('1216.TW', '統一'), ('1702.TW', '南僑'),
    ('2201.TW', '裕融'), ('2707.TW', '晶華'), ('2727.TW', '王品'), ('3042.TW', '創見'),
]

# ============== 技術指標計算 ==============
def get_stock_data(code, period='20d'):
    try:
        stock = yf.Ticker(code)
        hist = stock.history(period=period)
        return hist
    except:
        return None

def calc_ma(prices, period):
    if len(prices) < period:
        return None
    return prices.rolling(window=period).mean().iloc[-1]

def calc_rsi(prices, period=14):
    if len(prices) < period:
        return None
    deltas = prices.diff()
    gain = deltas.where(deltas > 0, 0).rolling(window=period).mean()
    loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else None

def calc_kd(hist, k_period=9, d_period=3):
    if len(hist) < k_period:
        return None, None
    low_min = hist['Low'].rolling(window=k_period).min()
    high_max = hist['High'].rolling(window=k_period).max()
    rsv = (hist['Close'] - low_min) / (high_max - low_min) * 100
    rsv = rsv.fillna(50)
    k = rsv.rolling(window=d_period).mean().iloc[-1]
    d = pd.Series(k).rolling(window=d_period).mean().iloc[-1]
    return k if not np.isnan(k) else None, d if not np.isnan(d) else None

def calc_macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow:
        return None, None
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line.iloc[-1], histogram.iloc[-1]

def calc_score(hist):
    if hist.empty or len(hist) < 20:
        return 0, {}
    
    close = hist['Close'].dropna()
    if close.empty:
        return 0, {}
    
    price = close.iloc[-1]
    score = 0
    details = {}
    
    ma5 = calc_ma(close, 5)
    if ma5 and price > ma5:
        score += 3
        details['ma5'] = '✅'
    else:
        details['ma5'] = '⚠️'
    
    ma20 = calc_ma(close, 20)
    if ma20 and price > ma20:
        score += 2
        details['ma20'] = '✅'
    else:
        details['ma20'] = '⚠️'
    
    rsi = calc_rsi(close)
    if rsi:
        details['rsi'] = f'{rsi:.1f}'
        if rsi < 30:
            score += 3
            details['rsi_status'] = '超賣'
        elif rsi > 70:
            details['rsi_status'] = '超買'
        else:
            details['rsi_status'] = '正常'
    
    k, d = calc_kd(hist)
    if k is not None and d is not None:
        details['k'] = f'{k:.1f}'
        details['d'] = f'{d:.1f}'
        if k < 30 and d < 30 and k > d:
            score += 3
            details['kd_status'] = '黃金交叉'
        elif k > 70 and d > 70 and k < d:
            details['kd_status'] = '死亡交叉'
        else:
            details['kd_status'] = '-'
    
    macd, histogram = calc_macd(close)
    if macd is not None:
        details['macd'] = f'{macd:.2f}'
        if histogram > 0:
            score += 2
            details['macd_status'] = '✅'
        else:
            details['macd_status'] = '⚠️'
    
    vol = hist['Volume'].iloc[-1]
    vol_avg = hist['Volume'].iloc[-5:].mean() if len(hist) >= 5 else vol
    if vol > vol_avg * 1.5:
        score += 2
        details['vol_status'] = '量增'
    elif vol > vol_avg:
        score += 1
        details['vol_status'] = '微量'
    else:
        details['vol_status'] = '量縮'
    
    return score, details

# ============== 大盤指數 ==============
def get_market():
    indices = {}
    try:
        twii = yf.Ticker("^TWII")
        h = twii.history(period="5d")
        if not h.empty:
            p = h['Close'].iloc[-1]
            prev = h['Close'].iloc[-2] if len(h) >= 2 else p
            indices['加權'] = {'price': p, 'change': p - prev, 'pct': (p - prev) / prev * 100 if prev else 0}
    except:
        pass
    return indices

# ============== HTML 生成 ==============
def generate_html(results, market, update_time):
    up_color = '#F85149'
    down_color = '#3FB950'
    
    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>台股每日推薦報告</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0D1171; color: #E6EDF3; padding: 20px; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
header {{ text-align: center; padding: 30px 0; }}
h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
.subtitle {{ color: #8B949E; font-size: 1.1rem; }}
.market {{ display: flex; gap: 20px; justify-content: center; margin: 20px 0; }}
.market-card {{ background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 20px; text-align: center; min-width: 200px; }}
.market-card h3 {{ color: #8B949E; font-size: 0.9rem; margin-bottom: 10px; }}
.market-card .price {{ font-size: 2rem; font-weight: bold; }}
.market-card .change {{ font-size: 1.1rem; margin-top: 5px; }}
.top5 {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin: 30px 0; }}
.top-card {{ background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 20px; text-align: center; }}
.top-card .rank {{ background: #F85149; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; margin: 0 auto 10px; font-weight: bold; }}
.top-card .name {{ font-size: 1.2rem; font-weight: bold; margin-bottom: 5px; }}
.top-card .code {{ color: #8B949E; font-size: 0.9rem; }}
.top-card .price {{ font-size: 1.8rem; margin: 10px 0; }}
.top-card .score {{ background: #F85149; color: white; border-radius: 20px; padding: 5px 15px; display: inline-block; font-weight: bold; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #30363D; }}
th {{ background: #161B22; color: #8B949E; }}
tr:hover {{ background: #161B22; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }}
.badge-up {{ background: rgba(248, 81, 73, 0.2); color: #F85149; }}
.badge-down {{ background: rgba(63, 185, 80, 0.2); color: #3FB950; }}
.badge-neutral {{ background: rgba(210, 153, 34, 0.2); color: #D29922; }}
footer {{ text-align: center; padding: 30px; color: #8B949E; font-size: 0.9rem; }}
@media (max-width: 768px) {{ 
    .top5 {{ grid-template-columns: repeat(2, 1fr); }}
    .market {{ flex-direction: column; }}
}}
</style>
</head>
<body>
<div class="container">
<header>
    <h1>📈 台股每日推薦報告</h1>
    <p class="subtitle">技術分析 | 每日推薦 | 更新時間: {update_time}</p>
</header>
'''

    # 大盤
    if market:
        html += '<div class="market">'
        for name, data in market.items():
            color = up_color if data['change'] > 0 else down_color
            html += f'''
    <div class="market-card">
        <h3>{name}指數</h3>
        <div class="price">{data['price']:,.0f}</div>
        <div class="change" style="color: {color}">{data['change']:+,.0f} ({data['pct']:+.1f}%)</div>
    </div>'''
        html += '</div>'

    # Top 5
    html += '<h2 style="text-align:center; margin: 30px 0;">🏅 TOP 5 推薦</h2><div class="top5">'
    for i, row in enumerate(results.head(5).to_dict('records')):
        color = up_color if row['change'] > 0 else down_color
        html += f'''
    <div class="top-card">
        <div class="rank">{i+1}</div>
        <div class="name">{row['name']}</div>
        <div class="code">{row['code']}</div>
        <div class="price" style="color: {color}">{row['price']:,.0f}</div>
        <div style="color: {color}">{row['change']:+,.2f} ({row['pct']:+.1f}%)</div>
        <div class="score">⭐ {row['score']} 分</div>
    </div>'''
    html += '</div>'

    # 完整排名
    html += '<h2 style="margin: 30px 0;">📋 完整排名</h2><table><thead><tr><th>排名</th><th>代碼</th><th>名稱</th><th>現價</th><th>漲跌</th><th>總分</th><th>MA5</th><th>RSI</th><th>KD</th></tr></thead><tbody>'
    for _, row in results.iterrows():
        color = up_color if row['change'] > 0 else down_color
        d = row['details']
        kd_disp = f"K:{d.get('k','-')} D:{d.get('d','-')}" if 'k' in d else '-'
        html += f'''<tr>
    <td>#{row['rank']}</td>
    <td>{row['code']}</td>
    <td><strong>{row['name']}</strong></td>
    <td style="color: {color}">{row['price']:,.0f}</td>
    <td style="color: {color}">{row['change']:+,.2f} ({row['pct']:+.1f}%)</td>
    <td><span class="badge badge-up">⭐ {row['score']}</span></td>
    <td>{d.get('ma5', '-')}</td>
    <td>{d.get('rsi', '-')} {d.get('rsi_status', '')}</td>
    <td>{kd_disp} {d.get('kd_status', '')}</td>
</tr>'''
    html += '</tbody></table>'

    # 技術說明
    html += '''
<h2 style="margin: 30px 0;">📊 評分說明</h2>
<div style="background: #161B22; border-radius: 8px; padding: 20px; line-height: 1.8;">
<p><strong>MA5 / MA20:</strong> 站上均線 +3/+2 分，低於 ⚠️</p>
<p><strong>RSI:</strong> 低於 30 超賣 +3 分，高於 70 超買</p>
<p><strong>KD:</strong> 低檔黃金交叉 +3 分，高檔死亡交叉 ⚠️</p>
<p><strong>MACD:</strong> 柱狀正值 +2 分</p>
<p><strong>成交量:</strong> 量增 1.5 倍 +2 分</p>
</div>
'''

    html += f'''
<footer>
    <p>📈 台股每日推薦報告 | 資料來源: Yahoo Finance | 每小時更新</p>
    <p>本報告僅供參考，不构成投資建議</p>
</footer>
</div>
</body>
</html>'''
    return html

# ============== 主程式 ==============
def main():
    print("📈 開始生成台股每日推薦報告...")
    
    # 大盤
    print("取得大盤指數...")
    market = get_market()
    
    # 股票分析
    print("分析 20 檔股票...")
    results = []
    for code, name in STOCKS:
        print(f"  分析 {code} {name}...")
        hist = get_stock_data(code)
        if hist is not None and not hist.empty:
            score, details = calc_score(hist)
            price = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2] if len(hist) >= 2 else price
            change = price - prev
            pct = (change / prev) * 100 if prev != 0 else 0
            results.append({
                'code': code.replace('.TW', ''),
                'name': name,
                'price': price,
                'change': change,
                'pct': pct,
                'score': score,
                'details': details
            })
    
    # 排序
    df = pd.DataFrame(results)
    df = df.sort_values('score', ascending=False).reset_index(drop=True)
    df['rank'] = range(1, len(df) + 1)
    
    # 生成 HTML
    print("生成 HTML...")
    update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html = generate_html(df, market, update_time)
    
    # 寫入檔案
    output_path = '/Users/yhlut_tsmc/.openclaw/workspace/html-report/index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 報告已生成: {output_path}")
    
    # 印出 Top 5
    print("\n🏅 TOP 5 推薦:")
    for i, row in df.head(5).iterrows():
        print(f"  #{row['rank']} {row['name']} ({row['code']}) - {row['price']:,.0f} ({row['change']:+,.2f}) ⭐{row['score']}分")
    
    return df

if __name__ == '__main__':
    main()