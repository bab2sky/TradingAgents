"""Crypto-native public market data tools for standalone Crypto TradingAgents."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any
import requests
from langchain_core.tools import tool
_BINANCE = "https://api.binance.com"
_MEMPOOL = "https://mempool.space/api"

def _symbol(value: str) -> str:
    s = value.strip().upper().replace("/", "-")
    for suffix in ("-USD", "-USDT", "-USDC"):
        if s.endswith(suffix): return s[:-len(suffix)] + "USDT"
    return s if s.endswith("USDT") else s + "USDT"

def _get(url: str, params: dict[str, Any] | None = None) -> Any:
    r = requests.get(url, params=params, timeout=15); r.raise_for_status(); return r.json()

def _market_payload(ticker: str, interval: str, limit: int) -> dict:
    symbol = _symbol(ticker)
    klines = _get(f"{_BINANCE}/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": min(limit, 1000)})
    book = _get(f"{_BINANCE}/api/v3/ticker/24hr", {"symbol": symbol})
    rows = [{"time": datetime.fromtimestamp(k[0]/1000, tz=timezone.utc).isoformat(), "open": float(k[1]), "high": float(k[2]), "low": float(k[3]), "close": float(k[4]), "volume": float(k[5])} for k in klines]
    return {"symbol": symbol, "interval": interval, "candles": rows, "24h": {"last": float(book["lastPrice"]), "change_pct": float(book["priceChangePercent"]), "volume": float(book["volume"])} }

@tool
def get_crypto_market_data(ticker: str, interval: str = "1d", limit: int = 120) -> str:
    """Get recent OHLCV candles and 24h crypto market data from Binance public API."""
    return json.dumps(_market_payload(ticker, interval, limit), ensure_ascii=False)

@tool
def get_crypto_indicators(ticker: str, interval: str = "1d", limit: int = 200) -> str:
    """Calculate SMA, EMA, RSI, MACD and volume metrics from crypto candles."""
    data = _market_payload(ticker, interval, limit); closes = [x["close"] for x in data["candles"]]; volumes = [x["volume"] for x in data["candles"]]
    if len(closes) < 50: return json.dumps({"error": "insufficient candle history", "symbol": data["symbol"]})
    def sma(n): return sum(closes[-n:]) / n
    def ema(n):
        a = 2/(n+1); v = closes[0]
        for p in closes[1:]: v = a*p + (1-a)*v
        return v
    gains, losses = [], []
    for a,b in zip(closes[-15:], closes[-14:]):
        d=b-a; gains.append(max(d,0)); losses.append(max(-d,0))
    ag=sum(gains)/14; al=sum(losses)/14; rsi=100 if al == 0 else 100-100/(1+ag/al)
    e12,e26=ema(12),ema(26)
    return json.dumps({"symbol":data["symbol"],"last":closes[-1],"sma_20":sma(20),"sma_50":sma(50),"ema_12":e12,"ema_26":e26,"rsi_14":rsi,"macd":e12-e26,"volume_20_avg":sum(volumes[-20:])/20}, ensure_ascii=False)

@tool
def get_onchain_metrics(ticker: str, lookback_days: int = 7) -> str:
    """Get public on-chain metrics where a reliable chain endpoint is enabled."""
    if ticker.upper().replace("/","-").startswith("BTC"):
        return json.dumps({"asset":"BTC","tip_height":_get(f"{_MEMPOOL}/blocks/tip/height"),"recommended_fees":_get(f"{_MEMPOOL}/fees/recommended"),"note":"Public mempool metrics only; exchange-flow and whale attribution are not inferred."}, ensure_ascii=False)
    return json.dumps({"asset":ticker,"available":False,"note":"No chain-specific endpoint is enabled for this asset in v1."}, ensure_ascii=False)

@tool
def get_derivatives_metrics(ticker: str) -> str:
    """Get Binance perpetual funding, open interest and mark-price metrics."""
    symbol=_symbol(ticker); return json.dumps({"symbol":symbol,"mark":_get(f"https://fapi.binance.com/fapi/v1/premiumIndex",{"symbol":symbol}),"open_interest":_get(f"https://fapi.binance.com/fapi/v1/openInterest",{"symbol":symbol}),"recent_funding":_get(f"https://fapi.binance.com/fapi/v1/fundingRate",{"symbol":symbol,"limit":5})}, ensure_ascii=False)

@tool
def get_order_flow(ticker: str, limit: int = 20) -> str:
    """Get Binance order-book depth and recent trade flow."""
    symbol=_symbol(ticker); depth=_get(f"{_BINANCE}/api/v3/depth",{"symbol":symbol,"limit":min(limit,100)}); trades=_get(f"{_BINANCE}/api/v3/trades",{"symbol":symbol,"limit":100})
    bid=sum(float(p)*float(q) for p,q in depth["bids"]); ask=sum(float(p)*float(q) for p,q in depth["asks"]); buy=sum(float(t["qty"]) for t in trades if not t["isBuyerMaker"]); sell=sum(float(t["qty"]) for t in trades if t["isBuyerMaker"])
    return json.dumps({"symbol":symbol,"best_bid":depth["bids"][0] if depth["bids"] else None,"best_ask":depth["asks"][0] if depth["asks"] else None,"bid_notional":bid,"ask_notional":ask,"recent_buy_qty":buy,"recent_sell_qty":sell,"imbalance":(bid-ask)/(bid+ask) if bid+ask else 0}, ensure_ascii=False)
