# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import os
import boto3
from botocore.exceptions import ClientError
from itemadapter import ItemAdapter
from theater_scraper.items import TheaterItem, MovieItem
from theater_scraper.tmdb_client import TMDbClient
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()


class DynamoDBPipeline:
    """DynamoDB Local にデータを保存するパイプライン"""
    
    def __init__(self, dynamodb_endpoint='http://localhost:8000'):
        self.dynamodb_endpoint = dynamodb_endpoint
        self.dynamodb = None
    
    def open_spider(self, spider):
        """スパイダー開始時の初期化"""
        self.dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=self.dynamodb_endpoint,
            region_name='ap-northeast-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        spider.logger.info(f"DynamoDB接続: {self.dynamodb_endpoint}")
    
    def process_item(self, item, spider):
        """アイテムをDynamoDBに保存"""
        adapter = ItemAdapter(item)
        
        try:
            if isinstance(item, TheaterItem):
                self._save_theater_item(adapter, spider)
            elif isinstance(item, MovieItem):
                self._save_movie_item(adapter, spider)
            else:
                spider.logger.warning(f"未知のアイテムタイプ: {type(item)}")
                
        except ClientError as e:
            spider.logger.error(f"DynamoDB保存エラー: {e}")
            raise
        
        return item
    
    def _save_theater_item(self, adapter, spider):
        """映画館アイテムをTheaterTableに保存"""
        table = self.dynamodb.Table('TheaterTable')
        
        item_data = {
            'theater_id': adapter.get('theater_id'),
            'name': adapter.get('name'),
            'official_url': adapter.get('official_url'),
            'last_updated': adapter.get('last_updated')
        }
        
        table.put_item(Item=item_data)
        spider.logger.info(f"映画館保存: {item_data['name']}")
    
    def _save_movie_item(self, adapter, spider):
        """映画アイテムをMovieTableに保存 (detail_urlベースで上書き)"""
        table = self.dynamodb.Table('MovieTable')
        
        # detail_urlをプライマリキーとして使用
        detail_url = adapter.get('detail_url')
        
        item_data = {
            'detail_url': detail_url,  # プライマリキー
            'theater_id': adapter.get('theater_id'),
            'title': adapter.get('title'),
            'synopsis': adapter.get('synopsis') or '',
            'created_at': adapter.get('created_at'),
            'updated_at': adapter.get('updated_at')
        }
        
        # 新しいフィールドを追加
        if adapter.get('original_title'):
            item_data['original_title'] = adapter.get('original_title')
        if adapter.get('release_year'):
            item_data['release_year'] = adapter.get('release_year')
        if adapter.get('official_website'):
            item_data['official_website'] = adapter.get('official_website')
        
        # TMDb関連フィールドがあれば追加
        if adapter.get('tmdb_id'):
            item_data['tmdb_id'] = adapter.get('tmdb_id')
        if adapter.get('tmdb_poster_path'):
            item_data['tmdb_poster_path'] = adapter.get('tmdb_poster_path')
        
        # put_itemは既存レコードを自動的に上書きする
        table.put_item(Item=item_data)
        spider.logger.info(f"映画保存: {item_data['title']} (year: {adapter.get('release_year')}, official: {adapter.get('official_website')})")


