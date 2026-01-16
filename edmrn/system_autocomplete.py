import requests
import threading
import time
from typing import List, Optional, Callable
from edmrn.logger import get_logger

logger = get_logger('SystemAutocomplete')


class SystemAutocompleter:
    
    def __init__(self):
        self.spansh_api_url = "https://spansh.co.uk/api/systems/search"
        self.edsm_api_url = "https://www.edsm.net/api-v1/systems"
        self.cache = {}
        self.cache_ttl = 3600
    
    def get_suggestions(self, query: str, max_results: int = 10) -> List[str]:
        if not query or len(query.strip()) < 3:
            return []
        
        query = query.strip()
        
        if query in self.cache:
            cached_time, cached_results = self.cache[query]
            if time.time() - cached_time < self.cache_ttl:
                return cached_results[:max_results]
        
        results = self._fetch_from_spansh(query, max_results)
        
        if results:
            self.cache[query] = (time.time(), results)
            return results[:max_results]
        
        logger.debug(f"Spansh returned no results, trying EDSM for: {query}")
        results = self._fetch_from_edsm(query, max_results)
        
        if results:
            self.cache[query] = (time.time(), results)
            return results[:max_results]
        
        return []
    
    def _fetch_from_edsm(self, query: str, max_results: int) -> List[str]:
        try:
            params = {
                "systemName": query,
                "showId": 0,
                "showCoordinates": 0,
                "showPermit": 0,
                "showInformation": 0,
                "showPrimaryStar": 0
            }
            
            response = requests.get(
                self.edsm_api_url,
                params=params,
                headers={'User-Agent': "EDMRN_AutoComplete/1.0"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    all_results = [system.get('name') for system in data if isinstance(system, dict) and system.get('name')]
                    
                    if all_results:
                        query_lower = query.lower()
                        exact = [r for r in all_results if r.lower() == query_lower]
                        starts_with = [r for r in all_results if r.lower().startswith(query_lower) and r not in exact]
                        contains = [r for r in all_results if query_lower in r.lower() and r not in exact and r not in starts_with]
                        
                        return exact + starts_with + contains
            
            return []
            
        except Exception as e:
            logger.debug(f"EDSM API error for '{query}': {str(e)}")
            return []
    
    def _fetch_from_spansh(self, query: str, max_results: int) -> List[str]:
        try:
            payload = {
                "filters": {
                    "name": {
                        "value": query
                    }
                },
                "size": 50,
                "sort": [{"name": {"order": "asc"}}]
            }
            
            response = requests.post(
                self.spansh_api_url,
                json=payload,
                headers={
                    'User-Agent': "EDMRN_AutoComplete/1.0",
                    'Content-Type': 'application/json'
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and isinstance(data['results'], list):
                    all_results = [system.get('name') for system in data['results'] if system.get('name')]
                    
                    if all_results:
                        query_lower = query.lower()
                        exact = [r for r in all_results if r.lower() == query_lower]
                        starts_with = [r for r in all_results if r.lower().startswith(query_lower) and r not in exact]
                        contains = [r for r in all_results if query_lower in r.lower() and r not in exact and r not in starts_with]
                        
                        return exact + starts_with + contains
            
            return []
            
        except Exception as e:
            logger.debug(f"Spansh API error for '{query}': {str(e)}")
            return []
    
    def get_suggestions_async(self, query: str, callback: Callable, max_results: int = 10):

        def fetch():
            results = self.get_suggestions(query, max_results)
            callback(results)
        
        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()
