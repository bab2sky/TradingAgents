from tradingagents.agents.utils.agent_states import AgentState

class ConditionalLogic:
    def __init__(self, max_debate_rounds=1, max_risk_discuss_rounds=1):
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds

    def _continue(self, state, tool_node, clear_node):
        return tool_node if state["messages"][-1].tool_calls else clear_node

    def should_continue_market(self, state): return self._continue(state, "tools_market", "Msg Clear Market")
    def should_continue_sentiment(self, state): return self._continue(state, "tools_sentiment", "Msg Clear Sentiment")
    def should_continue_news(self, state): return self._continue(state, "tools_news", "Msg Clear News")
    def should_continue_onchain(self, state): return self._continue(state, "tools_onchain", "Msg Clear On-chain")
    def should_continue_derivatives(self, state): return self._continue(state, "tools_derivatives", "Msg Clear Derivatives")
    def should_continue_order_flow(self, state): return self._continue(state, "tools_order_flow", "Msg Clear Order Flow")
    def should_continue_macro(self, state): return self._continue(state, "tools_macro", "Msg Clear Macro")

    def should_continue_debate(self, state):
        if state["investment_debate_state"]["count"] >= 2 * self.max_debate_rounds: return "Research Manager"
        return "Bear Researcher" if state["investment_debate_state"]["current_response"].startswith("Bull") else "Bull Researcher"

    def should_continue_risk_analysis(self, state):
        if state["risk_debate_state"]["count"] >= 3 * self.max_risk_discuss_rounds: return "Portfolio Manager"
        speaker = state["risk_debate_state"]["latest_speaker"]
        if speaker.startswith("Aggressive"): return "Conservative Analyst"
        if speaker.startswith("Conservative"): return "Neutral Analyst"
        return "Aggressive Analyst"
