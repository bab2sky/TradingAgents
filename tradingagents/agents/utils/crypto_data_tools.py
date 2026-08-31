"""Crypto-native market data tools.

These tools are deliberately independent from Vibe-Trading. They provide a
small, public-API based crypto data surface for the standalone Crypto
TradingAgents phase. Execution/broker integration is intentionally out of scope.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from langchain_core.tools import tool

_BINANCE = "https://api.binance.com"
_MEMPOOL = "https://mempool.space/api"


def _symbol(value: str) -> str:
    s = value.strip().upper().replace("/", "-")
    for suffix in ("-USD", "-USDT", "-USDC"):
        if s.endswith(suffix):
            return s[: -len(suffix)] + "USDT"
    if s.endswith("USDT"):
        return s
    return s + "USDT"


def _get(url: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


@tool
def get_crypto_market_data(ticker: str, interval: str = "1d", limit: int = 120) -> str:
    """Get recent OHLCV candles and current crypto market price from Binance public API."""
    symbol = _symbol(ticker)
    klines = _get(f"{_BINANCE}/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": min(limit, 1000)})
    book = _get(f"{_BINANCE}/api/v3/ticker/24hr", {"symbol": symbol})
    rows = [
        {
            "time": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).isoformat(),
            "open": float(k[1]), "high": float(k[2]), "low": float(k[3]),
            "close": float(k[4]), "volume": float(k[5]),
        }
        for k in klines
    ]
    return json.dumps({"symbol": symbol, "interval": interval, "candles": rows,
                       "24h": {"last": float(book["lastPrice"]), "change_pct": float(book["priceChangePercent"]),
                               "volume": float(book["volume"])}}, ensure_ascii=False)


@tool
def get_crypto_indicators(ticker: str, interval: str = "1d", limit: int = 200) -> str:
    """Calculate common technical indicators from Binance crypto candles."""
    data = json.loads(get_crypto_market_data(ticker, interval, limit).content if hasattr(get_crypto_market_data(ticker, interval, limit), "content") else get_crypto_market_data(ticker, interval, limit))
    closes = [x["close"] for x in data["candles"]]
    volumes = [x["volume"] for x in data["candles"]]
    if len(closes) < 30:
        return json.dumps({"error": "insufficient candle history", "symbol": data["symbol"]})

    def sma(n: int) -> float:
        return sum(closes[-n:]) / n

    def ema(n: int) -> float:
        alpha = 2 / (n + 1)
        value = closes[0]
        for price in closes[1:]:
            value = alpha * price + (1 - alpha) * value
        return value

    gains, losses = [], []
    for a, b in zip(closes[-15:], closes[-14:]):
        d = b - a
        gains.append(max(d, 0)); losses.append(max(-d, 0))
    avg_gain = sum(gains) / 14
    avg_loss = sum(losses) / 14
    rsi = 100.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)

    fast = ema(12)
    slow = ema(26)
    macd = fast - slow
    result = {
        "symbol": data["symbol"], "last": closes[-1],
        "sma_20": sma(20), "sma_50": sma(50), "ema_12": fast, "ema_26": slow,
        "rsi_14": rsi, "macd": macd,
        "volume_20_avg": sum(volumes[-20:]) / 20,
    }
    return json.dumps(result, ensure_ascii=False)


@tool
def get_onchain_metrics(ticker: str, lookback_days: int = 7) -> str:
    """Get public on-chain metrics where a reliable chain endpoint is available."""
    base = ticker.upper().replace("/", "-")
    if base.startswith("BTC"):
        tip = _get(f"{_MEMPOOL}/blocks/tip/height")
        fees = _get(f"{_MEMPOOL}/fees/recommended")
        return json.dumps({"asset": "BTC", "tip_height": tip, "recommended_fees": fees,
                           "note": "Public mempool metrics; exchange-flow and whale-wallet attribution are not inferred."}, ensure_ascii=False)
    return json.dumps({"asset": ticker, "available": False,
                       "note": "No chain-specific endpoint is enabled for this asset in Crypto TradingAgents v1. Add a provider later without changing the analyst interface."}, ensure_ascii=False)


@tool
def get_derivatives_metrics(ticker: str) -> str:
    """Get Binance perpetual futures funding, open interest and mark-price metrics."""
    symbol = _symbol(ticker)
    mark = _get(f"{_BINANCE}/fapi/v1/premiumIndex", {"symbol": symbol})
    oi = _get(f"{_BINANCE}/fapi/v1/openInterest", {"symbol": symbol})
    funding = _get(f"{_BINANCE}/fapi/v1/fundingRate", {"symbol": symbol, "limit": 5})
    return json.dumps({"symbol": symbol, "mark": mark, "open_interest": oi,
                       "recent_funding": funding}, ensure_ascii=False)


@tool
def get_order_flow(ticker: str, limit: int = 20) -> str:
    """Get crypto order-book depth and recent trades from Binance public API."""
    symbol = _symbol(ticker)
    depth = _get(f"{_BINANCE}/api/v3/depth", {"symbol": symbol, "limit": min(limit, 100)})
    trades = _get(f"{_BINANCE}/api/v3/trades", {"symbol": symbol, "limit": 100})
    bid_volume = sum(float(p) * float(q) for p, q in depth["bids"])
    ask_volume = sum(float(p) * float(q) for p, q in depth["asks"])
    buy = sum(float(t["qty"]) for t in trades if not t["isBuyerMaker"])
    sell = sum(float(t["qty"]) for t in trades if t["isBuyerMaker"])
    return json.dumps({"symbol": symbol, "best_bid": depth["bids"][0] if depth["bids"] else None,
                       "best_ask": depth["asks"][0] if depth["asks"] else None,
                       "bid_notional": bid_volume, "ask_notional": ask_volume,
                       "recent_buy_qty": buy, "recent_sell_qty": sell,
                       "imbalance": (bid_volume - ask_volume) / (bid_volume + ask_volume) if bid_volume + ask_volume else 0}, ensure_ascii=False)
