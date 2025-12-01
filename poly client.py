import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

class PolymarketScanner:
    def __init__(self):
        self.base_url = "https://gamma-api.polymarket.com"
        self.clob_url = "https://clob.polymarket.com"
        
    def get_active_markets(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Fetch active markets from Polymarket
        
        Args:
            limit: Number of markets to fetch (default 100, can go higher)
            offset: Pagination offset
            
        Returns:
            List of market dictionaries
        """
        endpoint = f"{self.base_url}/markets"
        
        params = {
            "limit": limit,
            "offset": offset,
            "closed": "false",  # Only active markets
            "order": "volume24hr",  # Order by 24h volume
            "ascending": "false"
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            print(f"API returned {len(data)} markets")
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching markets: {e}")
            return []
    
    def get_market_history(self, condition_id: str, interval: str = "1d") -> List[Dict]:
        """
        Get historical price data for a market
        
        Args:
            condition_id: The condition ID for the market
            interval: Time interval (1m, 5m, 1h, 1d)
            
        Returns:
            List of historical price points
        """
        endpoint = f"{self.base_url}/prices-history"
        
        params = {
            "market": condition_id,
            "interval": interval
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching market history: {e}")
            return []
    
    def parse_outcomes(self, outcomes_field) -> List[str]:
        """
        Parse outcomes field which might be a string, list, or JSON string
        """
        if isinstance(outcomes_field, list):
            return outcomes_field
        elif isinstance(outcomes_field, str):
            try:
                # Try to parse as JSON
                parsed = json.loads(outcomes_field)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            return [outcomes_field]
        return []
    
    def display_market_info(self, market: Dict) -> None:
        """Display formatted market information"""
        print(f"\n{'='*80}")
        print(f"Market: {market.get('question', 'N/A')}")
        print(f"Market ID: {market.get('id', 'N/A')}")
        print(f"Condition ID: {market.get('condition_id', 'N/A')}")
        print(f"Category: {market.get('category', 'N/A')}")
        
        # End date
        end_date = market.get('end_date_iso')
        if end_date:
            try:
                dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                print(f"Ends: {dt.strftime('%Y-%m-%d %H:%M UTC')}")
            except:
                print(f"Ends: {end_date}")
        
        # Volume
        volume = market.get('volume', 0)
        volume_24h = market.get('volume_24hr', 0)
        print(f"Total Volume: ${float(volume):,.2f}")
        print(f"24h Volume: ${float(volume_24h):,.2f}")
        
        # Liquidity
        liquidity = market.get('liquidity', 0)
        print(f"Liquidity: ${float(liquidity):,.2f}")
        
        # Parse outcomes properly
        outcomes_raw = market.get('outcomes', [])
        outcomes = self.parse_outcomes(outcomes_raw)
        tokens = market.get('tokens', [])
        
        print(f"\nOutcomes ({len(outcomes)}):")
        
        if tokens and len(tokens) > 0:
            # If we have token data with prices
            for i, outcome in enumerate(outcomes):
                if i < len(tokens):
                    token = tokens[i]
                    price = float(token.get('price', 0))
                    token_id = token.get('token_id', 'N/A')
                    winner = token.get('winner', False)
                    status = " ✓ WINNER" if winner else ""
                    print(f"  {i+1}. {outcome}: ${price:.4f} ({price*100:.2f}%){status}")
                    print(f"     Token ID: {token_id}")
                else:
                    print(f"  {i+1}. {outcome}: No price data")
        else:
            # Just list outcomes
            for i, outcome in enumerate(outcomes):
                print(f"  {i+1}. {outcome}")
        
        print(f"{'='*80}")
    
    def get_market_prices(self, market: Dict) -> Dict[str, float]:
        """
        Extract current prices for all outcomes in a market
        
        Returns:
            Dictionary mapping outcome names to prices
        """
        prices = {}
        outcomes_raw = market.get('outcomes', [])
        outcomes = self.parse_outcomes(outcomes_raw)
        tokens = market.get('tokens', [])
        
        for i, outcome in enumerate(outcomes):
            if i < len(tokens):
                price = float(tokens[i].get('price', 0))
                prices[outcome] = price
        
        return prices
    
    def plot_markets_over_time(self, markets: List[Dict], num_markets: int = 5):
        """
        Plot price history for top markets
        
        Args:
            markets: List of market dictionaries
            num_markets: Number of markets to plot
        """
        try:
            import matplotlib.pyplot as plt
            from matplotlib.dates import DateFormatter
        except ImportError:
            print("matplotlib not installed. Install with: pip install matplotlib")
            return
        
        print(f"\nFetching historical data for top {num_markets} markets...")
        
        fig, axes = plt.subplots(num_markets, 1, figsize=(12, 4*num_markets))
        if num_markets == 1:
            axes = [axes]
        
        for idx, market in enumerate(markets[:num_markets]):
            condition_id = market.get('condition_id')
            if not condition_id:
                print(f"Skipping market {idx+1}: No condition_id")
                continue
            
            print(f"Fetching data for: {market.get('question', 'Unknown')[:60]}...")
            history = self.get_market_history(condition_id, interval="1h")
            
            if not history:
                print(f"  No historical data available")
                continue
            
            # Parse outcomes
            outcomes = self.parse_outcomes(market.get('outcomes', []))
            
            # Plot each outcome
            ax = axes[idx]
            
            for outcome_idx, outcome in enumerate(outcomes):
                times = []
                prices = []
                
                for point in history:
                    if 'prices' in point and outcome_idx < len(point['prices']):
                        timestamp = datetime.fromisoformat(point['t'].replace('Z', '+00:00'))
                        price = float(point['prices'][outcome_idx])
                        times.append(timestamp)
                        prices.append(price * 100)  # Convert to percentage
                
                if times and prices:
                    ax.plot(times, prices, label=outcome, linewidth=2, marker='o', markersize=3)
            
            ax.set_title(market.get('question', 'Unknown')[:80], fontsize=10, fontweight='bold')
            ax.set_xlabel('Time')
            ax.set_ylabel('Price (%)')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 100])
            
            # Format x-axis
            ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            print(f"  ✓ Plotted {len(times)} data points")
            time.sleep(0.5)  # Rate limiting
        
        plt.tight_layout()
        plt.savefig('polymarket_price_history.png', dpi=150, bbox_inches='tight')
        print(f"\n✓ Chart saved as 'polymarket_price_history.png'")
        plt.show()


def main():
    # Initialize scanner
    scanner = PolymarketScanner()
    
    # Fetch active markets
    print("Fetching active markets from Polymarket...")
    markets = scanner.get_active_markets(limit=100)
    
    if not markets:
        print("No markets found or error occurred")
        return
    
    print(f"\nTotal markets retrieved: {len(markets)}\n")
    
    # Display top markets by volume
    print("\n" + "="*80)
    print("TOP MARKETS BY 24H VOLUME")
    print("="*80)
    
    for i, market in enumerate(markets[:10], 1):
        print(f"\n[Market {i}]")
        scanner.display_market_info(market)
        
        # Show price breakdown and check for arbitrage
        prices = scanner.get_market_prices(market)
        if prices:
            total_prob = sum(prices.values())
            print(f"\nTotal implied probability: {total_prob*100:.2f}%")
            if abs(total_prob - 1.0) > 0.01:
                arbitrage_gap = abs(1.0 - total_prob) * 100
                print(f"⚠️  ARBITRAGE OPPORTUNITY? Gap: {arbitrage_gap:.2f}%")
    
    # Statistics
    print("\n" + "="*80)
    print("MARKET STATISTICS")
    print("="*80)
    total_volume_24h = sum(float(m.get('volume_24hr', 0)) for m in markets)
    total_liquidity = sum(float(m.get('liquidity', 0)) for m in markets)
    
    print(f"Total markets: {len(markets)}")
    print(f"Total 24h volume: ${total_volume_24h:,.2f}")
    print(f"Total liquidity: ${total_liquidity:,.2f}")
    
    # Save to JSON
    filename = 'polymarket_active_markets.json'
    with open(filename, 'w') as f:
        json.dump(markets, f, indent=2)
    print(f"\nAll markets saved to '{filename}'")
    
    # Plot price history
    print("\n" + "="*80)
    print("PLOTTING PRICE HISTORY")
    print("="*80)
    scanner.plot_markets_over_time(markets, num_markets=5)


if __name__ == "__main__":
    main()