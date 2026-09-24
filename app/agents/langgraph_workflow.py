"""
LangGraph Workflow Integration for ClaimShield AI.
Constructs a stateful graph pipeline for multi-agent claim verification,
integrating security sanitization, NLP entity parsing, Scikit-Learn stance classification,
vector retrieval, LLM verification, and audit logging.
"""

from typing import TypedDict, List, Dict, Any, Optional

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


class ClaimVerificationState(TypedDict):
    claim: str
    username: str
    clean_claim: str
    role: str
    entities: List[Dict[str, Any]]
    search_query: str
    ml_classification: Dict[str, Any]
    articles: List[Dict[str, Any]]
    evidence_summary: str
    verdict: str
    confidence: float
    summary: str
    citations: List[str]
    engine: str
    status: str
    error_message: Optional[str]


class LangGraphClaimVerifier:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.graph = None
        if LANGGRAPH_AVAILABLE:
            self._build_graph()

    def _build_graph(self):
        builder = StateGraph(ClaimVerificationState)

        # Define graph node functions
        def sanitize_node(state: ClaimVerificationState) -> Dict[str, Any]:
            res = self.orchestrator.security_agent.handle_message({
                "action": "sanitize",
                "data": {"text": state["claim"]}
            })
            if res.get("status") != "success":
                return {"status": "error", "error_message": res.get("message")}
            return {"clean_claim": res.get("clean_text", state["claim"])}

        def nlp_node(state: ClaimVerificationState) -> Dict[str, Any]:
            res = self.orchestrator.nlp_agent.handle_message({
                "action": "process_claim",
                "data": {"claim": state["clean_claim"]}
            })
            if res.get("status") != "success":
                return {"status": "error", "error_message": res.get("message")}
            return {
                "entities": res.get("entities", []),
                "search_query": res.get("search_query", state["clean_claim"]),
                "ml_classification": res.get("ml_classification", {})
            }

        def retrieval_node(state: ClaimVerificationState) -> Dict[str, Any]:
            is_pro = state.get("role") in ["pro", "premium", "newsroom_admin"]
            limit = 5 if is_pro else 3
            res = self.orchestrator.retrieval_agent.handle_message({
                "action": "retrieve",
                "data": {"query": state["search_query"], "limit": limit}
            })
            if res.get("status") != "success":
                return {"status": "error", "error_message": res.get("message")}
            raw_articles = res.get("articles", [])
            display_articles = raw_articles[:2] if not is_pro else raw_articles[:5]
            return {"articles": display_articles}

        def verify_node(state: ClaimVerificationState) -> Dict[str, Any]:
            res = self.orchestrator.verification_agent.handle_message({
                "action": "verify_claim",
                "data": {
                    "claim": state["clean_claim"],
                    "articles": state.get("articles", []),
                    "evidence_summary": state.get("evidence_summary", "")
                }
            })
            if res.get("status") != "success":
                return {"status": "error", "error_message": res.get("message")}
            return {
                "verdict": res.get("verdict", "Unclear"),
                "confidence": res.get("confidence", 0.0),
                "summary": res.get("summary", ""),
                "citations": res.get("citations", []),
                "engine": f"LangGraph ({res.get('engine', 'LLM')})",
                "status": "success"
            }

        builder.add_node("sanitize", sanitize_node)
        builder.add_node("nlp", nlp_node)
        builder.add_node("retrieve", retrieval_node)
        builder.add_node("verify", verify_node)

        builder.set_entry_point("sanitize")

        def route_after_sanitize(state: ClaimVerificationState) -> str:
            return "nlp" if state.get("status") != "error" else END

        def route_after_nlp(state: ClaimVerificationState) -> str:
            return "retrieve" if state.get("status") != "error" else END

        def route_after_retrieve(state: ClaimVerificationState) -> str:
            return "verify" if state.get("status") != "error" else END

        # If any node reports failure it patches "status" to "error" and the graph
        # short-circuits to END instead of continuing and overwriting the error.
        builder.add_conditional_edges("sanitize", route_after_sanitize, {"nlp": "nlp", END: END})
        builder.add_conditional_edges("nlp", route_after_nlp, {"retrieve": "retrieve", END: END})
        builder.add_conditional_edges("retrieve", route_after_retrieve, {"verify": "verify", END: END})
        builder.add_edge("verify", END)

        self.graph = builder.compile()

    def run(self, claim: str, username: str = "guest", role: str = "user") -> Dict[str, Any]:
        """Executes the verification graph."""
        if not LANGGRAPH_AVAILABLE or self.graph is None:
            # Fallback execution when LangGraph is not directly installed
            return self._fallback_pipeline(claim, username, role)

        initial_state: ClaimVerificationState = {
            "claim": claim,
            "username": username,
            "clean_claim": claim,
            "role": role,
            "entities": [],
            "search_query": claim,
            "ml_classification": {},
            "articles": [],
            "evidence_summary": "",
            "verdict": "Unclear",
            "confidence": 0.0,
            "summary": "",
            "citations": [],
            "engine": "LangGraph Stateful Workflow",
            "status": "pending",
            "error_message": None
        }

        try:
            final_state = self.graph.invoke(initial_state)
            status = final_state.get("status", "success")
            result = {
                "sender": "langgraph_orchestrator",
                "status": status,
                "claim": final_state.get("clean_claim", claim),
                "verdict": final_state.get("verdict", "Unclear"),
                "confidence": final_state.get("confidence", 0.0),
                "summary": final_state.get("summary", ""),
                "entities": final_state.get("entities", []),
                "articles": final_state.get("articles", []),
                "ml_classification": final_state.get("ml_classification", {}),
                "engine": final_state.get("engine", "LangGraph Graph Execution")
            }
            if status == "error":
                result["message"] = final_state.get("error_message") or "A LangGraph node failed during verification."
            return result
        except Exception as e:
            print(f"[LangGraph] Verification graph raised: {e}")
            return self._fallback_pipeline(claim, username, role)

    def _fallback_pipeline(self, claim: str, username: str, role: str) -> Dict[str, Any]:
        """Structured pipeline fallback simulating graph step sequence."""
        return self.orchestrator._verify_flow({"claim": claim, "username": username})
