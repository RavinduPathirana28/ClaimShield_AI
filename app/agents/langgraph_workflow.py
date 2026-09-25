"""
LangGraph Workflow Integration for ClaimShield AI.
Constructs a stateful graph pipeline for multi-agent claim verification,
integrating security sanitization, NLP entity parsing, Scikit-Learn stance classification,
vector retrieval, extractive summarization, LLM verification, and audit logging.

The graph is driven through the orchestrator's A2A send_message transport so
inter-agent activity is traced in the A2A Protocol Monitor exactly like the
standard sequential flow, and the result payload mirrors the standard engine's
keys (is_pro_plan, total_resources_found, straight_answer, tokens_remaining, ...).

Rate limiting is NOT enforced here: the orchestrator resolves it (and spends a
token) before entering the graph. This module only receives the resolved role,
remaining tokens, and clean claim via a user context dict.
"""

from typing import TypedDict, List, Dict, Any, Optional

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from app import config

PRO_ROLES = {"pro", "premium", "newsroom_admin"}


class ClaimVerificationState(TypedDict):
    claim: str
    username: str
    clean_claim: str
    role: str
    tokens_remaining: float
    entities: List[Dict[str, Any]]
    search_query: str
    ml_classification: Dict[str, Any]
    articles: List[Dict[str, Any]]
    total_resources_found: int
    evidence_summary: str
    verdict: str
    confidence: float
    straight_answer: str
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

        # Define graph node functions. Every node routes through the
        # orchestrator's send_message so the A2A/1.0 trace captures it.
        def sanitize_node(state: ClaimVerificationState) -> Dict[str, Any]:
            res = self.orchestrator.send_message(
                recipient=self.orchestrator.security_agent,
                action="sanitize",
                data={"text": state["claim"]}
            )
            if res.get("status") != "success":
                return {"status": "error", "error_message": res.get("message")}
            return {"clean_claim": res.get("clean_text", state["claim"])}

        def nlp_node(state: ClaimVerificationState) -> Dict[str, Any]:
            res = self.orchestrator.send_message(
                recipient=self.orchestrator.nlp_agent,
                action="process_claim",
                data={"claim": state["clean_claim"]}
            )
            if res.get("status") != "success":
                return {"status": "error", "error_message": res.get("message")}
            return {
                "entities": res.get("entities", []),
                "search_query": res.get("search_query", state["clean_claim"]),
                "ml_classification": res.get("ml_classification", {})
            }

        def retrieval_node(state: ClaimVerificationState) -> Dict[str, Any]:
            is_pro = state.get("role") in PRO_ROLES
            limit = config.PRO_PLAN_MAX_RESOURCES if is_pro else max(config.PRO_PLAN_MIN_RESOURCES, 3)
            res = self.orchestrator.send_message(
                recipient=self.orchestrator.retrieval_agent,
                action="retrieve",
                data={"query": state["search_query"], "limit": limit}
            )
            if res.get("status") != "success":
                return {"status": "error", "error_message": res.get("message")}
            articles = res.get("articles", [])
            return {
                "articles": articles,
                "total_resources_found": len(articles)
            }

        def summarize_node(state: ClaimVerificationState) -> Dict[str, Any]:
            articles = state.get("articles", [])
            evidence_summary = ""
            top_score = articles[0].get("score", 0.0) if articles else 0.0
            if articles and top_score >= 0.30:
                combined_text = " ".join(
                    f"{a['title']}. {a['content']}" for a in articles
                )
                res = self.orchestrator.send_message(
                    recipient=self.orchestrator.nlp_agent,
                    action="summarize",
                    data={"text": combined_text, "max_sentences": 3}
                )
                if res.get("status") == "success":
                    evidence_summary = res.get("summary", "")
            return {"evidence_summary": evidence_summary}

        def verify_node(state: ClaimVerificationState) -> Dict[str, Any]:
            res = self.orchestrator.send_message(
                recipient=self.orchestrator.verification_agent,
                action="verify_claim",
                data={
                    "claim": state["clean_claim"],
                    "articles": state.get("articles", []),
                    "evidence_summary": state.get("evidence_summary", "")
                }
            )
            if res.get("status") != "success":
                return {"status": "error", "error_message": res.get("message")}
            return {
                "verdict": res.get("verdict", "Unclear"),
                "confidence": res.get("confidence", 0.0),
                "straight_answer": res.get("straight_answer", ""),
                "summary": res.get("summary", ""),
                "citations": res.get("citations", []),
                "engine": f"LangGraph ({res.get('engine', 'LLM')})",
                "status": "success"
            }

        builder.add_node("sanitize", sanitize_node)
        builder.add_node("nlp", nlp_node)
        builder.add_node("retrieve", retrieval_node)
        builder.add_node("summarize", summarize_node)
        builder.add_node("verify", verify_node)

        builder.set_entry_point("sanitize")

        def route(state: ClaimVerificationState) -> str:
            return "nlp" if state.get("status") != "error" else END

        def route_nlp(state: ClaimVerificationState) -> str:
            return "retrieve" if state.get("status") != "error" else END

        def route_retrieve(state: ClaimVerificationState) -> str:
            return "summarize" if state.get("status") != "error" else END

        def route_summarize(state: ClaimVerificationState) -> str:
            return "verify" if state.get("status") != "error" else END

        # If any node reports failure it patches "status" to "error" and the graph
        # short-circuits to END instead of continuing and overwriting the error.
        builder.add_conditional_edges("sanitize", route, {"nlp": "nlp", END: END})
        builder.add_conditional_edges("nlp", route_nlp, {"retrieve": "retrieve", END: END})
        builder.add_conditional_edges("retrieve", route_retrieve, {"summarize": "summarize", END: END})
        builder.add_conditional_edges("summarize", route_summarize, {"verify": "verify", END: END})
        builder.add_edge("verify", END)

        self.graph = builder.compile()

    def run(self, claim: str, user_ctx: dict = None, username: str = "guest",
            role: str = "user", tokens_remaining: float = 0.0) -> Dict[str, Any]:
        """Executes the verification graph.

        The orchestrator normally passes a resolved `user_ctx` (sanitized claim,
        role, remaining tokens, raw claim) so the graph is never responsible for
        rate limiting and no token is double-charged. The keyword-only username/
        role/tokens_remaining params exist for direct standalone calls.
        """
        if user_ctx is None:
            user_ctx = {
                "claim_input": claim,
                "clean_claim": claim,
                "username": username,
                "role": role,
                "tokens_remaining": tokens_remaining,
                "is_pro": role in PRO_ROLES
            }

        if not LANGGRAPH_AVAILABLE or self.graph is None:
            # Fallback execution when LangGraph is not directly installed
            return self._fallback_pipeline(user_ctx)

        initial_state: ClaimVerificationState = {
            "claim": user_ctx.get("clean_claim", claim),
            "username": user_ctx.get("username", "guest"),
            "clean_claim": user_ctx.get("clean_claim", claim),
            "role": user_ctx.get("role", "user"),
            "tokens_remaining": user_ctx.get("tokens_remaining", 0.0),
            "entities": [],
            "search_query": user_ctx.get("clean_claim", claim),
            "ml_classification": {},
            "articles": [],
            "total_resources_found": 0,
            "evidence_summary": "",
            "verdict": "Unclear",
            "confidence": 0.0,
            "straight_answer": "",
            "summary": "",
            "citations": [],
            "engine": "LangGraph Stateful Workflow",
            "status": "pending",
            "error_message": None
        }

        try:
            final_state = self.graph.invoke(initial_state)
            status = final_state.get("status", "success")

            # Display filtering must match the standard flow so free/pro tier
            # resource visibility (and QA suppression) stays identical across engines.
            articles = final_state.get("articles", [])
            verdict = final_state.get("verdict", "Unclear")
            is_pro = final_state.get("role") in PRO_ROLES
            display_articles = articles
            if verdict in ["Answered", "General Info"] or (articles and articles[0].get("score", 0.0) < 0.30):
                display_articles = []
            elif not is_pro:
                display_articles = articles[:config.FREE_PLAN_DISPLAY_RESOURCES]
            else:
                display_articles = articles[:config.PRO_PLAN_MAX_RESOURCES]

            result = {
                "sender": "langgraph_orchestrator",
                "status": status,
                "claim": final_state.get("clean_claim", claim),
                "verdict": verdict,
                "confidence": final_state.get("confidence", 0.0),
                "straight_answer": final_state.get("straight_answer", ""),
                "summary": final_state.get("summary", ""),
                "evidence_summary": final_state.get("evidence_summary", ""),
                "citations": final_state.get("citations", []),
                "entities": final_state.get("entities", []),
                "search_query": final_state.get("search_query", claim),
                "articles": display_articles,
                "all_articles": articles,
                "total_resources_found": final_state.get("total_resources_found", len(articles)),
                "is_pro_plan": is_pro,
                "ml_classification": final_state.get("ml_classification", {}),
                "engine": final_state.get("engine", "LangGraph Graph Execution"),
                "tokens_remaining": final_state.get("tokens_remaining", user_ctx.get("tokens_remaining", 0.0))
            }
            if status == "error":
                result["message"] = final_state.get("error_message") or "A LangGraph node failed during verification."
            return result
        except Exception as e:
            print(f"[LangGraph] Verification graph raised: {e}")
            return self._fallback_pipeline(user_ctx)

    def _fallback_pipeline(self, user_ctx: dict) -> Dict[str, Any]:
        """Structured pipeline fallback simulating graph step sequence.

        Reuses the orchestrator's already-resolved security context so the token
        already spent in the precheck is not deducted a second time. The
        orchestrator's _complete_verification attaches audit + recommendations.
        """
        return self.orchestrator._verify_flow_with_ctx(user_ctx)