"""
Polymarket API quickstart (read-only):
- List markets (Gamma + CLOB simplified)
- Extract outcome token_ids
- Fetch order book summary (/book)
- Fetch recent trades (Data-API /trades)
- Compute sum of YES prices via /prices (best ask)

Requires: Python 3.10+, `pip install requests` (optional: `pandas`)
No auth used (read-only). Placing orders requires L2 auth (not included).
"""

from __future__ import annotations
import math
from typing import Dict, List, Any, Iterable, Tuple, Optional
import requests

try:
    import pandas as pd  # optional; script works without it
except Exception:
    pd = None

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
DATA = "https://data-api.polymarket.com"


# ----------------------------
# 1) Gamma markets (discovery)
# ----------------------------
def list_markets_gamma(
    limit: int = 25,
    cursor: Optional[str] = None,
    closed: bool = False,
    active: Optional[bool] = True,
) -> Dict[str, Any]:
    """
    GET /markets from Gamma (handy for discovery/metadata).
    Use closed=false to avoid archived markets; active=True to focus on live ones.
    """
    params: Dict[str, Any] = {"limit": limit, "closed": str(closed).lower()}
    if active is not None:
        params["active"] = str(active).lower()
    if cursor:
        params["cursor"] = cursor
    r = requests.get(f"{GAMMA}/markets", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


# ------------------------------------------------------------
# 2) CLOB simplified-markets (stable shape; includes token_ids)
# ------------------------------------------------------------
def list_simplified_markets(next_cursor: Optional[str] = None) -> Dict[str, Any]:
    """
    GET /simplified-markets from CLOB (paginated via next_cursor).
    Returns { "data": [SimplifiedMarket...], "next_cursor": "..." }
    Each market has: condition_id, active/closed, tokens=[{token_id, name}, ...]
    """
    params: Dict[str, Any] = {}
    if next_cursor:
        params["next_cursor"] = next_cursor
    r = requests.get(f"{CLOB}/simplified-markets", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def clob_simplified_pages(max_pages: int = 2) -> Iterable[Dict[str, Any]]:
    """Yield up to max_pages pages from /simplified-markets."""
    cursor = None
    for _ in range(max_pages):
        page = list_simplified_markets(cursor)
        yield page
        cursor = page.get("next_cursor")
        if not cursor:
            break


def flatten_tokens_from_simplified(page_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Flatten a CLOB simplified-markets page -> list of tokens with market grouping.
    Output rows: {condition_id, active, closed, token_id, label}
    """
    data = page_json.get("data", [])
    rows: List[Dict[str, Any]] = []
    for m in data:
        cond = m.get("condition_id")
        active = m.get("active")
        closed = m.get("closed")
        tokens = m.get("tokens") or []
        for t in tokens:
            rows.append(
                {
                    "condition_id": cond,
                    "active": bool(active),
                    "closed": bool(closed),
                    "token_id": str(t.get("token_id")) if t.get("token_id") is not None else None,
                    "label": t.get("name") or t.get("outcome") or t.get("title"),
                }
            )
    return rows


# -------------------------------------
# 3) Order book + prices (CLOB, public)
# -------------------------------------
def get_book(token_id: str) -> Dict[str, Any]:
    """
    GET /book for a single token_id (summary + levels).
    Returns {"error": "not_found"} if 404, rather than raising.
    """
    r = requests.get(f"{CLOB}/book", params={"token_id": token_id}, timeout=20)
    if r.status_code == 404:
        return {"error": "not_found", "token_id": token_id}
    r.raise_for_status()
    return r.json()


def get_best_prices(token_ids: List[str], side: str = "BUY", batch_size: int = 50) -> Dict[str, Dict[str, Any]]:
    """
    POST /prices for batches of token_ids.
    side="BUY" -> best ask (what you'd pay), side="SELL" -> best bid.
    Returns mapping: { token_id: { "BUY": "0.5123" } } (string numbers).
    """
    out: Dict[str, Dict[str, Any]] = {}
    if not token_ids:
        return out
    for i in range(0, len(token_ids), batch_size):
        batch = token_ids[i : i + batch_size]
        payload = {"params": [{"token_id": tid, "side": side} for tid in batch]}
        r = requests.post(f"{CLOB}/prices", json=payload, timeout=20)
        r.raise_for_status()
        data = r.json() or {}
        # API returns {asset_id: {side: price_string}}
        for asset_id, sides in (data.items() if isinstance(data, dict) else []):
            out[str(asset_id)] = sides
    return out


# ------------------------------
# 4) Trades (Data-API, read-only)
# ------------------------------
def get_trades_dataapi(condition_id: Optional[str] = None, limit: int = 25) -> Dict[str, Any]:
    """
    GET /trades from Data-API (public). Filter with market=<conditionId>.
    """
    params: Dict[str, Any] = {"limit": limit}
    if condition_id:
        params["market"] = condition_id
    r = requests.get(f"{DATA}/trades", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


# -------------------------------------------------------------------
# 5) Compute sum of YES (best ask) per market (binary & multi-outcome)
# -------------------------------------------------------------------
def _to_float(x: Any) -> float:
    try:
        if x is None:
            return math.nan
        return float(x)
    except Exception:
        return math.nan


def sum_yes_by_market(tokens: List[Dict[str, Any]]) -> List[Tuple[str, int, float]]:
    """
    For each condition_id (market), sum best asks across its tokens using /prices (BUY side).
    Returns list of (condition_id, n_tokens, sum_best_ask), sorted ascending by sum.
    """
    # group token_ids per market
    by_market: Dict[str, List[str]] = {}
    for t in tokens:
        cond = t.get("condition_id")
        tid = t.get("token_id")
        closed = t.get("closed")
        if cond and tid and not closed:
            by_market.setdefault(cond, []).append(tid)

    # batch query best asks
    all_token_ids = [tid for lst in by_market.values() for tid in lst]
    price_map = get_best_prices(all_token_ids, side="BUY")  # best ask

    results: List[Tuple[str, int, float]] = []
    for cond, tids in by_market.items():
        asks = []
        for tid in tids:
            p = None
            if tid in price_map:
                p = price_map[tid].get("BUY")
            asks.append(_to_float(p))
        finite = [x for x in asks if isinstance(x, (int, float)) and not math.isnan(x)]
        s = sum(finite) if finite else math.nan
        results.append((cond, len(tids), s))

    results.sort(key=lambda x: (math.inf if math.isnan(x[2]) else x[2]))
    return results


# -----------------
# 6) Demo / driver
# -----------------
def main():
    print("=== Gamma /markets sample (filtered to live) ===")
    gm = list_markets_gamma(limit=10, closed=False, active=True)
    # Gamma shape may be list or dict with 'data'; print a small preview of keys/first row
    if isinstance(gm, dict):
        print("Gamma top-level keys:", list(gm)[:6])
        first = (gm.get("data") or gm.get("markets") or gm)
        if isinstance(first, list) and first:
            print("Gamma first market keys:", list(first[0])[:10])
    elif isinstance(gm, list) and gm:
        print("Gamma first market keys:", list(gm[0])[:10])

    print("\n=== CLOB /simplified-markets (2 pages) ===")
    pages = []
    for page in clob_simplified_pages(max_pages=2):
        pages.append(page)
        print("Page keys:", list(page)[:5], "| next_cursor:", page.get("next_cursor"))

    if not pages:
        print("No CLOB pages returned.")
        return

    # Flatten tokens from the first page and filter to live (not closed)
    tokens = flatten_tokens_from_simplified(pages[0])
    live = [t for t in tokens if t.get("token_id") and not t.get("closed")]
    print(f"\nExtracted tokens from first simplified page: {len(tokens)} | live: {len(live)}")
    if live:
        print("Token sample:", {k: live[0][k] for k in ["condition_id", "label", "token_id"]})

    # Fetch one order book for the first live token_id
    if live:
        print("\n=== CLOB /book sample ===")
        tid = live[0]["token_id"]
        book = get_book(tid)
        if "error" in book:
            print("Book not found (404) for token:", tid)
        else:
            print("Book top-level keys:", list(book)[:10], "| token:", tid)

    # Fetch recent trades from Data-API using condition_id (market)
    if live:
        print("\n=== Data-API /trades sample ===")
        cond = live[0]["condition_id"]
        trades = get_trades_dataapi(condition_id=cond, limit=10)
        # Usually returns dict with keys such as "data" (list of trades) and paging cursors
        print("Trades payload keys:", list(trades)[:10])

    # Compute sum of YES (best ask) per market and show top deviations from 1
    print("\n=== Sum of YES prices by market (best ask via /prices) ===")
    sums = sum_yes_by_market(live)
    shown = 0
    for cond, n_tok, s in sums:
        if isinstance(s, float) and not math.isnan(s):
            dev = s - 1.0
            print(f"[{cond}] n={n_tok}  sum_yes={s:.3f}  dev_from_1={dev:+.3f}")
            shown += 1
        if shown >= 15:
            break

    # Optional: pretty table with pandas if available
    if pd is not None and sums:
        print("\nTop 15 by sum_yes (ascending):")
        df = pd.DataFrame(sums, columns=["condition_id", "n_tokens", "sum_yes"])
        print(df.sort_values("sum_yes").head(15).to_string(index=False))


if __name__ == "__main__":
    main()
