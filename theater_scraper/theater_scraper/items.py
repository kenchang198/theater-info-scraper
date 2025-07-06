# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TheaterItem(scrapy.Item):
    """映画館情報アイテム"""
    theater_id = scrapy.Field()
    name = scrapy.Field()
    official_url = scrapy.Field()
    last_updated = scrapy.Field()


class MovieItem(scrapy.Item):
    """作品情報アイテム"""
    # 基本情報
    theater_id = scrapy.Field()
    title = scrapy.Field()
    original_title = scrapy.Field()  # 原題（英語タイトル）
    release_year = scrapy.Field()  # 製作年
    official_website = scrapy.Field()  # 公式サイトURL
    synopsis = scrapy.Field()
    detail_url = scrapy.Field()  # プライマリキーとして使用
    
    # TMDb API関連フィールド
    tmdb_id = scrapy.Field()
    tmdb_poster_path = scrapy.Field()
    
    # タイムスタンプ
    created_at = scrapy.Field()
    updated_at = scrapy.Field()
