# Theater Info Scraper

東京都内単館系映画館情報スクレイピングシステム

## プロジェクト概要

このプロジェクトは、東京都内の単館系映画館の現在上映中作品情報をスクレイピングし、DynamoDBに保存するシステムです。

## 技術構成

- **スクレイピング**: Scrapy
- **データベース**: AWS DynamoDB（ローカル開発環境ではDynamoDB Local）
- **開発環境**: Python 3.13, Docker Compose

## プロジェクト構造

```
theater-info-scraper/
├── docker-compose.yml          # DynamoDB Local環境
├── requirements.txt            # Python依存関係
├── create_tables.py           # DynamoDBテーブル作成スクリプト
├── test_data_insertion.py     # テストデータ挿入スクリプト
└── theater_scraper/           # Scrapyプロジェクト
    ├── scrapy.cfg
    └── theater_scraper/
        ├── items.py           # データ構造定義
        ├── pipelines.py       # DynamoDB保存パイプライン
        ├── settings.py        # Scrapy設定
        └── spiders/
            └── cinema_qualite.py  # サンプルスパイダー
```

## セットアップ

### 1. 仮想環境の作成とアクティベート

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\\Scripts\\activate  # Windows
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. DynamoDB Localの起動

```bash
docker-compose up -d
```

### 4. DynamoDBテーブルの作成

```bash
python create_tables.py
```

## 使用方法

### テストデータの挿入

```bash
python test_data_insertion.py
```

### スパイダーの実行

```bash
cd theater_scraper
scrapy crawl cinema_qualite
```

## データ構造

### TheaterTable
- `theater_id` (PK): 映画館ID
- `name`: 映画館名
- `official_url`: 公式サイトURL
- `last_updated`: 最終更新日時

### MovieTable
- `movie_id` (PK): 作品ID
- `theater_id` (GSI): 映画館ID
- `title`: 作品タイトル
- `image_url`: サムネイル画像URL
- `synopsis`: あらすじ（抜粋）
- `detail_url`: 詳細ページURL
- `created_at`: 作成日時
- `updated_at`: 更新日時

## 開発状況

### 完了済み
- [x] Scrapyプロジェクトの基本構造作成
- [x] DynamoDB Local環境構築（Docker Compose）
- [x] DynamoDBテーブル作成（TheaterTable, MovieTable）
- [x] 基本的なスクレイピング機能実装
- [x] DynamoDBデータ投入機能実装
- [x] データ検証パイプライン実装

### 今後の予定
- [ ] 実際の映画館サイトに対応したスパイダー実装
- [ ] エラーハンドリングとリトライ機能強化
- [ ] スケジュール実行機能（CloudWatch Events対応）
- [ ] AWS Lambda対応
- [ ] FastAPI実装（フェーズ2）
- [ ] Next.jsフロントエンド実装（フェーズ3）

## 注意事項

- スクレイピング対象サイトの利用規約を遵守してください
- 適切な間隔でのクローリングを心がけてください（現在1秒間隔設定）
- 本番環境では実際のAWS DynamoDBを使用してください

## ライセンス

このプロジェクトは開発用サンプルです。# theater-info-scraper
