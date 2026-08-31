import logging
from collections.abc import Mapping
from typing import Any
from langchain_core.messages import HumanMessage, RemoveMessage
from tradingagents.agents.utils.crypto_data_tools import get_crypto_indicators, get_crypto_market_data, get_derivatives_metrics, get_onchain_metrics, get_order_flow
from tradingagents.agents.utils.macro_data_tools import get_macro_indicators
from tradingagents.agents.utils.news_data_tools import get_global_news, get_news
from tradingagents.agents.utils.prediction_markets_tools import get_prediction_markets

# Compatibility aliases are intentionally kept only so older modules can import
# during the staged migration. They are not part of the crypto workflow.
get_stock_data = get_crypto_market_data
get_indicators = get_crypto_indicators
get_verified_market_snapshot = get_crypto_market_data
get_insider_transactions = get_news
get_fundamentals = get_balance_sheet = get_cashflow = get_income_statement = get_macro_indicators

__all__ = [
    "get_crypto_market_data", "get_crypto_indicators", "get_indicators", "get_stock_data",
    "get_news", "get_global_news", "get_macro_indicators", "get_prediction_markets",
    "get_onchain_metrics", "get_derivatives_metrics", "get_order_flow",
    "get_verified_market_snapshot", "get_fundamentals", "get_balance_sheet", "get_cashflow", "get_income_statement", "get_insider_transactions",
    "build_instrument_context", "resolve_instrument_identity", "get_instrument_context_from_state", "get_language_instruction", "create_msg_delete",
]

logger = logging.getLogger(__name__)

def get_language_instruction() -> str:
    from tradingagents.dataflows.config import get_config
    lang = get_config().get("output_language", "English")
    return "" if lang.strip().lower() == "english" else f" Write your entire response in {lang}."

def opponent_argument_or_opening(text: str, opponent: str) -> str:
    return (text or "").strip() or f"(The {opponent} has not spoken yet — open the debate with your own case.)"

def resolve_instrument_identity(ticker: str) -> dict:
    return {"symbol": ticker.strip().upper()}

def build_instrument_context(ticker: str, asset_type: str = "crypto", identity: Mapping[str, str] | None = None) -> str:
    return f"The crypto asset to analyze is `{ticker}`. Use this exact symbol in every tool call, report, and recommendation. Treat it as a crypto asset, not a company; do not invent corporate fundamentals."

def get_instrument_context_from_state(state: Mapping[str, Any]) -> str:
    context = state.get("instrument_context")
    return context if isinstance(context, str) and context.strip() else build_instrument_context(str(state["company_of_interest"]), "crypto")

def create_msg_delete():
    def delete_messages(state):
        removals = [RemoveMessage(id=m.id) for m in state["messages"]]
        return {"messages": removals + [HumanMessage(content=f"Proceed with your assigned analysis. {get_instrument_context_from_state(state)} The analysis date is {state.get('trade_date', 'the requested date')}.")]}
    return delete_messages
