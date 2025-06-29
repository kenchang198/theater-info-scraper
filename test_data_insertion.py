#!/usr/bin/env python3
"""
テストデータをDynamoDBに挿入してシステム動作確認
"""

import boto3
from datetime import datetime
import hashlib


def insert_test_data():
    """テストデータをDynamoDBに挿入"""
    
    # DynamoDB Local接続
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='ap-northeast-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    
    # テーブル取得
    theater_table = dynamodb.Table('TheaterTable')
    movie_table = dynamodb.Table('MovieTable')
    
    # テスト映画館データ
    test_theaters = [
        {
            'theater_id': 'test_theater_1',
            'name': 'テスト映画館1',
            'official_url': 'https://example.com/theater1',
            'last_updated': datetime.now().isoformat()
        },
        {
            'theater_id': 'test_theater_2', 
            'name': 'テスト映画館2',
            'official_url': 'https://example.com/theater2',
            'last_updated': datetime.now().isoformat()
        }
    ]
    
    # テスト映画データ
    test_movies = [
        {
            'movie_id': hashlib.md5('test_theater_1_映画A'.encode()).hexdigest(),
            'theater_id': 'test_theater_1',
            'title': '映画A',
            'image_url': 'https://example.com/images/movie_a.jpg',
            'synopsis': 'これは映画Aのあらすじです。テスト用のダミーデータです。',
            'detail_url': 'https://example.com/movies/movie_a',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        },
        {
            'movie_id': hashlib.md5('test_theater_1_映画B'.encode()).hexdigest(),
            'theater_id': 'test_theater_1',
            'title': '映画B',
            'image_url': 'https://example.com/images/movie_b.jpg',
            'synopsis': 'これは映画Bのあらすじです。感動的なストーリーが展開されます。',
            'detail_url': 'https://example.com/movies/movie_b',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        },
        {
            'movie_id': hashlib.md5('test_theater_2_映画C'.encode()).hexdigest(),
            'theater_id': 'test_theater_2',
            'title': '映画C',
            'image_url': 'https://example.com/images/movie_c.jpg',
            'synopsis': 'これは映画Cのあらすじです。アクション満載の作品です。',
            'detail_url': 'https://example.com/movies/movie_c',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    ]
    
    # 映画館データ挿入
    print("映画館データを挿入中...")
    for theater in test_theaters:
        theater_table.put_item(Item=theater)
        print(f"  - {theater['name']} を挿入")
    
    # 映画データ挿入
    print("\n映画データを挿入中...")
    for movie in test_movies:
        movie_table.put_item(Item=movie)
        print(f"  - {movie['title']} ({movie['theater_id']}) を挿入")
    
    print("\nテストデータ挿入完了!")


def verify_data():
    """データが正しく挿入されたか確認"""
    
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='ap-northeast-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    
    theater_table = dynamodb.Table('TheaterTable')
    movie_table = dynamodb.Table('MovieTable')
    
    # 映画館データ確認
    print("\n=== 映画館データ確認 ===")
    response = theater_table.scan()
    for item in response['Items']:
        print(f"ID: {item['theater_id']}, 名前: {item['name']}")
    
    # 映画データ確認
    print("\n=== 映画データ確認 ===")
    response = movie_table.scan()
    for item in response['Items']:
        print(f"ID: {item['movie_id'][:8]}..., "
              f"映画館: {item['theater_id']}, "
              f"タイトル: {item['title']}")
    
    # 映画館別映画検索テスト
    print("\n=== 映画館別映画検索テスト ===")
    response = movie_table.query(
        IndexName='theater_id-index',
        KeyConditionExpression='theater_id = :theater_id',
        ExpressionAttributeValues={
            ':theater_id': 'test_theater_1'
        }
    )
    print(f"test_theater_1の映画数: {response['Count']}")
    for item in response['Items']:
        print(f"  - {item['title']}")


if __name__ == "__main__":
    print("DynamoDBテストデータ挿入開始...")
    insert_test_data()
    verify_data()
    print("\nテスト完了!")