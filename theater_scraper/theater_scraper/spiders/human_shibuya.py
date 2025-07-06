import scrapy
from datetime import datetime
from theater_scraper.items import TheaterItem, MovieItem


class HumanShibuyaSpider(scrapy.Spider):
    name = "human_shibuya"
    allowed_domains = ["ttcg.jp"]
    start_urls = ["https://ttcg.jp/human_shibuya/movie/"]
    
    theater_id = "human_shibuya"
    theater_name = "ヒューマントラストシネマ渋谷"

    def parse(self, response):
        """映画館情報と作品一覧をスクレイピング"""
        
        # 映画館情報を生成
        theater_item = TheaterItem()
        theater_item['theater_id'] = self.theater_id
        theater_item['name'] = self.theater_name
        theater_item['official_url'] = "https://ttcg.jp/human_shibuya/"
        theater_item['last_updated'] = datetime.now().isoformat()
        yield theater_item
        
        # 上映中の作品情報を取得
        movie_links = response.css('a[href*="/human_shibuya/movie/"]')
        self.logger.info(f"/human_shibuya/movie/を含むリンク数: {len(movie_links)}")
        
        # 重複を避けるためのセット
        processed_urls = set()
        
        # 各映画リンクを処理して詳細ページへ
        for link in movie_links:
            detail_url = link.css('::attr(href)').get()
            if detail_url:
                if not detail_url.startswith('http'):
                    detail_url = response.urljoin(detail_url)
                # HTTPSに正規化して重複を防ぐ
                detail_url = detail_url.replace('http://', 'https://')
                
                if detail_url.endswith('/movie/'):
                    continue
                
                if not detail_url.endswith('.html'):
                    continue
                
                if detail_url not in processed_urls:
                    processed_urls.add(detail_url)
                    # 詳細ページをリクエスト
                    yield scrapy.Request(detail_url, callback=self.parse_movie_detail)
    
    def parse_movie_detail(self, response):
        """映画詳細ページから情報を抽出"""
        try:
            title = response.css('h2::text').get()
            
            if not title:
                self.logger.warning(f"タイトルが取得できませんでした: {response.url}")
                return
            
            title = title.strip()
            
            synopsis_texts = []
            
            description_paragraphs = response.css('div p::text').getall()
            for text in description_paragraphs:
                if text and text.strip():
                    clean_text = text.strip()
                    if not any(keyword in clean_text for keyword in ['©', '(C)', 'All Rights Reserved', '製作委員会']):
                        synopsis_texts.append(clean_text)
            
            synopsis = ' '.join(synopsis_texts)
            if len(synopsis) > 200:
                synopsis = synopsis[:200] + "..."
            
            movie_info = {}
            for dl in response.css('dl'):
                dt_text = dl.css('dt::text').get()
                dd_text = dl.css('dd::text').get()
                
                if dt_text and dd_text:
                    movie_info[dt_text.strip()] = dd_text.strip()
            
            # 製作年を抽出
            release_year = None
            import re
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                release_year = int(year_match.group(1))
            
            official_website = None
            external_links = response.css('a[href^="http"]::attr(href)').getall()
            for link in external_links:
                if 'ttcg.jp' not in link and 'theatres.co.jp' not in link:
                    official_website = link
                    break
            
            # MovieItemを作成
            movie_item = MovieItem()
            movie_item['theater_id'] = self.theater_id
            movie_item['title'] = title
            movie_item['original_title'] = None  # この劇場サイトには原題情報がない場合が多い
            movie_item['release_year'] = release_year
            movie_item['official_website'] = official_website
            movie_item['synopsis'] = synopsis
            movie_item['detail_url'] = response.url
            movie_item['created_at'] = datetime.now().isoformat()
            movie_item['updated_at'] = datetime.now().isoformat()
            
            self.logger.info(f"映画詳細取得: {title} ({release_year}) - {official_website}")
            
            yield movie_item
            
        except Exception as e:
            self.logger.error(f"詳細ページ解析エラー ({response.url}): {e}")
