from tradingagents.agents.utils.agent_utils import get_instrument_context_from_state, get_language_instruction, opponent_argument_or_opening

def create_bull_researcher(llm):
    def bull_node(state) -> dict:
        d=state["investment_debate_state"]; history=d.get("history",""); current=opponent_argument_or_opening(d.get("current_response",""),"bear analyst")
        reports="\n".join([f"Market: {state.get('market_report','')}",f"Sentiment: {state.get('sentiment_report','')}",f"News: {state.get('news_report','')}",f"On-chain: {state.get('onchain_report','')}",f"Derivatives: {state.get('derivatives_report','')}",f"Order flow: {state.get('order_flow_report','')}",f"Macro: {state.get('macro_report','')}"])
        prompt=f"""You are the Bull Analyst in a crypto investment debate. Build an evidence-based bullish case for the exact crypto asset, using market, sentiment, news, on-chain, derivatives, order-flow and macro evidence. Do not invent missing data. Explicitly counter the bear argument and distinguish facts from assumptions.

{get_instrument_context_from_state(state)}

RESEARCH REPORTS:
{reports}

DEBATE HISTORY:
{history}

LAST BEAR ARGUMENT:
{current}
"""+get_language_instruction()
        response=llm.invoke(prompt); argument=f"Bull Analyst: {response.content}"
        return {"investment_debate_state":{"history":history+"\n"+argument,"bull_history":d.get("bull_history","")+"\n"+argument,"bear_history":d.get("bear_history",""),"current_response":argument,"count":d["count"]+1}}
    return bull_node
