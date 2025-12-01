## Quick context for AI agents

This repository is a small Python project that fetches Polymarket (Gamma / CLOB / Data-API) read-only data and explores simple arbitrage/analytics.

- Primary code: `src/polymarket_api.py` (lightweight client, context-manager friendly)
- Utilities & demos: `api.py` (detailed helpers for Gamma/CLOB/Data API), `poly client.py` (PolymarketFetcher/Plotter), `example.py` (usage/demo)
- Persisted sample data: `polymarket_active_markets.json` (snapshot used by demos)
- Tests: `tests/test_polymarket_api.py` (pytest + unittest.mock patterns)

Key takeaways for a coding agent
--------------------------------

1) Big picture / data flows
   - Discovery: Gamma (`/markets`) is used for discovery/metadata (see `api.py::list_markets_gamma`).
   - Stable market shape: CLOB `/simplified-markets` provides `token_id` and outcome tokens (see `api.py::list_simplified_markets` and `flatten_tokens_from_simplified`).
   - Prices & books: CLOB `/book` and `/prices` endpoints are used to compute best asks/bids (see `api.py::get_book`, `get_best_prices`).
   - Trades: Data-API `/trades` is used for recent trade history (see `api.py::get_trades_dataapi`).

2) Conventions and patterns to follow
   - Use the `PolymarketAPI` client in `src/polymarket_api.py` (it exposes `get_markets` and `get_market`) and supports context-manager usage (preferred in examples and README).
   - Network calls use `requests` with explicit timeouts (10–20s) and a `requests.Session()` in the client. Keep mocks consistent with the import path used in tests: patch `src.polymarket_api.requests.Session`.
   - Outcomes/tokens are sometimes stringified JSON in the payloads. Use `PolymarketFetcher.parse_outcomes` pattern when parsing `outcomes` fields.
   - Numeric fields may be strings in sample data (`polymarket_active_markets.json`); convert carefully (float/Decimal) and tolerate missing/None values.

3) Testing & mocking notes
   - Tests use pytest and `unittest.mock.patch`. Example: `@patch('src.polymarket_api.requests.Session')` in `tests/test_polymarket_api.py` — patch the client module’s imported `requests` object rather than the top-level `requests` name.
   - Keep tests fast: most logic is offline parsing and small HTTP response shapes; prefer unit tests that mock network I/O.

4) How to run locally (developer workflows)
   - Install deps: `pip install -r requirements.txt` (README confirmed)
   - Run demo: `python example.py` or `python poly\ client.py` (these scripts use the client and will save `polymarket_active_markets.json`)
   - Run tests: `pytest tests/ -v`

5) Small implementation guidance for PRs
   - Preserve context-manager and session usage in `src/polymarket_api.py` (it is relied on by examples/tests).
   - When adding new network calls: add timeouts, handle 404/empty payloads gracefully (see `api.py::get_book` which returns `{"error": "not_found"}` for 404).
   - Follow existing JSON-shape defensive coding (check for dict/list, optional keys). Add a short unit test that mocks `requests.Session` for any new client method.

6) Files to open first when working here
   - `README.md` — quick usage and commands
   - `src/polymarket_api.py` — canonical minimal client
   - `api.py` — expanded helpers showing real API shapes and parsing
   - `tests/test_polymarket_api.py` — unit test/mocking examples

If anything here is unclear or you want a different tone/length, tell me which sections to expand or remove and I’ll iterate.
