from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_crypto_indicators,
    get_crypto_market_data,
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_market_analyst(llm):
    def market_analyst_node(state):
        current_date = state["trade_date"]
        context = get_instrument_context_from_state(state)
        tools = [get_crypto_market_data, get_crypto_indicators]
        system_message = (
            "You are the Market Analyst for a crypto trading research team. Analyze price, volume, trend, momentum and volatility for the exact crypto asset. "
            "Use get_crypto_market_data for OHLCV and current 24h data, then get_crypto_indicators for SMA/EMA/RSI/MACD/volume context. "
            "Do not discuss company financial statements or stock fundamentals. Use exact tool values for numerical claims and clearly state uncertainty. "
            "Append a Markdown table summarizing the key market evidence."
            + get_language_instruction()
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant collaborating with crypto trading analysts. Use the provided tools. Available tools: {tools}. Today's analysis date is {date}. {context}\n{system}"),
            MessagesPlaceholder(variable_name="messages"),
        ]).partial(tools=", ".join(t.name for t in tools), date=current_date, context=context, system=system_message)
        result = (prompt | llm.bind_tools(tools)).invoke(state["messages"])
        return {"messages": [result], "market_report": result.content if not result.tool_calls else ""}
    return market_analyst_node
