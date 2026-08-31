from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import get_instrument_context_from_state, get_language_instruction, get_macro_indicators


def create_macro_analyst(llm):
    def node(state):
        context = get_instrument_context_from_state(state)
        tools = [get_macro_indicators]
        system = (
            "You are the Macro Analyst for a crypto trading research team. "
            "Analyze rates, liquidity, inflation, employment, Treasury yields and other macro variables that can affect crypto risk appetite. "
            "Use FRED tool results for exact values and dates. Distinguish observation from interpretation and avoid claiming causality without evidence. "
            "Focus on the current macro regime and implications for the exact crypto asset. Append a concise Markdown evidence table."
            + get_language_instruction()
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are collaborating with other trading analysts. {context} The analysis date is {date}. Available tools: {tools}.\n{system}"),
            MessagesPlaceholder(variable_name="messages"),
        ]).partial(context=context, date=state["trade_date"], tools=", ".join(t.name for t in tools), system=system)
        result = (prompt | llm.bind_tools(tools)).invoke(state["messages"])
        return {"messages": [result], "macro_report": result.content if not result.tool_calls else ""}
    return node
