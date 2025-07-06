#!/usr/bin/env python
"""
TMDb API テストスクリプト
TMDb APIの動作を単体でテストし、問題を診断します
"""

import os
import sys
import logging
from dotenv import load_dotenv

# プロジェクトのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'theater_scraper'))

from theater_scraper.tmdb_client import TMDbClient

# 環境変数を読み込み
load_dotenv()

# ログレベルをDEBUGに設定
logging.basicConfig(level=logging.DEBUG)


def test_search_movies():
    """様々な映画タイトルでTMDb APIをテスト"""
    
    # テスト用の映画タイトル
    test_titles = [
        # 日本語タイトル
        "千と千尋の神隠し",
        "君の名は。",
        "シン・ゴジラ",
        "東京物語",
        "羅生門",
        
        # 英語タイトル
        "The Shawshank Redemption",
        "Inception",
        "The Dark Knight",
        
        # 特殊なケース
        "もののけ姫",  # 日本のアニメ
        "パラサイト 半地下の家族",  # 韓国映画
        "アメリ",  # フランス映画
        
        # 新宿シネマカリテで上映されそうな作品
        "ドライブ・マイ・カー",
        "犬王",
        "アフターサン",
    ]
    
    print("=" * 80)
    print("TMDb API Test Script")
    print("=" * 80)
    
    # TMDbクライアントを初期化
    try:
        client = TMDbClient()
        print("✓ TMDb client initialized successfully")
        print(f"  Access token: {'***' + os.getenv('TMDB_ACCESS_TOKEN', '')[-4:] if os.getenv('TMDB_ACCESS_TOKEN') else 'NOT SET'}")
    except Exception as e:
        print(f"✗ Failed to initialize TMDb client: {e}")
        return
    
    print("\n" + "=" * 80)
    print("Testing movie searches:")
    print("=" * 80)
    
    # 各タイトルをテスト
    for i, title in enumerate(test_titles, 1):
        print(f"\n[{i}/{len(test_titles)}] Searching for: '{title}'")
        print("-" * 40)
        
        try:
            result = client.search_movie(title)
            
            if result:
                print(f"✓ Found: '{result.get('title')}' ({result.get('original_title')})")
                print(f"  Release date: {result.get('release_date', 'N/A')}")
                print(f"  TMDb ID: {result.get('id')}")
                print(f"  Poster path: {result.get('poster_path', 'None')}")
                if result.get('poster_path'):
                    poster_url = TMDbClient.get_poster_url(result['poster_path'])
                    print(f"  Full poster URL: {poster_url}")
            else:
                print(f"✗ No results found")
                
        except Exception as e:
            print(f"✗ Error: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 80)
    print("Test completed. Check tmdb_api.log for detailed logs.")
    print("=" * 80)


def test_specific_title():
    """特定のタイトルを詳細にテスト"""
    import json
    
    title = input("\nEnter a movie title to test (or press Enter to skip): ").strip()
    if not title:
        return
    
    print(f"\nDetailed test for: '{title}'")
    print("=" * 80)
    
    try:
        client = TMDbClient()
        
        # 通常検索
        print("\n1. Normal search:")
        result = client.search_movie(title)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("No results")
        
        # 年を指定して検索（例：2023年）
        print("\n2. Search with year 2023:")
        result = client.search_movie(title, year=2023)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("No results")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 基本テスト
    test_search_movies()
    
    # 追加の詳細テスト
    test_specific_title()