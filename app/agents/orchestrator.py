import json
import app.config as config
from app.agents.base_agent import BaseAgent
from app.agents.security_agent import SecurityAgent
from app.agents.nlp_agent import NLPAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.verification_agent import VerificationAgent
from app.agents.langgraph_workflow import LangGraphClaimVerifier
from app.agents.autogen_bridge import AutoGenClaimBridge
from app.recommendations import ClaimRecommender

class Orchestrator(BaseAgent):
    """
    Orchestrator Agent. The master controller of the multi-agent system.
    Guides claims through sanitization, rate-limit validation, NLP analysis, 
    FAISS retrieval, LLM verification, and database auditing. Supports execution via
    Standard A2A, LangGraph StateGraph, or AutoGen Multi-Agent Debate.
    """
    def __init__(self, 
                 security_agent: SecurityAgent = None,
                 nlp_agent: NLPAgent = None,
                 retrieval_agent: RetrievalAgent = None,
                 verification_agent: VerificationAgent = None):
        super().__init__("orchestrator")
        
        # Share or initialize subagents
        self.security_agent = security_agent or SecurityAgent()
        self.nlp_agent = nlp_agent or NLPAgent()
        self.retrieval_agent = retrieval_agent or RetrievalAgent(db=self.security_agent.db)
        self.verification_agent = verification_agent or VerificationAgent()
        
        # Framework Bridges
        self.langgraph_verifier = LangGraphClaimVerifier(self)
        self.autogen_bridge = AutoGenClaimBridge(self)
        self.recommender = ClaimRecommender(
            db=self.security_agent.db,
            vector_store=self.retrieval_agent.vector_store
        )

    def handle_message(self, message: dict) -> dict:
        action = message.get("action")
        data = message.get("data", {})
        
        if action == "verify":
            mode = data.get("engine_mode", "Standard A2A Protocol")
            if mode == "LangGraph Stateful Workflow":
                # The same security gates that govern the standard flow apply
                # here: sanitize, token-bucket rate limit (deducts a token),
                # audit logging, and recommendations.
                ctx, err = self._security_precheck(data)
                if err:
                    return err
                result = self.langgraph_verifier.run(
                    claim=ctx["clean_claim"],
                    user_ctx=ctx
                )
                return self._complete_verification(ctx, result)
            elif mode == "AutoGen Agent Debate":
                res = self._verify_flow(data)
                debate = self.autogen_bridge.run_debate(data.get("claim", ""), res.get("articles", []))
                res["autogen_debate"] = debate
                res["engine"] = f"{res.get('engine')} + AutoGen Debate Bridge"
                return res
            else:
                return self._verify_flow(data)
        else:
            return {
                "sender": self.name,
                "status": "error",
                "message": f"Unknown action: {action}"
            }

    def _security_precheck(self, data: dict) -> tuple:
        """Steps 1-2: sanitization + rate-limit validation.

        Returns (ctx, None) on success or (None, error_result) otherwise. The
        context carries the resolved username, role, remaining tokens, and both
        the raw and cleaned claim so downstream engines can stay in parity with
        the standard flow without re-checking or double-charging.
        """
        claim_input = data.get("claim", "")
        username = data.get("username", "")

        if not claim_input:
            return None, {
                "sender": self.name,
                "status": "error",
                "message": "A claim must be provided for verification."
            }

        # Step 1: Sanitize input (Security Agent)
        san_resp = self.send_message(
            recipient=self.security_agent,
            action="sanitize",
            data={"text": claim_input}
        )

        if san_resp.get("status") != "success":
            return None, {
                "sender": self.name,
                "status": "error",
                "message": f"Sanitization phase failed: {san_resp.get('message')}"
            }

        clean_claim = san_resp.get("clean_text", claim_input)

        # Step 2: Check Rate Limit (Security Agent)
        if not username:
            username = "guest"

        rate_resp = self.send_message(
            recipient=self.security_agent,
            action="check_rate_limit",
            data={"username": username}
        )

        if rate_resp.get("status") != "success":
            return None, {
                "sender": self.name,
                "status": "error",
                "message": f"Rate limit verification failed: {rate_resp.get('message')}"
            }

        if not rate_resp.get("allowed", False):
            retry_after = rate_resp.get("retry_after_seconds", 60)
            return None, {
                "sender": self.name,
                "status": "rate_limited",
                "message": f"Too many requests! Rate limit exceeded for {username}.",
                "retry_after_seconds": retry_after
            }

        user_role = rate_resp.get("role", "user")
        ctx = {
            "claim_input": claim_input,
            "clean_claim": clean_claim,
            "username": username,
            "role": user_role,
            "tokens_remaining": rate_resp.get("tokens", 0.0),
            "is_pro": user_role in ["pro", "premium", "newsroom_admin"]
        }
        return ctx, None

    def _verify_flow(self, data: dict) -> dict:
        ctx, err = self._security_precheck(data)
        if err:
            return err
        return self._complete_verification(ctx)

    def _complete_verification(self, ctx: dict, result: dict = None) -> dict:
        """Finalizes a verification result: audit logging + recommendations.

        Used by both the standard sequential flow and the LangGraph graph so the
        two engines share token accounting (already spent in precheck), audit
        persistence, and the related-claims panel.
        """
        result = result if result is not None else self._verify_flow_with_ctx(ctx)
        if result.get("status") == "success":
            self._log_verification_audit(ctx, result)
            result["recommendations"] = self._recommendations(result, ctx)
        return result

    def _log_verification_audit(self, ctx: dict, result: dict) -> None:
        """Persists an encrypted audit entry for a completed verification."""
        articles = result.get("all_articles") or result.get("articles", [])
        audit_details = {
            "clean_claim": result.get("claim") or ctx["clean_claim"],
            "entities": result.get("entities", []),
            "search_query": result.get("search_query") or ctx["clean_claim"],
            "articles_retrieved": [
                {
                    "id": a.get("id"),
                    "title": a.get("title"),
                    "source": a.get("source"),
                    "score": a.get("score", 0.0)
                } for a in articles
            ],
            "citations": result.get("citations", []),
            "engine": result.get("engine", ""),
            "summary": result.get("summary", ""),
            "straight_answer": result.get("straight_answer", ""),
            "tokens_remaining": ctx["tokens_remaining"]
        }
        self.send_message(
            recipient=self.security_agent,
            action="log_audit",
            data={
                "user_id": ctx["username"],
                "claim": ctx["claim_input"],
                "verdict": result.get("verdict", "Unclear"),
                "confidence": result.get("confidence", 0.0),
                "details": audit_details
            }
        )

    def _recommendations(self, result: dict, ctx: dict) -> list:
        try:
            return self.recommender.recommend(
                result.get("claim") or ctx["clean_claim"],
                ctx["username"]
            )
        except Exception as e:
            print(f"[Orchestrator] Recommendation generation failed: {e}")
            return []

    def _verify_flow_with_ctx(self, ctx: dict) -> dict:
        """Steps 3-7 with an already-resolved security context.

        Assumes sanitization + rate limiting were performed (no token is
        re-charged here). Mirrors the sequential steps the LangGraph fallback
        uses when the graph itself raises.
        """
        clean_claim = ctx["clean_claim"]
        user_role = ctx["role"]
        is_pro = ctx["is_pro"]
        remaining_tokens = ctx["tokens_remaining"]

        # Step 3: Parse Claim & NER (NLP Agent)
        nlp_resp = self.send_message(
            recipient=self.nlp_agent,
            action="process_claim",
            data={"claim": clean_claim}
        )

        if nlp_resp.get("status") != "success":
            return {
                "sender": self.name,
                "status": "error",
                "message": f"NLP parsing phase failed: {nlp_resp.get('message')}"
            }

        entities = nlp_resp.get("entities", [])
        search_query = nlp_resp.get("search_query", clean_claim)
        ml_classification = nlp_resp.get("ml_classification", {})

        # Step 4: Retrieve Supporting Documents (Retrieval Agent)
        # Pro users retrieve up to 5 resources; Free users retrieve at least 3 internally for verification
        limit = config.PRO_PLAN_MAX_RESOURCES if is_pro else max(config.PRO_PLAN_MIN_RESOURCES, 3)
        ret_resp = self.send_message(
            recipient=self.retrieval_agent,
            action="retrieve",
            data={"query": search_query, "limit": limit}
        )

        if ret_resp.get("status") != "success":
            return {
                "sender": self.name,
                "status": "error",
                "message": f"Fact retrieval phase failed: {ret_resp.get('message')}"
            }

        articles = ret_resp.get("articles", [])

        # Step 4.5: Summarize retrieved evidence (NLP Agent — Extractive Summarization)
        # Only summarize if top article vector score demonstrates actual relevance (>= 0.30)
        evidence_summary = ""
        top_score = articles[0].get("score", 0.0) if articles else 0.0
        if articles and top_score >= 0.30:
            combined_text = " ".join(
                f"{a['title']}. {a['content']}" for a in articles
            )
            sum_resp = self.send_message(
                recipient=self.nlp_agent,
                action="summarize",
                data={"text": combined_text, "max_sentences": 3}
            )
            if sum_resp.get("status") == "success":
                evidence_summary = sum_resp.get("summary", "")

        # Step 5: Fact verification (Verification Agent - LLM)
        ver_resp = self.send_message(
            recipient=self.verification_agent,
            action="verify_claim",
            data={"claim": clean_claim, "articles": articles, "evidence_summary": evidence_summary}
        )

        if ver_resp.get("status") != "success":
            return {
                "sender": self.name,
                "status": "error",
                "message": f"Fact verification phase failed: {ver_resp.get('message')}"
            }

        verdict = ver_resp.get("verdict", "Unclear")
        confidence = ver_resp.get("confidence", 0.0)
        straight_answer = ver_resp.get("straight_answer", "")
        summary = ver_resp.get("summary", "")
        citations = ver_resp.get("citations", [])
        engine = ver_resp.get("engine", "Local Heuristic Mock")

        # Suppress evidence_summary for general QA answers if irrelevant
        if verdict in ["Answered", "General Info"]:
            evidence_summary = ""

        # Filter reference articles so general QA queries don't display unrelated articles
        display_articles = articles
        if verdict in ["Answered", "General Info"] or (articles and articles[0].get("score", 0.0) < 0.30):
            display_articles = []
        elif not is_pro:
            # Free tier strictly displays only 2 resources
            display_articles = articles[:config.FREE_PLAN_DISPLAY_RESOURCES]
        else:
            # Pro tier displays at least 3 (if available) and up to 5 maximum resources
            display_articles = articles[:config.PRO_PLAN_MAX_RESOURCES]

        # Step 7: Compile and Return final response payload
        return {
            "sender": self.name,
            "status": "success",
            "claim": clean_claim,
            "verdict": verdict,
            "confidence": confidence,
            "straight_answer": straight_answer,
            "summary": summary,
            "evidence_summary": evidence_summary,
            "citations": citations,
            "entities": entities,
            "search_query": search_query,
            "articles": display_articles,
            "all_articles": articles,
            "total_resources_found": len(articles),
            "is_pro_plan": is_pro,
            "ml_classification": ml_classification,
            "engine": engine,
            "tokens_remaining": remaining_tokens
        }
