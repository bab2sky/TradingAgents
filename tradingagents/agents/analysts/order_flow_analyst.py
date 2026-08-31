from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.crypto_data_tools import get_order_flow
from tradingagents.agents.utils.agent_utils import get_instrument_context_from_state, get_language_instruction


def create_order_flow_analyst(llm):
    def node(state):
        context = get_instrument_context_from_state(state)
        tools = [get_order_flow]
        system = (
            "You are the Order Flow Analyst for a crypto trading research team. "
            "Analyze order-book depth, bid/ask notional imbalance and recent aggressive trade flow. "
            "Use the tool output as the sole source for exact values. Explain liquidity conditions, pressure and possible execution implications. "
            "Do not infer hidden orders or future price movement as facts. Append a concise Markdown evidence table."
            + get_language_instruction()
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are collaborating with other trading analysts. {context} The analysis date is {date}. Available tools: {tools}.\n{system}"),
            MessagesPlaceholder(variable_name="messages"),
        ]).partial(context=context, date=state["trade_date"], tools=", ".join(t.name for t in tools), system=system)
        result = (prompt | llm.bind_tools(tools)).invoke(state["messages"])
        return {"messages": [result], "order_flow_report": result.content if not result.tool_calls else ""}
    return node
