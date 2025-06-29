#!/usr/bin/env python3
"""
DynamoDB Local用テーブル作成スクリプト
要件定義書に基づいてTheaterTableとMovieTableを作成
"""

import boto3
from botocore.exceptions import ClientError


def create_dynamodb_tables():
    """DynamoDB LocalにTheaterTableとMovieTableを作成"""
    
    # DynamoDB Local接続設定
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='ap-northeast-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    
    # TheaterTable作成
    try:
        theater_table = dynamodb.create_table(
            TableName='TheaterTable',
            KeySchema=[
                {
                    'AttributeName': 'theater_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'theater_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("TheaterTable作成中...")
        theater_table.wait_until_exists()
        print("TheaterTable作成完了")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("TheaterTableは既に存在します")
        else:
            print(f"TheaterTable作成エラー: {e}")
    
    # MovieTable作成
    try:
        movie_table = dynamodb.create_table(
            TableName='MovieTable',
            KeySchema=[
                {
                    'AttributeName': 'movie_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'movie_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'theater_id',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'theater_id-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'theater_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("MovieTable作成中...")
        movie_table.wait_until_exists()
        print("MovieTable作成完了")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("MovieTableは既に存在します")
        else:
            print(f"MovieTable作成エラー: {e}")


def list_tables():
    """作成されたテーブル一覧を表示"""
    dynamodb = boto3.client(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='ap-northeast-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    
    try:
        response = dynamodb.list_tables()
        print("\n作成されたテーブル:")
        for table_name in response['TableNames']:
            print(f"  - {table_name}")
    except ClientError as e:
        print(f"テーブル一覧取得エラー: {e}")


if __name__ == "__main__":
    print("DynamoDB Localテーブル作成を開始...")
    create_dynamodb_tables()
    list_tables()
    print("\nテーブル作成完了!")