"""Polymarket API client for loading market data."""

import requests
from typing import List, Dict, Optional


class PolymarketAPI:
    """Simple client for interacting with Polymarket API."""
    
    BASE_URL = "https://gamma-api.polymarket.com"
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize the Polymarket API client.
        
        Args:
            base_url: Optional custom base URL for the API.
        """
        self.base_url = base_url or self.BASE_URL
        self.session = requests.Session()
    
    def get_markets(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Fetch available markets from Polymarket.
        
        Args:
            limit: Maximum number of markets to return (default: 100).
            offset: Number of markets to skip (default: 0).
            
        Returns:
            List of market dictionaries.
            
        Raises:
            requests.RequestException: If the API request fails.
        """
        url = f"{self.base_url}/markets"
        params = {"limit": limit, "offset": offset}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_market(self, condition_id: str) -> Dict:
        """Fetch a specific market by condition ID.
        
        Args:
            condition_id: The unique identifier for the market condition.
            
        Returns:
            Market dictionary with details.
            
        Raises:
            requests.RequestException: If the API request fails.
        """
        url = f"{self.base_url}/markets/{condition_id}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def close(self):
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
