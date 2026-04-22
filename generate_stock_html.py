#!/usr/bin/env python3
"""台股每日推薦報告 - 靜態 HTML 生成器（綜合評分版）"""

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

# ============== 大盤指數 ==============
def get_market():
    indices = {}
    try:
        twii = yf.Ticker("^TWII")
        h = twii.history(period="5d")
        if not h.empty:
            p = h['Close'].iloc[-1]
            prev = h['Close'].iloc[-2] if len(h) >= 2 else p
            indices['加權指數'] = {'price': p, 'change': p - prev, 'pct': (p - prev) / prev * 100 if prev else 0}
    except:
        pass
    
    try:
        otc = yf.Ticker("^TaiwanOTC")
        h = otc.history(period="5d")
        if not h.empty:
            p = h['Close'].iloc[-1]
            prev = h['Close'].iloc[-2] if len(h) >= 2 else p
            indices['櫃買指數'] = {'price': p, 'change': p - prev, 'pct': (p - prev) / prev * 100 if prev else 0}
    except:
        pass
    
    try:
        vix = yf.Ticker("^VIX")
        h = vix.history(period="5d")
        if not h.empty:
            v = h['Close'].iloc[-1]
            indices['VIX'] = {'price': v, 'change': 0, 'pct': 0, 'level': '低風險' if v < 20 else '高風險'}
    except:
        pass
    
    return indices

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

def calc_bollinger(prices, period=20, std_dev=2):
    if len(prices) < period:
        return None, None, None
    ma = prices.rolling(window=period).mean().iloc[-1]
    std = prices.rolling(window=period).std().iloc[-1]
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    return upper, ma, lower

def calc_score(hist, market_indices=None):
    """計算綜合評分"""
    if hist.empty or len(hist) < 20:
        return 0, {}
    
    close = hist['Close'].dropna()
    if close.empty:
        return 0, {}
    
    price = close.iloc[-1]
    score = 0
    signals = []
    
    # === 大盤加分（如果VIX < 20）===
    vix_bonus = False
    if market_indices and 'VIX' in market_indices:
        vix = market_indices['VIX']['price']
        if vix < 20:
            score += 2
            vix_bonus = True
            signals.append(('VIX', f'{vix:.1f}', '✅ 低風險環境 +2'))
        else:
            signals.append(('VIX', f'{vix:.1f}', '⚠️ 高波動'))
    
    # === MA5 評分 ===
    ma5 = calc_ma(close, 5)
    if ma5:
        if price > ma5:
            score += 3
            signals.append(('MA5', f'{ma5:.0f}', '✅ 站上 +3'))
        else:
            signals.append(('MA5', f'{ma5:.0f}', '⚠️ 低於'))
    
    # === MA20 評分 ===
    ma20 = calc_ma(close, 20)
    if ma20:
        if price > ma20:
            score += 2
            signals.append(('MA20', f'{ma20:.0f}', '✅ 站上 +2'))
        else:
            signals.append(('MA20', f'{ma20:.0f}', '⚠️ 低於'))
    
    # === RSI 評分 ===
    rsi = calc_rsi(close)
    if rsi:
        if rsi < 30:
            score += 3
            signals.append(('RSI', f'{rsi:.1f}', '🔥 超賣低檔 +3'))
        elif rsi > 70:
            signals.append(('RSI', f'{rsi:.1f}', '⚠️ 超買區'))
        else:
            signals.append(('RSI', f'{rsi:.1f}', '正常'))
    
    # === KD 評分 ===
    k, d = calc_kd(hist)
    if k is not None and d is not None:
        if k < 30 and d < 30 and k > d:
            score += 3
            signals.append(('KD', f'K:{k:.0f} D:{d:.0f}', '🔥 低檔黃金交叉 +3'))
        elif k > 70 and d > 70 and k < d:
            signals.append(('KD', f'K:{k:.0f} D:{d:.0f}', '⚠️ 高檔死亡交叉'))
        else:
            signals.append(('KD', f'K:{k:.0f} D:{d:.0f}', '正常'))
    
    # === MACD 評分 ===
    macd, histogram = calc_macd(close)
    if macd is not None:
        if histogram > 0:
            score += 2
            signals.append(('MACD', f'{macd:.2f}', '✅ 多頭區 +2'))
        else:
            signals.append(('MACD', f'{macd:.2f}', '⚠️ 空頭區'))
    
    # === Bollinger Bands 評分 ===
    upper, middle, lower = calc_bollinger(close)
    if upper and lower:
        if price < lower:
            score += 2
            signals.append(('BB', f'{lower:.0f}', '🔥 跌破下軌超賣 +2'))
        elif price > upper:
            signals.append(('BB', f'{upper:.0f}', '⚠️ 突破上軌'))
        else:
            signals.append(('BB', '正常', '範圍內'))
    
    # === 成交量評分 ===
    vol = hist['Volume'].iloc[-1]
    vol_avg = hist['Volume'].iloc[-5:].mean() if len(hist) >= 5 else vol
    if vol > vol_avg * 1.5:
        score += 2
        signals.append(('成交量', f'{vol/1000000:.1f}M', '✅ 量增訊號 +2'))
    elif vol > vol_avg:
        score += 1
        signals.append(('成交量', f'{vol/1000000:.1f}M', '微量增加 +1'))
    else:
        signals.append(('成交量', f'{vol/1000000:.1f}M', '⚠️ 量縮'))
    
    return score, signals

