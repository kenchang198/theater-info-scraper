#!/usr/bin/env python3
"""
映画詳細ページの構造を解析するスクリプト
"""

import requests
from bs4 import BeautifulSoup
import sys

def analyze_movie_detail(url):
    """映画詳細ページを解析して情報を抽出"""
    print(f"解析中: {url}\n")
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # タイトル情報を探す
        print("=== タイトル情報 ===")
        for h1 in soup.find_all('h1'):
            print(f"h1: {h1.get_text(strip=True)}")
        for h2 in soup.find_all('h2'):
            text = h2.get_text(strip=True)
            if len(text) < 100:  # 長すぎるテキストは除外
                print(f"h2: {text}")
        
        # 原題を探す（英語タイトル）
        print("\n=== 原題の可能性がある要素 ===")
        # 一般的なパターン
        for pattern in ['原題', 'Original Title', 'English Title', '英題']:
            elements = soup.find_all(text=lambda t: pattern in str(t))
            for elem in elements:
                parent = elem.parent
                if parent:
                    print(f"{pattern}付近: {parent.get_text(strip=True)[:200]}")
        
        # 英語っぽいタイトルを探す
        import re
        english_pattern = re.compile(r'^[A-Za-z\s\-\':,\.!?]+$')
        for elem in soup.find_all(['p', 'div', 'span']):
            text = elem.get_text(strip=True)
            if 10 < len(text) < 100 and english_pattern.match(text):
                print(f"英語テキスト: {text}")
        
        # 製作年を探す
        print("\n=== 製作年情報 ===")
        year_pattern = re.compile(r'(19\d{2}|20\d{2})年')
        for match in year_pattern.finditer(soup.get_text()):
            context_start = max(0, match.start() - 20)
            context_end = min(len(soup.get_text()), match.end() + 20)
            context = soup.get_text()[context_start:context_end]
            print(f"年情報: ...{context}...")
        
        # 公式サイトリンクを探す
        print("\n=== 公式サイトリンク ===")
        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True).lower()
            href = a['href']
            if any(keyword in text for keyword in ['公式', 'official', 'オフィシャル']):
                print(f"リンクテキスト: {a.get_text(strip=True)}")
                print(f"URL: {href}")
            elif 'official' in href or 'movie' in href:
                if not href.startswith('/'):  # 内部リンクを除外
                    print(f"外部リンク: {href} (テキスト: {a.get_text(strip=True)})")
        
        # メタデータを探す
        print("\n=== メタデータ ===")
        for meta in soup.find_all('meta'):
            if meta.get('property') or meta.get('name'):
                content = meta.get('content', '')
                if content and len(content) < 200:
                    print(f"{meta.get('property') or meta.get('name')}: {content}")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    # デフォルトURL（最新の映画詳細ページ）
    default_url = "https://qualite.musashino-k.jp/movies/4695/"
    
    url = sys.argv[1] if len(sys.argv) > 1 else default_url
    analyze_movie_detail(url)