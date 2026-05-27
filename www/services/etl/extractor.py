import time
from typing import Any

import requests

from .interfaces import BaseExtractor


class OpenAlexExtractor(BaseExtractor):
    """
    Advanced Level Extractor for OpenAlex REST API.
    Handles automated pagination, rate limiting with backoff, and retries.
    """
    
    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, email: str = "academic.project@example.com"):
        """
        Initializes the extractor with a polite pool email address.
        """
        self.headers = {
            "User-Agent": f"BibliometrixETLPipeline/1.0 (mailto:{email})"
        }

    def extract(self, query: str, max_results: int = 100) -> list[dict[str, Any]]:
        """
        Extracts raw JSON payloads from OpenAlex API based on a search query.
        Accomplishes automatic pagination and error-resilient retries.
        """
        raw_results = []
        page = 1
        per_page = 25  # Standard page size for predictable API load
        
        while len(raw_results) < max_results:
            params = {
                "search": query,
                "page": page,
                "per_page": per_page
            }
            
            retries = 3
            backoff_time = 2
            
            while retries > 0:
                try:
                    response = requests.get(self.BASE_URL, headers=self.headers, params=params, timeout=15)
                    
                    # Handle Rate Limiting explicitly
                    if response.status_code == 429:
                        print(f"[Warning] Rate limit hit (429). Retrying in {backoff_time}s...")
                        time.sleep(backoff_time)
                        retries -= 1
                        backoff_time *= 2  # Exponential backoff
                        continue
                        
                    response.raise_for_status()
                    data = response.json()
                    break
                    
                except requests.RequestException as e:
                    print(f"[Error] API Request failed: {e}. Retries remaining: {retries - 1}")
                    retries -= 1
                    if retries == 0:
                        print("[Critical] Max retries reached. Returning extracted data so far.")
                        return raw_results
                    time.sleep(backoff_time)
            
            results = data.get("results", [])
            if not results:
                # No more records available from the API
                break
                
            raw_results.extend(results)
            print(f"[Extract] Fetched page {page}, accumulated {len(raw_results)} raw records.")
            
            # Boundary control to prevent over-fetching beyond max_results
            if len(results) < per_page:
                break
                
            page += 1
            time.sleep(0.1)  # Courteous delay between consecutive page calls
            
        # Trim excess records if pagination brought more than requested
        return raw_results[:max_results]
