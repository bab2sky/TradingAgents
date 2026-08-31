from typing import Any
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from tradingagents.agents import create_bear_researcher, create_bull_researcher, create_msg_delete, create_market_analyst, create_news_analyst, create_research_manager, create_sentiment_analyst, create_trader, create_portfolio_manager, create_aggressive_debator, create_neutral_debator, create_conservative_debator
from tradingagents.agents.analysts.onchain_analyst import create_onchain_analyst
from tradingagents.agents.analysts.derivatives_analyst import create_derivatives_analyst
from tradingagents.agents.analysts.order_flow_analyst import create_order_flow_analyst
from tradingagents.agents.analysts.macro_analyst import create_macro_analyst
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.crypto_data_tools import get_crypto_market_data, get_crypto_indicators, get_onchain_metrics, get_derivatives_metrics, get_order_flow
from tradingagents.agents.utils.agent_utils import get_news, get_macro_indicators
from .analyst_execution import build_analyst_execution_plan
from .conditional_logic import ConditionalLogic

DEBATE_PATH_MAP = {"Bull Researcher": "Bull Researcher", "Bear Researcher": "Bear Researcher", "Research Manager": "Research Manager"}
RISK_ANALYSIS_PATH_MAP = {"Aggressive Analyst": "Aggressive Analyst", "Conservative Analyst": "Conservative Analyst", "Neutral Analyst": "Neutral Analyst", "Portfolio Manager": "Portfolio Manager"}

class GraphSetup:
    def __init__(self, quick_thinking_llm: Any, deep_thinking_llm: Any, tool_nodes: dict[str, ToolNode], conditional_logic: ConditionalLogic): self.quick_thinking_llm, self.deep_thinking_llm, self.tool_nodes, self.conditional_logic = quick_thinking_llm, deep_thinking_llm, tool_nodes, conditional_logic
    def setup_graph(self, selected_analysts=("market", "sentiment", "news", "onchain", "derivatives", "order_flow", "macro")):
        plan = build_analyst_execution_plan(selected_analysts)
        factories = {"market":lambda:create_market_analyst(self.quick_thinking_llm),"sentiment":lambda:create_sentiment_analyst(self.quick_thinking_llm),"news":lambda:create_news_analyst(self.quick_thinking_llm),"onchain":lambda:create_onchain_analyst(self.quick_thinking_llm),"derivatives":lambda:create_derivatives_analyst(self.quick_thinking_llm),"order_flow":lambda:create_order_flow_analyst(self.quick_thinking_llm),"macro":lambda:create_macro_analyst(self.quick_thinking_llm)}
        tools = {"market":ToolNode([get_crypto_market_data,get_crypto_indicators]),"sentiment":ToolNode([get_news]),"news":ToolNode([get_news,get_macro_indicators]),"onchain":ToolNode([get_onchain_metrics]),"derivatives":ToolNode([get_derivatives_metrics]),"order_flow":ToolNode([get_order_flow]),"macro":ToolNode([get_macro_indicators])}
        workflow=StateGraph(AgentState)
        for spec in plan.specs:
            workflow.add_node(spec.agent_node,factories[spec.key]()); workflow.add_node(spec.clear_node,create_msg_delete()); workflow.add_node(spec.tool_node,tools[spec.key])
        for name,factory in {"Bull Researcher":create_bull_researcher,"Bear Researcher":create_bear_researcher,"Research Manager":create_research_manager,"Trader":create_trader,"Aggressive Analyst":create_aggressive_debator,"Neutral Analyst":create_neutral_debator,"Conservative Analyst":create_conservative_debator,"Portfolio Manager":create_portfolio_manager}.items(): workflow.add_node(name,factory(self.deep_thinking_llm) if name in {"Research Manager","Portfolio Manager"} else factory(self.quick_thinking_llm))
        workflow.add_edge(START,plan.specs[0].agent_node)
        for i,spec in enumerate(plan.specs):
            workflow.add_conditional_edges(spec.agent_node,getattr(self.conditional_logic,f"should_continue_{spec.key}"),[spec.tool_node,spec.clear_node]); workflow.add_edge(spec.tool_node,spec.agent_node); workflow.add_edge(spec.clear_node,plan.specs[i+1].agent_node if i+1<len(plan.specs) else "Bull Researcher")
        for node in ("Bull Researcher","Bear Researcher"): workflow.add_conditional_edges(node,self.conditional_logic.should_continue_debate,DEBATE_PATH_MAP)
        workflow.add_edge("Research Manager","Trader"); workflow.add_edge("Trader","Aggressive Analyst")
        for node in ("Aggressive Analyst","Conservative Analyst","Neutral Analyst"): workflow.add_conditional_edges(node,self.conditional_logic.should_continue_risk_analysis,RISK_ANALYSIS_PATH_MAP)
        workflow.add_edge("Portfolio Manager",END)
        return workflow