def get_institutional_data(code):
    """嘗試取得法人買賣資料（使用變通方式）"""
    try:
        stock = yf.Ticker(code)
        info = stock.info
        # yfinance 不一定有心法人數據，這裡用週轉率變通
        if 'averageVolume' in info:
            vol = info.get('averageVolume', 0)
            return vol
    except:
        pass
    return None

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
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #0D1171 0%, #1a237e 100%); color: #E6EDF3; padding: 20px; min-height: 100vh; }}
.container {{ max-width: 1400px; margin: 0 auto; }}
header {{ text-align: center; padding: 30px 0; background: rgba(22, 27, 34, 0.8); border-radius: 16px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
h1 {{ font-size: 2.5rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }}
.subtitle {{ color: #8B949E; font-size: 1.1rem; }}
.market {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
.market-card {{ background: rgba(22, 27, 34, 0.9); border: 1px solid #30363D; border-radius: 12px; padding: 20px; text-align: center; transition: transform 0.2s; }}
.market-card:hover {{ transform: translateY(-3px); box-shadow: 0 4px 15px rgba(0,0,0,0.4); }}
.market-card h3 {{ color: #8B949E; font-size: 0.9rem; margin-bottom: 10px; }}
.market-card .price {{ font-size: 1.8rem; font-weight: bold; }}
.market-card .change {{ font-size: 1rem; margin-top: 5px; }}
.market-card.vix-low {{ border-color: #3FB950; }}
.market-card.vix-high {{ border-color: #F85149; }}
.signal-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; margin: 2px; }}
.signal-up {{ background: rgba(63, 185, 80, 0.2); color: #3FB950; }}
.signal-down {{ background: rgba(248, 81, 73, 0.2); color: #F85149; }}
.signal-neutral {{ background: rgba(210, 153, 34, 0.2); color: #D29922; }}
.top5 {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin: 30px 0; }}
@media (max-width: 1024px) {{ .top5 {{ grid-template-columns: repeat(3, 1fr); }} }}
@media (max-width: 600px) {{ .top5 {{ grid-template-columns: repeat(2, 1fr); }} }}
.top-card {{ background: linear-gradient(145deg, #161B22, #1f2937); border: 1px solid #30363D; border-radius: 12px; padding: 20px; text-align: center; position: relative; overflow: hidden; }}
.top-card::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #F85149, #D29922, #3FB950); }}
.top-card .rank {{ background: linear-gradient(135deg, #F85149, #D29922); color: white; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; margin: 0 auto 10px; font-weight: bold; font-size: 0.9rem; }}
.top-card .name {{ font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; }}
.top-card .code {{ color: #8B949E; font-size: 0.85rem; }}
.top-card .price {{ font-size: 1.6rem; margin: 10px 0; font-weight: bold; }}
.top-card .score {{ background: linear-gradient(135deg, #F85149, #D29922); color: white; border-radius: 20px; padding: 6px 16px; display: inline-block; font-weight: bold; font-size: 1rem; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: rgba(22, 27, 34, 0.9); border-radius: 12px; overflow: hidden; }}
th, td {{ padding: 12px 15px; text-align: left; }}
th {{ background: rgba(48, 54, 61, 0.8); color: #8B949E; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.5px; }}
tr {{ border-bottom: 1px solid #30363D; transition: background 0.2s; }}
tr:hover {{ background: rgba(48, 54, 61, 0.5); }}
tr:last-child {{ border-bottom: none; }}
.score-cell {{ font-weight: bold; padding: 6px 12px; border-radius: 8px; text-align: center; }}
.score-high {{ background: linear-gradient(135deg, #F85149, #D29922); color: white; }}
.score-mid {{ background: rgba(210, 153, 34, 0.3); color: #D29922; }}
.score-low {{ background: rgba(63, 185, 80, 0.2); color: #3FB950; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; margin: 1px; }}
.badge-up {{ background: rgba(248, 81, 73, 0.2); color: #F85149; }}
.badge-down {{ background: rgba(63, 185, 80, 0.2); color: #3FB950; }}
.badge-neutral {{ background: rgba(210, 153, 34, 0.2); color: #D29922; }}
.signals-cell {{ font-size: 0.8rem; line-height: 1.6; }}
footer {{ text-align: center; padding: 30px; color: #8B949E; font-size: 0.9rem; }}
.legend {{ background: rgba(22, 27, 34, 0.9); border-radius: 12px; padding: 20px; margin: 20px 0; }}
.legend h3 {{ margin-bottom: 10px; color: #E6EDF3; }}
.legend-item {{ display: flex; align-items: center; gap: 10px; margin: 5px 0; font-size: 0.9rem; }}
.buy-signal {{ color: #3FB950; font-weight: bold; }}
.sell-signal {{ color: #F85149; font-weight: bold; }}
</style>
</head>
<body>
<div class="container">
<header>
    <h1>📈 台股每日推薦報告</h1>
    <p class="subtitle">技術分析 | 綜合評分 | 更新時間: {update_time}</p>
</header>
'''

    # 大盤
    if market:
        html += '<div class="market">'
        for name, data in market.items():
            color = up_color if data.get('change', 0) > 0 else down_color
            card_class = 'market-card'
            if name == 'VIX':
                card_class += ' vix-low' if data.get('level') == '低風險' else ' vix-high'
            html += f'''
    <div class="{card_class}">
        <h3>{name}</h3>
        <div class="price">{data.get('price', 0):,.2f}</div>'''
            if name != 'VIX':
                html += f'''
        <div class="change" style="color: {color}">{data.get('change', 0):+,.2f} ({data.get('pct', 0):+.2f}%)</div>'''
            else:
                html += f'''
        <div class="change" style="color: {'#3FB950' if data.get('level') == '低風險' else '#F85149'}">{data.get('level', 'N/A')}</div>'''
            html += '</div>'
        html += '</div>'

    # 信號說明
    html += '''
<div class="legend">
<h3>📊 評分說明（分數越高 = 買進訊號越強）</h3>
<div class="legend-item"><span class="buy-signal">✅</span> MA5/MA20 站上均線 (+3/+2)</div>
<div class="legend-item"><span class="buy-signal">🔥</span> RSI < 30 超賣 (+3) / KD 低檔黃金交叉 (+3)</div>
<div class="legend-item"><span class="buy-signal">✅</span> MACD 多頭 (+2) / 成交量放大 (+2)</div>
<div class="legend-item"><span class="buy-signal">✅</span> VIX < 20 大盤低風險環境 (+2)</div>
<div class="legend-item"><span class="sell-signal">⚠️</span> RSI > 70 超買 / KD 高檔死亡交叉</div>
</div>
'''

    # Top 5
    html += '<h2 style="text-align:center; margin: 30px 0;">🏅 TOP 5 推薦</h2><div class="top5">'
    for i, row in enumerate(results.head(5).to_dict('records')):
        color = up_color if row['change'] > 0 else down_color
        score_class = 'score-high' if row['score'] >= 8 else 'score-mid' if row['score'] >= 5 else 'score-low'
        html += f'''
    <div class="top-card">
        <div class="rank">{i+1}</div>
        <div class="name">{row['name']}</div>
        <div class="code">{row['code']}</div>
        <div class="price" style="color: {color}">{row['price']:,.0f}</div>
        <div style="color: {color}">{row['change']:+,.2f} ({row['pct']:+.1f}%)</div>
        <div class="score">{row['score']} 分</div>
    </div>'''
    html += '</div>'

    # 完整排名
    html += '<h2 style="margin: 30px 0;">📋 完整排名</h2><table><thead><tr><th>#</th><th>代碼</th><th>名稱</th><th>現價</th><th>漲跌</th><th>總分</th><th>關鍵信號</th></tr></thead><tbody>'
    for _, row in results.iterrows():
        color = up_color if row['change'] > 0 else down_color
        score_class = 'score-high' if row['score'] >= 8 else 'score-mid' if row['score'] >= 5 else 'score-low'
        
        # 信號顯示
        signals_html = ''
        buy_count = 0
        for sig in row['signals'][:4]:
            if '✅' in sig[2] or '🔥' in sig[2]:
                signals_html += f'<span class="badge badge-up">{sig[0]}:{sig[1]}</span> '
                buy_count += 1
            elif '⚠️' in sig[2]:
                signals_html += f'<span class="badge badge-neutral">{sig[0]}:{sig[1]}</span> '
            else:
                signals_html += f'<span class="badge badge-down">{sig[0]}:{sig[1]}</span> '
        
        html += f'''<tr>
    <td><strong>{row['rank']}</strong></td>
    <td>{row['code']}</td>
    <td><strong>{row['name']}</strong></td>
    <td style="color: {color}; font-weight: bold;">{row['price']:,.0f}</td>
    <td style="color: {color};">{row['change']:+,.2f} ({row['pct']:+.1f}%)</td>
    <td><span class="score-cell {score_class}">{row['score']}</span></td>
    <td class="signals-cell">{signals_html}</td>
</tr>'''
    html += '</tbody></table>'

    html += '''
<footer>
    <p>📈 台股每日推薦報告 | 資料來源: Yahoo Finance | 每小時更新</p>
    <p>本報告僅供參考，不构成投資建議。分數高不代表一定漲，請注意風險。</p>
</footer>
</div>
</body>
</html>'''
    return html

# ============== 主程式 ==============
def main():
    print("📈 開始生成台股每日推薦報告（綜合評分版）...")
    
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
            score, signals = calc_score(hist, market)
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
                'signals': signals
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
        buy_signals = [s for s in row['signals'] if '✅' in s[2] or '🔥' in s[2]]
        sig_str = ', '.join([s[0] for s in buy_signals[:3]])
        print(f"  #{row['rank']} {row['name']} ({row['code']}) - {row['price']:,.0f} ({row['change']:+,.2f}) ⭐{row['score']}分 | {sig_str}")
    
    return df

if __name__ == '__main__':
    main()