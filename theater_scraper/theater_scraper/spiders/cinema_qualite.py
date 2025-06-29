import scrapy
from datetime import datetime
import hashlib
from theater_scraper.items import TheaterItem, MovieItem


class CinemaQualiteSpider(scrapy.Spider):
    name = "cinema_qualite"
    allowed_domains = ["www.cinema-qualite.com"]
    start_urls = ["https://www.cinema-qualite.com/lineup/"]
    
    theater_id = "cinema_qualite"
    theater_name = "シネマカリテ"

    def parse(self, response):
        """映画館情報と作品一覧をスクレイピング"""
        
        # 映画館情報を生成
        theater_item = TheaterItem()
        theater_item['theater_id'] = self.theater_id
        theater_item['name'] = self.theater_name
        theater_item['official_url'] = "https://www.cinema-qualite.com/"
        theater_item['last_updated'] = datetime.now().isoformat()
        yield theater_item
        
        # 作品カードを取得（サンプル実装）
        # 実際のサイト構造に合わせて調整が必要
        movie_cards = response.css('.movie-card, .film-item, .lineup-item')
        
        if not movie_cards:
            # フォールバック: 他の可能性のあるセレクタを試す
            movie_cards = response.css('article, .entry, .post')
        
        for card in movie_cards:
            movie_item = self.parse_movie_card(card, response)
            if movie_item:
                yield movie_item
    
    def parse_movie_card(self, card, response):
        """映画カード情報を解析"""
        try:
            # タイトルを取得
            title = card.css('h1::text, h2::text, h3::text, .title::text, .movie-title::text').get()
            if not title:
                title = card.css('a::text').get()
            
            if not title:
                return None
            
            title = title.strip()
            
            # 画像URLを取得
            image_url = card.css('img::attr(src)').get()
            if image_url and not image_url.startswith('http'):
                image_url = response.urljoin(image_url)
            
            # 詳細ページURLを取得
            detail_url = card.css('a::attr(href)').get()
            if detail_url and not detail_url.startswith('http'):
                detail_url = response.urljoin(detail_url)
            
            # あらすじを取得（短縮版）
            synopsis = card.css('.synopsis::text, .description::text, p::text').get()
            if synopsis:
                synopsis = synopsis.strip()[:200] + "..." if len(synopsis) > 200 else synopsis.strip()
            
            # ユニークなmovie_idを生成
            movie_id = hashlib.md5(f"{self.theater_id}_{title}".encode()).hexdigest()
            
            movie_item = MovieItem()
            movie_item['movie_id'] = movie_id
            movie_item['theater_id'] = self.theater_id
            movie_item['title'] = title
            movie_item['image_url'] = image_url
            movie_item['synopsis'] = synopsis or ""
            movie_item['detail_url'] = detail_url or response.url
            movie_item['created_at'] = datetime.now().isoformat()
            movie_item['updated_at'] = datetime.now().isoformat()
            
            return movie_item
            
        except Exception as e:
            self.logger.error(f"映画カード解析エラー: {e}")
            return None
