# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import boto3
from botocore.exceptions import ClientError
from itemadapter import ItemAdapter
from theater_scraper.items import TheaterItem, MovieItem


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
        """映画アイテムをMovieTableに保存"""
        table = self.dynamodb.Table('MovieTable')
        
        item_data = {
            'movie_id': adapter.get('movie_id'),
            'theater_id': adapter.get('theater_id'),
            'title': adapter.get('title'),
            'image_url': adapter.get('image_url') or '',
            'synopsis': adapter.get('synopsis') or '',
            'detail_url': adapter.get('detail_url'),
            'created_at': adapter.get('created_at'),
            'updated_at': adapter.get('updated_at')
        }
        
        table.put_item(Item=item_data)
        spider.logger.info(f"映画保存: {item_data['title']}")


class ValidationPipeline:
    """データ検証パイプライン"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        if isinstance(item, TheaterItem):
            required_fields = ['theater_id', 'name', 'official_url']
        elif isinstance(item, MovieItem):
            required_fields = ['movie_id', 'theater_id', 'title']
        else:
            return item
        
        # 必須フィールドチェック
        for field in required_fields:
            if not adapter.get(field):
                spider.logger.error(f"必須フィールドが空です: {field}")
                raise ValueError(f"必須フィールドが空です: {field}")
        
        return item
