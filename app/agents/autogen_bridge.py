"""
Multi-Agent Debate Bridge for ClaimShield AI.

Runs a cross-examination debate (FactChecker -> Critic -> Consensus) grounded in the
real, independent responses of every configured LLM provider. The verification agent
collects those per-model analyses during its consensus pass; the bridge reuses them so
no extra API latency is added. When no LLM was available, the bridge reports the
offline heuristic assessment with an honest label.
"""

from typing import Dict, Any, List


class AutoGenClaimBridge:
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator

    @staticmethod
    def _claims_match(a: str, b: str) -> bool:
        a = (a or "").lower().strip()
        b = (b or "").lower().strip()
        return a == b or a in b or b in a

    def run_debate(self, claim: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compiles a multi-agent debate transcript from the most recent consensus run.
        Reuses the verification agent's per-model results (no repeated LLM calls).
        """
        va = getattr(self.orchestrator, "verification_agent", None)
        last = getattr(va, "last_result", None) if va else None

        result = {}
        if last and self._claims_match(last.get("claim", ""), claim):
            result = dict(last)

        # Fresh consensus results are missing -> run a bounded verification pass.
        if not result:
            if va is not None:
                try:
                    result = va.handle_message({
                        "action": "verify_claim",
                        "data": {"claim": claim, "articles": articles}
                    })
                except Exception as e:
                    result = {"status": "error", "message": str(e)}

        if result.get("status") != "success":
            return {
                "sender": "autogen_bridge",
                "status": "error",
                "debate_log": [],
                "consensus": "",
                "engine": f"Multi-Agent Debate (unavailable)",
                "message": result.get("message", "No verification result was available for the debate.")
            }

        verdict = result.get("verdict", "Unverified")
        confidence = result.get("confidence", 0.0)
        agreement = result.get("agreement_score")
        model_results = result.get("model_results", []) or []
        consensus_engine = result.get("engine", "Consensus")

        debate_log: List[Dict[str, Any]] = []

        # Stage 1 — FactChecker: each model's independent assessment, as reported live.
        if model_results:
            for mr in model_results:
                mr_verdict = mr.get("verdict", "Unverified")
                snippet = (mr.get("straight_answer") or mr.get("summary") or "").strip()[:240]
                debate_log.append({
                    "agent": "FactCheckerAgent",
                    "display": "Fact Checker",
                    "model": mr.get("engine", "LLM"),
                    "verdict": mr_verdict,
                    "confidence": int(mr.get("confidence", 0) * 100),
                    "message": snippet or f"Assessed the claim as '{mr_verdict}'.",
                })
        else:
            debate_log.append({
                "agent": "FactCheckerAgent",
                "display": "Fact Checker",
                "model": "Local Heuristic Engine",
                "verdict": None,
                "confidence": None,
                "offline": True,
                "message": "No live LLM responses were available — assessment produced by the Local Heuristic Engine.",
            })

        # Stage 2 — Critic: surfaces cross-model agreement or divergence.
        if agreement is not None:
            if agreement >= 0.7:
                critique = (f"Corroboration check: {int(agreement * 100)}% cross-model agreement on "
                            f"'{verdict}'. No material contradiction detected; the evidence is mutually reinforcing.")
            else:
                critique = (f"Divergence check: only {int(agreement * 100)}% cross-model agreement. "
                            "The models disagree on this claim, so the verdict carries lower confidence.")
            debate_log.append({
                "agent": "CriticAgent",
                "display": "Critic",
                "verdict": verdict,
                "confidence": int(confidence * 100),
                "message": critique,
            })
        else:
            debate_log.append({
                "agent": "CriticAgent",
                "display": "Critic",
                "verdict": verdict,
                "confidence": int(confidence * 100),
                "offline": True,
                "message": "No live model outputs to critique — verdict produced by the Local Heuristic Engine.",
            })

        # Stage 3 — Consensus: moderator aggregates the cross-examination.
        if model_results:
            consensus_message = (f"Cross-examined {len(model_results)} independent models and compiled the final "
                                 f"consensus: '{verdict}' at {int(confidence * 100)}% confidence "
                                 f"({consensus_engine}).")
        else:
            consensus_message = (f"Compiled the final consensus from the local heuristic engine: '{verdict}' at "
                                 f"{int(confidence * 100)}% confidence.")
        debate_log.append({
            "agent": "ConsensusAgent",
            "display": "Consensus",
            "verdict": verdict,
            "confidence": int(confidence * 100),
            "offline": not bool(model_results),
            "message": consensus_message,
        })

        consensus = f"{verdict} at {int(confidence * 100)}% confidence"
        if agreement is not None:
            consensus += f" (cross-model agreement {int(agreement * 100)}%)"

        models_count = len(model_results)
        engine_label = f"Multi-Agent Debate ({models_count} models)" if models_count else "Multi-Agent Debate (Local Heuristic)"
        return {
            "sender": "autogen_bridge",
            "status": "success",
            "claim": claim,
            "debate_log": debate_log,
            "consensus": consensus,
            "engine": engine_label,
        }