"""Tests for Polymarket API client."""

import pytest
from unittest.mock import Mock, patch
from src.polymarket_api import PolymarketAPI


class TestPolymarketAPI:
    """Test suite for PolymarketAPI class."""
    
    def test_initialization(self):
        """Test API client initialization."""
        api = PolymarketAPI()
        assert api.base_url == "https://gamma-api.polymarket.com"
        
        custom_url = "https://custom.api.com"
        api_custom = PolymarketAPI(base_url=custom_url)
        assert api_custom.base_url == custom_url
    
    @patch('src.polymarket_api.requests.Session')
    def test_get_markets(self, mock_session_class):
        """Test fetching markets."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "1", "question": "Test market 1"},
            {"id": "2", "question": "Test market 2"}
        ]
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        api = PolymarketAPI()
        markets = api.get_markets(limit=10, offset=0)
        
        assert len(markets) == 2
        assert markets[0]["id"] == "1"
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert "markets" in call_args[0][0]
        assert call_args[1]["params"]["limit"] == 10
    
    @patch('src.polymarket_api.requests.Session')
    def test_get_market(self, mock_session_class):
        """Test fetching a specific market."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "condition_id": "test123",
            "question": "Test market"
        }
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        api = PolymarketAPI()
        market = api.get_market("test123")
        
        assert market["condition_id"] == "test123"
        mock_session.get.assert_called_once()
        assert "test123" in mock_session.get.call_args[0][0]
    
    @patch('src.polymarket_api.requests.Session')
    def test_context_manager(self, mock_session_class):
        """Test API client as context manager."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        with PolymarketAPI() as api:
            assert api is not None
        
        mock_session.close.assert_called_once()
