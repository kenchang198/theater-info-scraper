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
        
        # 各映画リンクを処理して詳細ページへ
        for link in movie_links:
            detail_url = link.css('::attr(href)').get()
            if detail_url:
                if not detail_url.startswith('http'):
                    detail_url = response.urljoin(detail_url)
                # HTTPSに正規化して重複を防ぐ
                detail_url = detail_url.replace('http://', 'https://')
                
                # 映画一覧ページ（/movies/のみ）を除外
                if detail_url.endswith('/movies/'):
                    continue
                
                if detail_url not in processed_urls:
                    processed_urls.add(detail_url)
                    # 詳細ページをリクエスト
                    yield scrapy.Request(detail_url, callback=self.parse_movie_detail)
    
    def parse_movie_detail(self, response):
        """映画詳細ページから情報を抽出"""
        try:
            # タイトル
            title = response.css('h1 b::text').get()
            if not title:
                title = response.css('h1::text').get()
            
            if not title:
                self.logger.warning(f"タイトルが取得できませんでした: {response.url}")
                return
            
            title = title.strip()
            
            # 映画情報をdlリストから取得
            movie_info = {}
            for dl in response.css('dl'):
                dt_text = dl.css('dt b::text').get()
                if not dt_text:
                    dt_text = dl.css('dt::text').get()
                
                dd_text = dl.css('dd p::text').get()
                if not dd_text:
                    dd_text = dl.css('dd::text').get()
                
                if dt_text and dd_text:
                    movie_info[dt_text.strip()] = dd_text.strip()
            
            # 公式サイトURL
            official_website = None
            if '公式HP' in movie_info:
                # URLを含むaタグから取得
                official_link = response.xpath('//dt[contains(text(), "公式HP")]/following-sibling::dd//a/@href').get()
                if official_link:
                    official_website = official_link
            
            # 製作年を抽出
            release_year = None
            if '制作年／制作国' in movie_info:
                import re
                year_match = re.search(r'(\d{4})年', movie_info['制作年／制作国'])
                if year_match:
                    release_year = int(year_match.group(1))
            
            # あらすじ
            synopsis_texts = []
            # メインのテキストコンテナから取得
            for text_block in response.css('.module-text .text p'):
                text = text_block.css('::text').get()
                if text and text.strip():
                    # 上映期間やスタッフ情報を除外
                    if not any(keyword in text for keyword in ['上映期間:', '上映時間:', '©', '(C)']):
                        synopsis_texts.append(text.strip())
            
            synopsis = ' '.join(synopsis_texts)
            if len(synopsis) > 200:
                synopsis = synopsis[:200] + "..."
            
            # 上映期間
            showing_period = movie_info.get('上映期間', '')
            
            # MovieItemを作成
            movie_item = MovieItem()
            movie_item['theater_id'] = self.theater_id
            movie_item['title'] = title
            movie_item['original_title'] = None  # この劇場サイトには原題情報がない場合が多い
            movie_item['release_year'] = release_year
            movie_item['official_website'] = official_website
            movie_item['synopsis'] = synopsis or showing_period
            movie_item['detail_url'] = response.url
            movie_item['created_at'] = datetime.now().isoformat()
            movie_item['updated_at'] = datetime.now().isoformat()
            
            self.logger.info(f"映画詳細取得: {title} ({release_year}) - {official_website}")
            
            yield movie_item
            
        except Exception as e:
            self.logger.error(f"詳細ページ解析エラー ({response.url}): {e}")
    
