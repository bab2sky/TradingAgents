import functools
import logging
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage, RemoveMessage

from tradingagents.agents.utils.crypto_data_tools import (
    get_crypto_indicators,
    get_crypto_market_data,
    get_derivatives_metrics,
    get_onchain_metrics,
    get_order_flow,
)
from tradingagents.agents.utils.macro_data_tools import get_macro_indicators
from tradingagents.agents.utils.news_data_tools import get_global_news, get_news
from tradingagents.agents.utils.prediction_markets_tools import get_prediction_markets
from tradingagents.agents.utils.technical_indicators_tools import get_indicators

__all__ = [
    "get_crypto_market_data",
    "get_crypto_indicators",
    "get_indicators",
    "get_news",
    "get_global_news",
    "get_macro_indicators",
    "get_prediction_markets",
    "get_onchain_metrics",
    "get_derivatives_metrics",
    "get_order_flow",
    "build_instrument_context",
    "resolve_instrument_identity",
    "get_instrument_context_from_state",
    "get_language_instruction",
    "create_msg_delete",
]

logger = logging.getLogger(__name__)


def get_language_instruction() -> str:
    from tradingagents.dataflows.config import get_config
    lang = get_config().get("output_language", "English")
    if lang.strip().lower() == "english":
        return ""
    return f" Write your entire response in {lang}."


def opponent_argument_or_opening(text: str, opponent: str) -> str:
    text = (text or "").strip()
    return text or f"(The {opponent} has not spoken yet — open the debate with your own case.)"


def _clean_identity_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned if cleaned and cleaned.lower() not in {"none", "n/a", "nan", "null"} else None


def resolve_instrument_identity(ticker: str) -> dict:
    """Return minimal crypto identity without treating the asset as a company."""
    return {"symbol": ticker.strip().upper()}


def build_instrument_context(ticker: str, asset_type: str = "crypto", identity: Mapping[str, str] | None = None) -> str:
    context = (
        f"The crypto asset to analyze is `{ticker}`. Use this exact symbol in every tool call, report, and recommendation. "
        "Treat it as a crypto asset, not a company; do not invent corporate fundamentals."
    )
    if identity and identity.get("symbol"):
        context += f" Canonical asset symbol: `{identity['symbol']}`."
    return context


def get_instrument_context_from_state(state: Mapping[str, Any]) -> str:
    context = state.get("instrument_context")
    if isinstance(context, str) and context.strip():
        return context
    return build_instrument_context(str(state["company_of_interest"]), "crypto")


def create_msg_delete():
    def delete_messages(state):
        messages = state["messages"]
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        context = get_instrument_context_from_state(state)
        date = state.get("trade_date", "the requested date")
        return {"messages": removal_operations + [HumanMessage(content=f"Proceed with your assigned analysis. {context} The analysis date is {date}.")]}
    return delete_messages
