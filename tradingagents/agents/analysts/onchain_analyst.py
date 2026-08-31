from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.crypto_data_tools import get_onchain_metrics
from tradingagents.agents.utils.agent_utils import get_instrument_context_from_state, get_language_instruction


def create_onchain_analyst(llm):
    def node(state):
        context = get_instrument_context_from_state(state)
        tools = [get_onchain_metrics]
        system = (
            "You are the On-chain Analyst for a crypto trading research team. "
            "Analyze blockchain-native activity relevant to the exact asset. "
            "Use only evidence returned by tools; never invent wallet flows, whale activity, exchange flows, or network statistics. "
            "Clearly distinguish unavailable metrics from negative evidence. "
            "Discuss implications, uncertainty, and whether on-chain evidence supports or contradicts the broader market view. "
            "Append a concise Markdown evidence table."
            + get_language_instruction()
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are collaborating with other trading analysts. {context} The analysis date is {date}. Available tools: {tools}.\n{system}"),
            MessagesPlaceholder(variable_name="messages"),
        ]).partial(context=context, date=state["trade_date"], tools=", ".join(t.name for t in tools), system=system)
        result = (prompt | llm.bind_tools(tools)).invoke(state["messages"])
        return {"messages": [result], "onchain_report": result.content if not result.tool_calls else ""}
    return node
