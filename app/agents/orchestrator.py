import json
from app.agents.base_agent import BaseAgent
from app.agents.security_agent import SecurityAgent
from app.agents.nlp_agent import NLPAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.verification_agent import VerificationAgent
from app.agents.langgraph_workflow import LangGraphClaimVerifier
from app.agents.autogen_bridge import AutoGenClaimBridge

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

    def handle_message(self, message: dict) -> dict:
        action = message.get("action")
        data = message.get("data", {})
        
        if action == "verify":
            mode = data.get("engine_mode", "Standard A2A Protocol")
            if mode == "LangGraph Stateful Workflow":
                return self.langgraph_verifier.run(
                    claim=data.get("claim", ""),
                    username=data.get("username", "guest")
                )
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

    def _verify_flow(self, data: dict) -> dict:
        claim_input = data.get("claim", "")
        username = data.get("username", "")

        if not claim_input:
            return {
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
            return {
                "sender": self.name,
                "status": "error",
                "message": f"Sanitization phase failed: {san_resp.get('message')}"
            }
        
        clean_claim = san_resp.get("clean_text", claim_input)

        # Step 2: Check Rate Limit (Security Agent)
        # Guest users are blocked or assigned a temporary limit (handled by security agent)
        if not username:
            username = "guest"
            
        rate_resp = self.send_message(
            recipient=self.security_agent,
            action="check_rate_limit",
            data={"username": username}
        )

        if rate_resp.get("status") != "success":
            return {
                "sender": self.name,
                "status": "error",
                "message": f"Rate limit verification failed: {rate_resp.get('message')}"
            }

        if not rate_resp.get("allowed", False):
            retry_after = rate_resp.get("retry_after_seconds", 60)
            return {
                "sender": self.name,
                "status": "rate_limited",
                "message": f"Too many requests! Rate limit exceeded for {username}.",
                "retry_after_seconds": retry_after
            }

        user_role = rate_resp.get("role", "user")
        remaining_tokens = rate_resp.get("tokens", 0.0)

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

        # Step 4: Retrieve Supporting Documents (Retrieval Agent)
        # Premium/newsroom admins get slightly more documents (e.g. 5 vs 3)
        limit = 5 if user_role in ["premium", "newsroom_admin"] else 3
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

        # Step 6: Log Audit (Security Agent)
        audit_details = {
            "clean_claim": clean_claim,
            "entities": entities,
            "search_query": search_query,
            "articles_retrieved": [
                {
                    "id": a["id"],
                    "title": a["title"],
                    "source": a["source"],
                    "score": a.get("score", 0.0)
                } for a in articles
            ],
            "citations": citations,
            "engine": engine,
            "tokens_remaining": remaining_tokens
        }
        
        self.send_message(
            recipient=self.security_agent,
            action="log_audit",
            data={
                "user_id": username,
                "claim": claim_input,
                "verdict": verdict,
                "confidence": confidence,
                "details": audit_details
            }
        )

        # Filter reference articles so general QA queries don't display unrelated articles
        display_articles = articles
        if verdict in ["Answered", "General Info"] or (articles and articles[0].get("score", 0.0) < 0.30):
            display_articles = []

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
            "articles": display_articles,
            "engine": engine,
            "tokens_remaining": remaining_tokens
        }
