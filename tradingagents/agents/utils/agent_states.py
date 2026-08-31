from typing import Annotated
from langgraph.graph import MessagesState
from typing_extensions import TypedDict

class InvestDebateState(TypedDict):
    bull_history: Annotated[str, "Bullish conversation history"]
    bear_history: Annotated[str, "Bearish conversation history"]
    history: Annotated[str, "Conversation history"]
    current_response: Annotated[str, "Latest response"]
    judge_decision: Annotated[str, "Final judge decision"]
    count: Annotated[int, "Conversation length"]

class RiskDebateState(TypedDict):
    aggressive_history: Annotated[str, "Aggressive analyst history"]
    conservative_history: Annotated[str, "Conservative analyst history"]
    neutral_history: Annotated[str, "Neutral analyst history"]
    history: Annotated[str, "Risk conversation history"]
    latest_speaker: Annotated[str, "Last speaker"]
    current_aggressive_response: Annotated[str, "Latest aggressive response"]
    current_conservative_response: Annotated[str, "Latest conservative response"]
    current_neutral_response: Annotated[str, "Latest neutral response"]
    judge_decision: Annotated[str, "Risk judge decision"]
    count: Annotated[int, "Conversation length"]

class AgentState(MessagesState):
    company_of_interest: Annotated[str, "Crypto asset under analysis"]
    asset_type: Annotated[str, "Always crypto in this build"]
    instrument_context: Annotated[str, "Deterministic asset identity context"]
    trade_date: Annotated[str, "Analysis date"]
    sender: Annotated[str, "Agent that sent this message"]

    market_report: Annotated[str, "Market Analyst report"]
    sentiment_report: Annotated[str, "Sentiment Analyst report"]
    news_report: Annotated[str, "News Analyst report"]
    onchain_report: Annotated[str, "On-chain Analyst report"]
    derivatives_report: Annotated[str, "Derivatives Analyst report"]
    order_flow_report: Annotated[str, "Order Flow Analyst report"]
    macro_report: Annotated[str, "Macro Analyst report"]

    investment_debate_state: Annotated[InvestDebateState, "Investment debate state"]
    investment_plan: Annotated[str, "Research manager investment plan"]
    trader_investment_plan: Annotated[str, "Trader investment plan"]
    risk_debate_state: Annotated[RiskDebateState, "Risk debate state"]
    final_trade_decision: Annotated[str, "Final risk decision"]
    past_context: Annotated[str, "Optional historical context"]
