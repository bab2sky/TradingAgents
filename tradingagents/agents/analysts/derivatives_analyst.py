from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.crypto_data_tools import get_derivatives_metrics
from tradingagents.agents.utils.agent_utils import get_instrument_context_from_state, get_language_instruction


def create_derivatives_analyst(llm):
    def node(state):
        context = get_instrument_context_from_state(state)
        tools = [get_derivatives_metrics]
        system = (
            "You are the Derivatives Analyst for a crypto trading research team. "
            "Analyze perpetual-futures funding, open interest, mark price and recent funding observations. "
            "Identify leverage crowding, confirmation/divergence and liquidation risk only when supported by data. "
            "Never fabricate liquidation or positioning data that the tool does not provide. "
            "Append a concise Markdown evidence table."
            + get_language_instruction()
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are collaborating with other trading analysts. {context} The analysis date is {date}. Available tools: {tools}.\n{system}"),
            MessagesPlaceholder(variable_name="messages"),
        ]).partial(context=context, date=state["trade_date"], tools=", ".join(t.name for t in tools), system=system)
        result = (prompt | llm.bind_tools(tools)).invoke(state["messages"])
        return {"messages": [result], "derivatives_report": result.content if not result.tool_calls else ""}
    return node
