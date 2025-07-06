# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

東京都内の単館系映画館の現在上映中作品情報をスクレイピングし、DynamoDBに保存するPythonベースのシステムです。WebスクレイピングにはScrapy、ローカル開発環境にはDocker Composeを使用しています。

## ドキュメント構成

### プロジェクト要件
- **全体システム要件**: `../theater_info_prj_docs/requirements.md`
  - MVP機能、システムアーキテクチャ、開発フェーズを含む完全なプロジェクト仕様
  - Next.jsフロントエンド、FastAPIバックエンド、AWSサーバーレスインフラを定義
  - データ構造定義と開発ロードマップを含む
- **タスク分解**: `.tmp/task.md`に記載（必要時作成）
- **API仕様**: `.tmp/api-spec.md`に記載（必要時作成）
- **フロントエンド要件**: `.tmp/frontend-requirements.md`に記載（必要時作成）

**現在の状況**: このリポジトリはフェーズ1（基盤構築）- Scrapyベースのスクレイピングシステムです。今後のフェーズでFastAPIバックエンドとNext.jsフロントエンドコンポーネントを追加予定です。

**リポジトリ構成**: 現在のスクレイピングシステムと、今後のフェーズで作成するFastAPIバックエンドおよびNext.jsフロントエンドコンポーネントは、それぞれ異なるディレクトリ（別リポジトリ）に分けて構築します。

## よく使用するコマンド

### 環境セットアップ
```bash
# 仮想環境をアクティベート
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt

# DynamoDB Localを起動
docker-compose up -d

# データベーステーブルを作成
python create_tables.py
```

### 開発コマンド
```bash
# スパイダーを実行
cd theater_scraper
scrapy crawl cinema_qualite

# テストデータを挿入
python test_data_insertion.py

# DynamoDB Localを停止
docker-compose down
```

### プロジェクト構造
```
theater_scraper/             # Scrapyプロジェクトディレクトリ
├── theater_scraper/
│   ├── items.py             # データ構造定義（TheaterItem, MovieItem）
│   ├── pipelines.py         # DynamoDB保存パイプライン
│   ├── settings.py          # Scrapy設定
│   └── spiders/             # スパイダー実装
create_tables.py            # DynamoDBテーブル作成スクリプト
test_data_insertion.py      # テストデータ挿入スクリプト
docker-compose.yml          # DynamoDB Local設定
```

## アーキテクチャ説明

### データフロー
1. スパイダーが映画館サイトをスクレイピングし、TheaterItem/MovieItemオブジェクトをyield
2. ValidationPipelineが必須フィールドを検証
3. DynamoDBPipelineがローカルDynamoDBテーブルにデータを保存

### DynamoDBスキーマ
- **TheaterTable**: プライマリキー `theater_id`（String）
- **MovieTable**: プライマリキー `movie_id`（String）、`theater_id`でGSI

### 主要コンポーネント
- **Items**（`items.py`）: 映画館と作品のデータ構造を定義
- **Pipelines**（`pipelines.py`）: 検証とDynamoDB保存を処理
- **Settings**（`settings.py`）: ダウンロード遅延（1秒）、robots.txt遵守、パイプラインを設定
- **Spiders**: サイト固有のスクレイピングロジックを実装

### 開発パターン
- 全てのスパイダーはTheaterItemとMovieItemの両方をyieldする
- `hashlib.md5()`を使用してtheater_idとtitleからユニークなmovie_idを生成
- スパイダー実装には適切なエラーハンドリングとログ出力を含める
- 既存のパイプライン順序に従う: ValidationPipeline（100）→ DynamoDBPipeline（300）

### ローカル開発
- DynamoDB LocalはDocker Composeでポート8000で実行
- ローカル開発用にダミーAWS認証情報を使用
- データベースファイルは`./docker/dynamodb/`ディレクトリに永続化

### スパイダー実装ガイドライン
- `scrapy.Spider`を継承
- `theater_id`と`theater_name`クラス属性を定義
- フォールバック付きの堅牢なCSSセレクタを実装
- `response.urljoin()`を使用して相対URLを処理
- あらすじを200文字で切り詰め、"..."サフィックスを追加
- 日時フィールドにはISO形式のタイムスタンプを使用

### 画像取得アーキテクチャ
- **実装方式**: スクレイピング時にTMDb APIを同時実行
- **認証方式**: Bearer認証トークンを使用（より安全）
- **画像サイズ**: w300（ポスター表示用）
- **エラー処理**: TMDb APIエラー時は画像情報なしで処理継続
- **レート制限対策**: 0.1秒/リクエストの遅延を設定
- **パイプライン順序**: ValidationPipeline（100）→ TMDbPipeline（200）→ DynamoDBPipeline（300）

### TMDb API統合
- **環境変数**:
  - `TMDB_API_KEY`: APIキー（互換性のため保持）
  - `TMDB_ACCESS_TOKEN`: Bearer認証用アクセストークン
- **取得データ**:
  - `tmdb_id`: TMDb映画ID
  - `tmdb_poster_path`: ポスター画像パス
- **画像URL構成**: `https://image.tmdb.org/t/p/w300/[poster_path]`
- **APIリファレンス**: https://developer.themoviedb.org/reference/intro/getting-started

### TMDb APIデバッグ
- **専用ログファイル**: `tmdb_api.log`に詳細なAPIリクエスト/レスポンスを記録
- **テストスクリプト**: `python test_tmdb_api.py`でAPI動作を単体テスト
- **ログ分離**: Scrapy本体のログとTMDb APIログを分離して問題を切り分け