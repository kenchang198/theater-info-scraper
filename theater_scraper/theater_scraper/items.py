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
    theater_id = scrapy.Field()
    title = scrapy.Field()
    image_url = scrapy.Field()
    synopsis = scrapy.Field()
    detail_url = scrapy.Field()
    created_at = scrapy.Field()
    updated_at = scrapy.Field()
