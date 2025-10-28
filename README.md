# exploring-polymarket-arbitrage

A Python project for exploring arbitrage opportunities on Polymarket.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Example

```python
from src.polymarket_api import PolymarketAPI

# Using context manager (recommended)
with PolymarketAPI() as api:
    # Fetch markets
    markets = api.get_markets(limit=10)
    for market in markets:
        print(market['question'])
    
    # Fetch a specific market
    market = api.get_market("condition_id_here")
```

### Available Methods

- `get_markets(limit=100, offset=0)`: Fetch available markets
- `get_market(condition_id)`: Fetch a specific market by condition ID

## Testing

Run tests with pytest:
```bash
pytest tests/ -v
```

## Example

Run the example script:
```bash
python example.py
```