import scrapy
from datetime import datetime
from theater_scraper.items import TheaterItem, MovieItem


class CinemaQualiteSpider(scrapy.Spider):
    name = "cinema_qualite"
    allowed_domains = ["qualite.musashino-k.jp"]
    start_urls = ["https://qualite.musashino-k.jp/"]
    
    theater_id = "cinema_qualite"
    theater_name = "新宿シネマカリテ"

    def parse(self, response):
        """映画館情報と作品一覧をスクレイピング"""
        
        # 映画館情報を生成
        theater_item = TheaterItem()
        theater_item['theater_id'] = self.theater_id
        theater_item['name'] = self.theater_name
        theater_item['official_url'] = "https://qualite.musashino-k.jp/"
        theater_item['last_updated'] = datetime.now().isoformat()
        yield theater_item
        
        # 上映中の作品情報を取得
        # 全ての/movies/リンクから映画情報を取得
        movie_links = response.css('a[href*="/movies/"]')
        self.logger.info(f"/movies/を含むリンク数: {len(movie_links)}")
        
        # 重複を避けるためのセット
        processed_urls = set()
        
        # 各映画リンクを処理
        for link in movie_links:
            movie_item = self.parse_movie_link(link, response)
            if movie_item:
                detail_url = movie_item.get('detail_url', '')
                if detail_url not in processed_urls:
                    processed_urls.add(detail_url)
                    yield movie_item
    
    def parse_movie_link(self, link, response):
        """スライダーのリンクから映画情報を解析"""
        try:
            # 詳細ページURLを取得
            detail_url = link.css('::attr(href)').get()
            if detail_url:
                if not detail_url.startswith('http'):
                    detail_url = response.urljoin(detail_url)
                # HTTPSに正規化して重複を防ぐ
                detail_url = detail_url.replace('http://', 'https://')
                
                # 映画一覧ページ（/movies/のみ）を除外
                if detail_url.endswith('/movies/'):
                    return None
            
            # タイトルを取得 - HTML構造に基づく正確なセレクタ
            title = link.css('div.description div.text h4.title b::text').get()
            
            # フォールバック: <b>タグがない場合
            if not title:
                title = link.css('div.description div.text h4.title::text').get()
            
            # さらなるフォールバック: 最初のリンクのような場合
            if not title:
                title = link.css('b::text').get()
            
            if not title:
                self.logger.warning(f"タイトルが取得できませんでした: {detail_url}")
                return None
            
            title = title.strip()
            
            # 上映期間情報を取得
            showing_period = link.xpath('.//text()[contains(., "まで")]').get()
            if showing_period:
                showing_period = showing_period.strip()
            
            movie_item = MovieItem()
            movie_item['theater_id'] = self.theater_id
            movie_item['title'] = title
            movie_item['image_url'] = ""
            movie_item['synopsis'] = showing_period or ""
            movie_item['detail_url'] = detail_url or response.url
            movie_item['created_at'] = datetime.now().isoformat()
            movie_item['updated_at'] = datetime.now().isoformat()
            
            return movie_item
            
        except Exception as e:
            self.logger.error(f"スライダーリンク解析エラー: {e}")
            return None
    
    def parse_movie_article(self, article, response):
        """記事から映画情報を解析"""
        try:
            # 詳細ページURLを取得
            detail_url = article.css('a::attr(href)').get()
            if detail_url:
                if not detail_url.startswith('http'):
                    detail_url = response.urljoin(detail_url)
                # HTTPSに正規化して重複を防ぐ
                detail_url = detail_url.replace('http://', 'https://')
                
                # 映画一覧ページ（/movies/のみ）を除外
                if detail_url.endswith('/movies/'):
                    return None
                
                # ニュース記事を除外（/movies/を含むURLのみ処理）
                if '/movies/' not in detail_url:
                    return None
            
            # タイトルを取得 - 複数の候補から
            title = (article.css('h4::text').get() or 
                    article.css('h3::text').get() or 
                    article.css('h2::text').get() or
                    article.css('a::text').get() or
                    article.css('.title::text').get())
            
            if not title:
                self.logger.warning(f"タイトルが取得できませんでした: {detail_url}")
                return None
            
            title = title.strip()
            
            # 上映期間情報を取得
            showing_period = article.xpath('.//text()[contains(., "まで")]').get()
            if showing_period:
                showing_period = showing_period.strip()
            
            movie_item = MovieItem()
            movie_item['theater_id'] = self.theater_id
            movie_item['title'] = title
            movie_item['image_url'] = ""
            movie_item['synopsis'] = showing_period or ""
            movie_item['detail_url'] = detail_url or response.url
            movie_item['created_at'] = datetime.now().isoformat()
            movie_item['updated_at'] = datetime.now().isoformat()
            
            return movie_item
            
        except Exception as e:
            self.logger.error(f"記事解析エラー: {e}")
            return None

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
            
            # あらすじを取得（短縮版）- .is-metaクラス要素を除外
            synopsis = card.css('.synopsis:not(.is-meta)::text, .description:not(.is-meta)::text, p:not(.is-meta)::text').get()
            if synopsis:
                synopsis = synopsis.strip()[:200] + "..." if len(synopsis) > 200 else synopsis.strip()
            
            movie_item = MovieItem()
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
