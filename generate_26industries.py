#!/usr/bin/env python3
"""26檔產業龍頭深度分析報告 - 靜態 HTML 生成器"""

import json
from datetime import datetime

# 評等顏色
RATING_COLORS = {
    '🟢建議持有': '#3FB950',
    '🔵成長潛力': '#58A6FF', 
    '🟡觀望': '#D29922',
    '🟠留意': '#F0883E',
    '🔴風險': '#F85149',
}

def get_stock_card_html(stock):
    """產生單一股票的 HTML 卡片"""
    code = stock['code']
    name = stock['name']
    rating = stock.get('rating', '無評等')
    rating_color = stock.get('rating_color', '#8B949E')
    analysis = stock.get('analysis', '暂无产业分析资料')
    news = stock.get('news', '') or stock.get('suggestion', '暂无消息面资料')
    suggestion = stock.get('suggestion', '暂无投资建议')
    strengths = stock.get('strengths', '暂无优势资料')
    risks = stock.get('risks', '暂无风险资料')
    
    html = f'''
    <div class="stock-card" id="{code}">
        <div class="stock-header">
            <span class="stock-code">{code}</span>
            <span class="stock-name">{name}</span>
            <span class="rating-badge" style="background: {rating_color};">{rating}</span>
        </div>
        
        <div class="stock-section">
            <h3>📊 產業分析</h3>
            <p>{analysis}</p>
        </div>
        
        <div class="stock-section">
            <h3>📰 消息面</h3>
            <p>{news}</p>
        </div>
        
        <div class="stock-section">
            <h3>💡 投資建議</h3>
            <p>{suggestion}</p>
        </div>
        
        <div class="stock-section">
            <h3>🔍 評估依據</h3>
            <div class="strengths-risks">
                <div class="strengths">
                    <h4>優勢</h4>
                    <p>{strengths}</p>
                </div>
                <div class="risks">
                    <h4>風險</h4>
                    <p>{risks}</p>
                </div>
            </div>
        </div>
    </div>
    '''
    return html

