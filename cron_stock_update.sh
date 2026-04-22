#!/bin/bash
# 台股每日報告 Cron 更新腳本
# 每天早上 8:00 自動生成並部署報告

cd /Users/yhlut_tsmc/.openclaw/workspace

# 生成報告
python3 generate_stock_html.py

# 部署到 GitHub Pages
git add html-report/index.html
git commit -m "chore: 自動更新 $(date '+%Y-%m-%d %H:%M')"
git subtree push --prefix=html-report origin gh-pages

echo "報告已更新: $(date)"