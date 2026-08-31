from collections.abc import Iterable
from dataclasses import dataclass
from time import monotonic

@dataclass(frozen=True)
class AnalystNodeSpec:
    key: str
    agent_node: str
    clear_node: str
    tool_node: str
    report_key: str

@dataclass(frozen=True)
class AnalystExecutionPlan:
    specs: list[AnalystNodeSpec]

ANALYST_NODE_SPECS = {
    "market": AnalystNodeSpec("market", "Market Analyst", "Msg Clear Market", "tools_market", "market_report"),
    "sentiment": AnalystNodeSpec("sentiment", "Sentiment Analyst", "Msg Clear Sentiment", "tools_sentiment", "sentiment_report"),
    "news": AnalystNodeSpec("news", "News Analyst", "Msg Clear News", "tools_news", "news_report"),
    "onchain": AnalystNodeSpec("onchain", "On-chain Analyst", "Msg Clear On-chain", "tools_onchain", "onchain_report"),
    "derivatives": AnalystNodeSpec("derivatives", "Derivatives Analyst", "Msg Clear Derivatives", "tools_derivatives", "derivatives_report"),
    "order_flow": AnalystNodeSpec("order_flow", "Order Flow Analyst", "Msg Clear Order Flow", "tools_order_flow", "order_flow_report"),
    "macro": AnalystNodeSpec("macro", "Macro Analyst", "Msg Clear Macro", "tools_macro", "macro_report"),
}
CRYPTO_DEFAULTS = ("market", "sentiment", "news", "onchain", "derivatives", "order_flow", "macro")

def build_analyst_execution_plan(selected_analysts: Iterable[str]) -> AnalystExecutionPlan:
    requested = list(selected_analysts)
    if "fundamentals" in requested:
        requested = list(CRYPTO_DEFAULTS)
    requested = ["sentiment" if key == "social" else key for key in requested]
    specs, seen = [], set()
    for key in requested:
        if key in seen: continue
        spec = ANALYST_NODE_SPECS.get(key)
        if spec is None: raise ValueError(f"unknown crypto analyst key: {key}")
        specs.append(spec); seen.add(key)
    if not specs: raise ValueError("at least one analyst must be selected")
    return AnalystExecutionPlan(specs)

def get_initial_analyst_node(plan): return plan.specs[0].agent_node

class AnalystWallTimeTracker:
    def __init__(self, plan): self.plan, self._started_at, self._wall_times = plan, {}, {}
    def mark_started(self, analyst_key, started_at=None): self._started_at.setdefault(analyst_key, monotonic() if started_at is None else started_at)
    def mark_completed(self, analyst_key, completed_at=None):
        if analyst_key in self._wall_times: return
        started = self._started_at.get(analyst_key)
        if started is not None: self._wall_times[analyst_key] = max(0.0, (monotonic() if completed_at is None else completed_at) - started)
    def get_wall_times(self): return dict(self._wall_times)
    def format_summary(self):
        parts = [f"{s.agent_node.removesuffix(' Analyst')} {self._wall_times[s.key]:.2f}s" for s in self.plan.specs if s.key in self._wall_times]
        return "Analyst wall time: " + " | ".join(parts) if parts else "Analyst wall time: pending"

def sync_analyst_tracker_from_chunk(tracker, chunk, now=None):
    current = monotonic() if now is None else now
    for spec in tracker.plan.specs:
        if chunk.get(spec.report_key): tracker.mark_started(spec.key, current); tracker.mark_completed(spec.key, current)
