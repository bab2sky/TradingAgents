from tradingagents.agents.utils.agent_utils import get_instrument_context_from_state, get_language_instruction, opponent_argument_or_opening

def create_bear_researcher(llm):
    def bear_node(state) -> dict:
        d=state["investment_debate_state"]; history=d.get("history",""); current=opponent_argument_or_opening(d.get("current_response",""),"bull analyst")
        reports="\n".join([f"Market: {state.get('market_report','')}",f"Sentiment: {state.get('sentiment_report','')}",f"News: {state.get('news_report','')}",f"On-chain: {state.get('onchain_report','')}",f"Derivatives: {state.get('derivatives_report','')}",f"Order flow: {state.get('order_flow_report','')}",f"Macro: {state.get('macro_report','')}"])
        prompt=f"""You are the Bear Analyst in a crypto investment debate. Build an evidence-based bearish/risk case for the exact crypto asset, using market, sentiment, news, on-chain, derivatives, order-flow and macro evidence. Do not invent missing data. Identify leverage, liquidity, regime and narrative risks, and directly challenge the bull argument.

{get_instrument_context_from_state(state)}

RESEARCH REPORTS:
{reports}

DEBATE HISTORY:
{history}

LAST BULL ARGUMENT:
{current}
"""+get_language_instruction()
        response=llm.invoke(prompt); argument=f"Bear Analyst: {response.content}"
        return {"investment_debate_state":{"history":history+"\n"+argument,"bear_history":d.get("bear_history","")+"\n"+argument,"bull_history":d.get("bull_history",""),"current_response":argument,"count":d["count"]+1}}
    return bear_node
