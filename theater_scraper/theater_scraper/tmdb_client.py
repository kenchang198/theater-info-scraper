"""
TMDb API client for fetching movie poster information
"""

import os
import time
import logging
import json
import requests
from typing import Optional, Dict, Any
from pathlib import Path

# TMDb API専用ロガーの設定
logger = logging.getLogger('tmdb_api')
logger.setLevel(logging.DEBUG)

# ファイルハンドラーの設定（TMDb APIログを別ファイルに出力）
if not logger.handlers:
    # プロジェクトルートディレクトリに固定してログを出力
    log_file_path = Path(__file__).parent.parent.parent / 'tmdb_api.log'
    fh = logging.FileHandler(log_file_path, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # コンソールハンドラーも追加（INFO以上）
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class TMDbClient:
    """TMDb API client with Bearer authentication"""
    
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/"
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize TMDb client with Bearer token"""
        self.access_token = access_token or os.getenv('TMDB_ACCESS_TOKEN')
        if not self.access_token:
            raise ValueError("TMDB_ACCESS_TOKEN environment variable is not set")
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json;charset=utf-8"
        }
        self.last_request_time = 0
        self.request_delay = 0.1  # 100ms delay between requests
    
    def _rate_limit(self):
        """Implement rate limiting (10 requests per second)"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.request_delay:
            time.sleep(self.request_delay - time_since_last_request)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make API request with error handling"""
        self._rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        
        # リクエスト情報をログ出力
        logger.debug(f"=== TMDb API Request ===")
        logger.debug(f"URL: {url}")
        logger.debug(f"Params: {json.dumps(params, ensure_ascii=False, indent=2)}")
        logger.debug(f"Headers: {json.dumps({k: v if k != 'Authorization' else 'Bearer ***' for k, v in self.headers.items()}, indent=2)}")
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            # レスポンス情報をログ出力
            logger.debug(f"=== TMDb API Response ===")
            logger.debug(f"Status Code: {response.status_code}")
            logger.debug(f"Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            response_data = response.json()
            
            # レスポンスボディをログ出力（大きい場合は一部のみ）
            response_str = json.dumps(response_data, ensure_ascii=False, indent=2)
            if len(response_str) > 2000:
                logger.debug(f"Response Body (truncated): {response_str[:2000]}...")
            else:
                logger.debug(f"Response Body: {response_str}")
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"=== TMDb API Error ===")
            logger.error(f"Error Type: {type(e).__name__}")
            logger.error(f"Error Message: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response Status: {e.response.status_code}")
                logger.error(f"Response Body: {e.response.text}")
            return None
    
    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Search for a movie by title
        
        Args:
            title: Movie title to search for
            year: Optional release year to narrow search
            
        Returns:
            First matching movie data or None if not found
        """
        logger.info(f"=== Searching movie: '{title}' (year: {year or 'any'}) ===")
        
        params = {
            "query": title,
            "language": "ja-JP",
            "page": 1
        }
        
        if year:
            params["year"] = year
        
        result = self._make_request("/search/movie", params)
        
        if result:
            total_results = result.get("total_results", 0)
            results = result.get("results", [])
            
            logger.info(f"Search results: {total_results} movies found")
            
            if results:
                # 最初の5件の結果をログ出力
                logger.debug("Top search results:")
                for i, movie in enumerate(results[:5]):
                    logger.debug(
                        f"  {i+1}. '{movie.get('title')}' "
                        f"(original: '{movie.get('original_title')}', "
                        f"year: {movie.get('release_date', '').split('-')[0] if movie.get('release_date') else 'N/A'}, "
                        f"ID: {movie.get('id')}, "
                        f"poster: {movie.get('poster_path', 'None')})"
                    )
                
                # Return the first match
                movie = results[0]
                logger.info(
                    f"Selected movie: '{movie.get('title')}' "
                    f"(ID: {movie.get('id')}, poster: {movie.get('poster_path', 'None')})"
                )
                return movie
            else:
                logger.warning(f"No results in response for '{title}'")
        else:
            logger.warning(f"No response from TMDb API for '{title}'")
        
        return None
    
    def get_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed movie information
        
        Args:
            movie_id: TMDb movie ID
            
        Returns:
            Movie details or None if not found
        """
        return self._make_request(f"/movie/{movie_id}", {"language": "ja-JP"})
    
    @staticmethod
    def get_poster_url(poster_path: str, size: str = "w300") -> str:
        """
        Get full poster URL from poster path
        
        Args:
            poster_path: Poster path from TMDb API
            size: Image size (w92, w154, w185, w342, w500, w780, original)
            
        Returns:
            Full poster URL
        """
        if not poster_path:
            return ""
        return f"{TMDbClient.IMAGE_BASE_URL}{size}{poster_path}"