class ValidationPipeline:
    """データ検証パイプライン"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        if isinstance(item, TheaterItem):
            required_fields = ['theater_id', 'name', 'official_url']
        elif isinstance(item, MovieItem):
            required_fields = ['detail_url', 'theater_id', 'title']
        else:
            return item
        
        # 必須フィールドチェック
        for field in required_fields:
            if not adapter.get(field):
                spider.logger.error(f"必須フィールドが空です: {field}")
                raise ValueError(f"必須フィールドが空です: {field}")
        
        return item


class TMDbPipeline:
    """TMDb APIから映画のポスター画像情報を取得するパイプライン"""
    
    def __init__(self):
        self.tmdb_client = None
        self.enabled = False
    
    def open_spider(self, spider):
        """スパイダー開始時の初期化"""
        # 環境変数でTMDb機能の有効/無効を制御
        access_token = os.getenv('TMDB_ACCESS_TOKEN')
        spider.logger.info(f"TMDb Pipeline initialization - Token present: {bool(access_token)}")
        
        if access_token:
            try:
                self.tmdb_client = TMDbClient(access_token)
                self.enabled = True
                spider.logger.info("✓ TMDb API pipeline enabled successfully")
            except ValueError as e:
                spider.logger.warning(f"✗ TMDb API pipeline disabled: {e}")
                self.enabled = False
        else:
            spider.logger.warning("✗ TMDb API pipeline disabled (TMDB_ACCESS_TOKEN not set)")
            spider.logger.info("Please set TMDB_ACCESS_TOKEN in .env file to enable TMDb integration")
    
    def process_item(self, item, spider):
        """MovieItemの場合のみTMDb APIから画像情報を取得"""
        # TMDbが無効な場合はスキップ
        if not self.enabled or not isinstance(item, MovieItem):
            return item
        
        adapter = ItemAdapter(item)
        title = adapter.get('title')
        original_title = adapter.get('original_title')
        release_year = adapter.get('release_year')
        
        if not title:
            spider.logger.warning("MovieItem has no title, skipping TMDb lookup")
            return item
        
        # タイトルの前処理（余分な空白を削除）
        title = title.strip()
        
        spider.logger.info(f"TMDb Pipeline processing: '{title}' (original: '{original_title}', year: {release_year})")
        
        try:
            movie_data = None
            
            # 1. 原題と製作年での検索を優先
            if original_title and release_year:
                spider.logger.debug(f"Searching with original title and year: '{original_title}' ({release_year})")
                movie_data = self.tmdb_client.search_movie(original_title, year=release_year)
                if movie_data:
                    spider.logger.info(f"✓ Found with original title and year")
            
            # 2. 原題のみで検索
            if not movie_data and original_title:
                spider.logger.debug(f"Searching with original title only: '{original_title}'")
                movie_data = self.tmdb_client.search_movie(original_title)
                if movie_data:
                    spider.logger.info(f"✓ Found with original title")
            
            # 3. 日本語タイトルと製作年で検索
            if not movie_data and release_year:
                spider.logger.debug(f"Searching with Japanese title and year: '{title}' ({release_year})")
                movie_data = self.tmdb_client.search_movie(title, year=release_year)
                if movie_data:
                    spider.logger.info(f"✓ Found with Japanese title and year")
            
            # 4. 日本語タイトルのみで検索（フォールバック）
            if not movie_data:
                spider.logger.debug(f"Searching with Japanese title only: '{title}'")
                movie_data = self.tmdb_client.search_movie(title)
                if movie_data:
                    spider.logger.info(f"✓ Found with Japanese title")
            
            if movie_data:
                # TMDb情報を追加
                tmdb_id = movie_data.get('id')
                poster_path = movie_data.get('poster_path')
                
                adapter['tmdb_id'] = tmdb_id
                
                if poster_path:
                    adapter['tmdb_poster_path'] = poster_path
                    spider.logger.info(
                        f"✓ TMDb match found: '{title}' -> "
                        f"'{movie_data.get('title')}' (ID: {tmdb_id}, Poster: {poster_path})"
                    )
                else:
                    spider.logger.info(
                        f"✓ TMDb match found (no poster): '{title}' -> "
                        f"'{movie_data.get('title')}' (ID: {tmdb_id})"
                    )
            else:
                spider.logger.warning(f"✗ No TMDb match for: '{title}'")
                
        except Exception as e:
            spider.logger.error(f"TMDb API error for '{title}': {type(e).__name__}: {e}")
            import traceback
            spider.logger.debug(traceback.format_exc())
        
        return item
