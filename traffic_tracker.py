"""
GitHub Traffic Tracker
Scrapes GitHub repository traffic data and stores unlimited history
"""

import json
import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TrafficTracker')


class Config:
    """Configuration for traffic tracker."""
    
    REPO_OWNER = os.getenv('GITHUB_REPOSITORY_OWNER', 'NinurtaKalhu')
    REPO_NAME = os.getenv('GITHUB_REPOSITORY_NAME', 'Elite-Dangerous-Multi-Route-Optimizer')
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    DATA_FILE = 'traffic_history.json'
    DAYS_TO_KEEP = 365  # 1 yıl sakla
    
    @property
    def repo(self) -> str:
        return f"{self.REPO_OWNER}/{self.REPO_NAME}"
    
    @property
    def api_base(self) -> str:
        return f"https://api.github.com/repos/{self.repo}"
    
    @property
    def headers(self) -> Dict[str, str]:
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if self.GITHUB_TOKEN:
            headers['Authorization'] = f'token {self.GITHUB_TOKEN}'
        return headers


class TrafficTracker:
    """Tracks GitHub repository traffic data."""
    
    def __init__(self, config: Config):
        self.config = config
        self.data_file = Path(config.DATA_FILE)
        self.history: Dict[str, Any] = self.load_history()
    
    def load_history(self) -> Dict[str, Any]:
        """Load traffic history from file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"History loaded: {len(data.get('daily', []))} days")
                return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load history: {e}")
        
        return {
            "repo_stats": {},
            "daily": [],
            "releases": [],
            "last_updated": ""
        }
    
    def save_history(self) -> None:
        """Save traffic history to file."""
        self.history['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            logger.info("History saved")
        except IOError as e:
            logger.error(f"Failed to save history: {e}")
    
    def fetch_repo_stats(self) -> Optional[Dict]:
        """Fetch basic repository statistics."""
        try:
            response = requests.get(
                self.config.api_base,
                headers=self.config.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            stats = {
                'stars': data.get('stargazers_count', 0),
                'forks': data.get('forks_count', 0),
                'watchers': data.get('subscribers_count', 0),
                'open_issues': data.get('open_issues_count', 0),
                'size_kb': data.get('size', 0),
                'language': data.get('language', 'N/A'),
                'created_at': data.get('created_at', ''),
                'updated_at': data.get('updated_at', ''),
                'pushed_at': data.get('pushed_at', '')
            }
            
            logger.info(f"Repo stats: {stats['stars']} stars, {stats['forks']} forks")
            return stats
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch repo stats: {e}")
            return None
    
    def fetch_views(self) -> Optional[Dict]:
        """Fetch traffic views (requires auth)."""
        if not self.config.GITHUB_TOKEN:
            logger.warning("No GitHub token - views data unavailable")
            return None
        
        try:
            response = requests.get(
                f"{self.config.api_base}/traffic/views",
                headers=self.config.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            views = {
                'count': data.get('count', 0),
                'uniques': data.get('uniques', 0),
                'daily': data.get('views', [])
            }
            
            logger.info(f"Views: {views['count']} total, {views['uniques']} unique")
            return views
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch views: {e}")
            return None
    
    def fetch_clones(self) -> Optional[Dict]:
        """Fetch traffic clones (requires auth)."""
        if not self.config.GITHUB_TOKEN:
            logger.warning("No GitHub token - clones data unavailable")
            return None
        
        try:
            response = requests.get(
                f"{self.config.api_base}/traffic/clones",
                headers=self.config.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            clones = {
                'count': data.get('count', 0),
                'uniques': data.get('uniques', 0),
                'daily': data.get('clones', [])
            }
            
            logger.info(f"Clones: {clones['count']} total, {clones['uniques']} unique")
            return clones
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch clones: {e}")
            return None
    
    def fetch_top_content(self) -> Optional[Dict]:
        """Fetch top referring sites (requires auth)."""
        if not self.config.GITHUB_TOKEN:
            return None
        
        try:
            response = requests.get(
                f"{self.config.api_base}/traffic/popular/referrers",
                headers=self.config.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch referrers: {e}")
            return None
    
    def fetch_releases(self) -> list:
        """Fetch all releases with download counts."""
        try:
            response = requests.get(
                f"{self.config.api_base}/releases",
                headers=self.config.headers,
                timeout=30
            )
            response.raise_for_status()
            releases = response.json()
            
            result = []
            for release in releases:
                total_downloads = sum(a.get('download_count', 0) for a in release.get('assets', []))
                result.append({
                    'tag': release.get('tag_name', ''),
                    'name': release.get('name', ''),
                    'published_at': release.get('published_at', ''),
                    'downloads': total_downloads
                })
            
            logger.info(f"Releases: {len(result)} found")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch releases: {e}")
            return []
    
    def collect_daily_data(self) -> None:
        """Collect all traffic data for today."""
        today = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"Collecting data for {today}")
        
        # Fetch all data
        repo_stats = self.fetch_repo_stats()
        views = self.fetch_views()
        clones = self.fetch_clones()
        releases = self.fetch_releases()
        
        # Create daily entry
        daily_entry = {
            'date': today,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'repo_stats': repo_stats or {},
            'views': views or {'count': 0, 'uniques': 0},
            'clones': clones or {'count': 0, 'uniques': 0},
            'total_downloads': sum(r.get('downloads', 0) for r in releases)
        }
        
        # Check if today already exists
        existing_idx = None
        for i, entry in enumerate(self.history.get('daily', [])):
            if entry.get('date') == today:
                existing_idx = i
                break
        
        if existing_idx is not None:
            self.history['daily'][existing_idx] = daily_entry
            logger.info(f"Updated existing entry for {today}")
        else:
            self.history.setdefault('daily', []).append(daily_entry)
            logger.info(f"Added new entry for {today}")
        
        # Update releases
        self.history['releases'] = releases
        
        # Update repo stats
        if repo_stats:
            self.history['repo_stats'] = repo_stats
    
    def cleanup_old_data(self) -> None:
        """Remove data older than DAYS_TO_KEEP."""
        cutoff_date = (datetime.now() - timedelta(days=self.config.DAYS_TO_KEEP)).strftime('%Y-%m-%d')
        
        original_count = len(self.history.get('daily', []))
        self.history['daily'] = [
            entry for entry in self.history.get('daily', [])
            if entry.get('date', '') >= cutoff_date
        ]
        removed_count = original_count - len(self.history['daily'])
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} entries older than {cutoff_date}")
    
    def generate_summary(self) -> str:
        """Generate a summary of all collected data."""
        daily = self.history.get('daily', [])
        releases = self.history.get('releases', [])
        stats = self.history.get('repo_stats', {})
        
        if not daily:
            return "No data collected yet."
        
        # Calculate totals
        total_views = sum(d.get('views', {}).get('count', 0) for d in daily)
        total_clones = sum(d.get('clones', {}).get('count', 0) for d in daily)
        total_downloads = sum(d.get('total_downloads', 0) for d in daily)
        
        # Get latest
        latest = daily[-1] if daily else {}
        
        summary = f"""
EDMRN Traffic Summary
========================================

Current Stats:
  Stars: {stats.get('stars', 'N/A')}
  Forks: {stats.get('forks', 'N/A')}
  Watchers: {stats.get('watchers', 'N/A')}

Total Downloads (All Releases): {total_downloads}

Daily Data ({len(daily)} days tracked):
  Total Views: {total_views}
  Total Clones: {total_clones}

Latest ({latest.get('date', 'N/A')}):
  Views: {latest.get('views', {}).get('count', 0)}
  Clones: {latest.get('clones', {}).get('count', 0)}

Releases: {len(releases)}
"""
        return summary


def main():
    """Main entry point."""
    logger.info("GitHub Traffic Tracker started")
    
    config = Config()
    tracker = TrafficTracker(config)
    
    # Collect today's data
    tracker.collect_daily_data()
    
    # Cleanup old data
    tracker.cleanup_old_data()
    
    # Save
    tracker.save_history()
    
    # Print summary
    print(tracker.generate_summary())
    
    logger.info("Traffic tracking completed")


if __name__ == "__main__":
    main()