def generate_html(data):
    """產生完整的 HTML 頁面"""
    stocks = data.get('stocks', [])
    
    # Group by rating for summary
    rating_groups = {}
    for s in stocks:
        r = s.get('rating', '無評等')
        if r not in rating_groups:
            rating_groups[r] = []
        rating_groups[r].append(s)
    
    # Rating order
    rating_order = ['🟢建議持有', '🔵成長潛力', '🟡觀望', '🟠留意', '🔴風險']
    
    # 計算各評等數量
    counts = {}
    for r in rating_order:
        counts[r] = len([s for s in stocks if s.get('rating', '') == r])
    
    update_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>26檔產業龍頭深度分析報告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            padding: 2rem 0;
            border-bottom: 2px solid rgba(255,255,255,0.1);
            margin-bottom: 2rem;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            color: #ffffff;
            margin-bottom: 0.5rem;
        }}
        
        .header p {{
            color: #a0a0a0;
        }}
        
        .summary {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            justify-content: center;
            margin-bottom: 2rem;
        }}
        
        .summary-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            text-align: center;
        }}
        
        .summary-card .count {{
            font-size: 2rem;
            font-weight: bold;
        }}
        
        .stock-card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            backdrop-filter: blur(10px);
        }}
        
        .stock-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .stock-code {{
            background: #2d3748;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: bold;
        }}
        
        .stock-name {{
            font-size: 1.5rem;
            font-weight: bold;
            flex-grow: 1;
        }}
        
        .rating-badge {{
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: bold;
            color: #fff;
        }}
        
        .stock-section {{
            margin-bottom: 1.5rem;
        }}
        
        .stock-section h3 {{
            color: #58a6ff;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }}
        
        .stock-section p {{
            color: #c0c0c0;
            line-height: 1.6;
        }}
        
        .strengths-risks {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }}
        
        .strengths, .risks {{
            background: rgba(255,255,255,0.03);
            padding: 1rem;
            border-radius: 8px;
        }}
        
        .strengths h4, .risks h4 {{
            margin-bottom: 0.5rem;
        }}
        
        .strengths h4 {{color: #3fb950;}}
        .risks h4 {{color: #f85149;}}
        
        @media (max-width: 768px) {{
            .strengths-risks {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem 0;
            color: #666;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin-top: 2rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 26檔產業龍頭深度分析報告</h1>
            <p>更新時間: {update_time}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="count" style="color: #3fb950;">{counts.get('🟢建議持有', 0)}</div>
                <div>建議持有</div>
            </div>
            <div class="summary-card">
                <div class="count" style="color: #58a6ff;">{counts.get('🔵成長潛力', 0)}</div>
                <div>成長潛力</div>
            </div>
            <div class="summary-card">
                <div class="count" style="color: #d29922;">{counts.get('🟡觀望', 0)}</div>
                <div>觀望</div>
            </div>
            <div class="summary-card">
                <div class="count" style="color: #f0883e;">{counts.get('🟠留意', 0)}</div>
                <div>留意</div>
            </div>
            <div class="summary-card">
                <div class="count" style="color: #f85149;">{counts.get('🔴風險', 0)}</div>
                <div>風險</div>
            </div>
        </div>
'''
    
    # 按評等排序顯示
    for rating in rating_order:
        if rating in rating_groups:
            color = RATING_COLORS.get(rating, '#fff')
            html += f'\n        <h2 style="color: {color}; margin: 2rem 0 1rem;">{rating}</h2>\n'
            for stock in rating_groups[rating]:
                html += get_stock_card_html(stock)
    
    html += '''
        <div class="footer">
            <p>本報告僅供參考，不構成投資建議。投資有風險，請審慎評估。</p>
        </div>
    </div>
</body>
</html>'''
    
    return html

def generate_simple_index_html(data):
    """產生首頁（連結到完整報告）"""
    stocks = data.get('stocks', [])
    update_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>26檔產業龍頭</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 2rem;
        }}
        .container {{ max-width: 800px; margin: 0 auto; text-align: center; }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #888; margin-bottom: 2rem; }}
        .btn {{
            display: inline-block;
            background: #58a6ff;
            color: #fff;
            padding: 1rem 2rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            margin: 1rem 0;
        }}
        .btn:hover {{ background: #3b8bff; }}
        .stock-list {{ text-align: left; margin-top: 2rem; }}
        .stock-item {{
            background: rgba(255,255,255,0.05);
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        .stock-item a {{ color: #58a6ff; text-decoration: none; }}
        .stock-item a:hover {{ text-decoration: underline; }}
        .rating {{ padding: 0.25rem 0.5rem; border-radius: 4px; color: #fff; font-size: 0.8rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 26檔產業龍頭</h1>
        <p class="subtitle">更新: {update_time}</p>
        
        <a href="26industries-report.html" class="btn">查看完整分析報告 →</a>
        
        <div class="stock-list">
            <h2 style="margin: 1.5rem 0;">股票清單</h2>
'''
    
    for s in stocks:
        rating = s.get('rating', '')
        rating_color = s.get('rating_color', '#666')
        html += f'''
            <div class="stock-item">
                <span class="stock-code">{s['code']}</span>
                <span class="stock-name">{s['name']}</span>
                <span class="rating" style="background:{rating_color};">{rating}</span>
            </div>'''
    
    html += '''
        </div>
    </div>
</body>
</html>'''
    
    return html

def main():
    print("📊 開始生成 26檔產業龍頭深度分析報告...")
    
    # 讀取股票資料
    with open('/Users/yhlut_tsmc/.openclaw/workspace/stock_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"共載入 {len(data['stocks'])} 檔股票")
    
    # 生成 HTML
    html = generate_html(data)
    
    # 寫入檔案
    output_path = '/Users/yhlut_tsmc/.openclaw/workspace/26industries-report.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 報告已生成: {output_path}")
    
    # 同時生成一個簡潔版本（首頁）
    simple_html = generate_simple_index_html(data)
    simple_path = '/Users/yhlut_tsmc/.openclaw/workspace/index.html'
    with open(simple_path, 'w', encoding='utf-8') as f:
        f.write(simple_html)
    
    print(f"✅ 精簡版首頁: {simple_path}")

if __name__ == '__main__':
    main()
