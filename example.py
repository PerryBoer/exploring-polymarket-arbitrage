"""Example usage of the Polymarket API client."""

from src.polymarket_api import PolymarketAPI


def main():
    """Demonstrate basic usage of the Polymarket API."""
    # Using context manager (recommended)
    with PolymarketAPI() as api:
        try:
            # Fetch first 5 markets
            print("Fetching markets...")
            markets = api.get_markets(limit=5)
            
            print(f"\nFound {len(markets)} markets:")
            for i, market in enumerate(markets, 1):
                print(f"\n{i}. {market.get('question', 'N/A')}")
                print(f"   Condition ID: {market.get('condition_id', 'N/A')}")
                
        except Exception as e:
            print(f"Error fetching markets: {e}")


if __name__ == "__main__":
    main()
