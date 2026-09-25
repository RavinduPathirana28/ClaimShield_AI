"""
ClaimShield AI — Claim Verification Dashboard View.
"""

from __future__ import annotations

import html
import time
import streamlit as st
from app.agents.base_agent import BaseAgent
from ui.views.common import (
    render_clean_html,
    render_html,
    icon_md,
    pdf_report_bytes,
    _pipeline_loading,
    _report_pipeline_step,
    _ORIGINAL_BASE_SEND,
    _PIPELINE_LOCK,
    SEARCH,
    SMART_TOY,
    SMARTPHONE,
    NIGHTLIGHT,
    COFFEE,
    BAR_CHART,
    CHECK_CIRCLE,
    CANCEL,
    LIGHTBULB,
    ARROW_FORWARD,
    EXPLORE,
    LINK,
    NEWSPAPER,
    BOLT,
    SHIELD,
    BALANCE,
    BIOTECH,
    PUBLIC,
    HANDSHAKE,
    DESCRIPTION,
    EDIT_NOTE,
    RECORD_VOICE_OVER,
    SELL,
    PUSH_PIN,
    ICON_BALANCE,
    ICON_CANCEL,
    ICON_CHAT,
    ICON_CHECK,
    ICON_CHECK_CIRCLE,
    ICON_HELP,
    ICON_SEARCH,
    ICON_TRACK_CHANGES,
    ICON_WARNING,
)


def render_verification_page(db, orchestrator):
    """Renders the verification dashboard, claim input, live agent execution, and results."""
    st.markdown(f"### {icon_md(SEARCH)} Ask a Question or Verify a Claim")
    st.markdown("Type any general question or factual statement below. Our multi-agent AI system will evaluate it and provide a realistic, easy-to-understand explanation.")

    # Preset sample query buttons for quick testing
    st.markdown("**Sample Questions & Claims:**")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    sample_query = None
    with col_s1:
        if st.button("What is AI?", icon=f":material/{SMART_TOY}:", use_container_width=True):
            sample_query = "What is Artificial Intelligence?"
    with col_s2:
        if st.button("iPhone 18 in 2026?", icon=f":material/{SMARTPHONE}:", use_container_width=True):
            sample_query = "Apple will launch the iPhone 18 in July 2026."
    with col_s3:
        if st.button("Why is sky blue?", icon=f":material/{NIGHTLIGHT}:", use_container_width=True):
            sample_query = "Why is the sky blue?"
    with col_s4:
        if st.button("Is coffee healthy?", icon=f":material/{COFFEE}:", use_container_width=True):
            sample_query = "Is drinking coffee good for heart health?"

    if "claim_text_val" not in st.session_state:
        st.session_state.claim_text_val = ""
    if "recommendations_cache" not in st.session_state:
        st.session_state.recommendations_cache = []
    if sample_query:
        st.session_state.claim_text_val = sample_query

    claim_input = st.text_area(
        "Query or Claim Input", 
        value=st.session_state.claim_text_val,
        placeholder="e.g. 'What is quantum computing?', 'Why is the sky blue?', or 'Apple will launch iPhone 18 in July 2026'",
        label_visibility="collapsed",
        height=100
    )
    
    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        submit_fact = st.button("Run ClaimShield AI")
    with col_info:
        st.caption("Supports general knowledge questions as well as factual news verification.")

    # A recommended claim is selected on the report panel: it pre-fills the
    # input, sets this flag, and reruns so the pipeline auto-executes.
    auto_verify_claim = st.session_state.pop("pending_auto_verify", None)

    if submit_fact or auto_verify_claim:
        if not claim_input.strip():
            st.warning("Please type a question or statement first.")
        else:
            with _pipeline_loading():
                st.session_state.agent_logs = []
                
                def trace_agent_message(sender, recipient, action, data, response):
                    log_entry = {
                        "timestamp": time.strftime("%H:%M:%S", time.localtime()),
                        "from": sender,
                        "to": recipient,
                        "action": action,
                        "data_sent": data,
                        "response_received": response
                    }
                    st.session_state.agent_logs.append(log_entry)
                
                def custom_send(self, recipient, action, data):
                    _report_pipeline_step(action)
                    resp = _ORIGINAL_BASE_SEND(self, recipient, action, data)
                    trace_agent_message(self.name, recipient.name, action, data, resp)
                    return resp

                selected_engine = st.session_state.get("engine_mode", "Standard A2A Protocol")
                orchestrator_req = {
                    "action": "verify",
                    "data": {
                        "claim": claim_input,
                        "username": st.session_state.username,
                        "engine_mode": selected_engine
                    }
                }

                pipeline_start_time = time.time()
                with _PIPELINE_LOCK:
                    try:
                        # Single-session tracing hook. Guarded by the lock so a
                        # concurrent rerun never sees a half-patched BaseAgent,
                        # and failures render cleanly instead of crashing the page.
                        BaseAgent.send_message = custom_send
                        pipeline_result = orchestrator.handle_message(orchestrator_req)
                    except Exception as e:
                        print(f"[UI] Pipeline raised an unexpected exception: {e}")
                        pipeline_result = {"status": "error", "message": f"Unexpected pipeline error: {e}"}
                    finally:
                        BaseAgent.send_message = _ORIGINAL_BASE_SEND
                pipeline_end_time = time.time()
                
                if pipeline_result.get("status") == "rate_limited":
                    st.error(pipeline_result.get("message"))
                    st.info(f"Please wait {pipeline_result.get('retry_after_seconds')} seconds, or upgrade to the Pro Plan on the Account page.")
                elif pipeline_result.get("status") == "success":
                    st.markdown(f"### {icon_md(BAR_CHART)} AI Analysis Report")
                    
                    verdict = pipeline_result["verdict"]
                    confidence = pipeline_result["confidence"]
                    straight_ans = pipeline_result.get("straight_answer", "")
                    summary = pipeline_result["summary"]
                    entities = pipeline_result.get("entities", [])
                    citations = pipeline_result.get("citations", [])
                    engine = pipeline_result.get("engine", "Unknown")
                    ret_articles = pipeline_result.get("articles", [])

                    # Per-model consensus metadata from the verification agent's latest run
                    agreement_score = None
                    model_breakdown = []
                    try:
                        last_result = getattr(orchestrator.verification_agent, "last_result", None)
                        lc = (last_result or {}).get("claim", "").strip().lower()
                        pc = pipeline_result.get("claim", "").strip().lower()
                        if lc and (lc == pc or lc in pc or pc in lc):
                            agreement_score = (last_result or {}).get("agreement_score")
                            model_breakdown = (last_result or {}).get("model_results", []) or []
                    except Exception:
                        pass
                    
                    v_class = "verdict-unclear"
                    verdict_display = verdict
                    if verdict in ["Supported", "True"]:
                        v_class = "verdict-supported"
                        verdict_display = f"{ICON_CHECK_CIRCLE} Verified True"
                    elif verdict in ["Contradicted", "False"]:
                        v_class = "verdict-contradicted"
                        verdict_display = f"{ICON_CANCEL} Debunked / False"
                    elif verdict in ["Answered", "General Info"]:
                        v_class = "verdict-answered"
                        verdict_display = f"{ICON_CHAT} Direct Answer"
                    elif verdict in ["Unverified", "Unclear"]:
                        v_class = "verdict-unclear"
                        verdict_display = f"{ICON_HELP} Unverified"

                    if not straight_ans:
                        straight_ans = summary.split(". ")[0] + "." if summary else verdict_display
                        
                    v_border = "#059669" if verdict in ["Supported", "True"] else "#DC2626" if verdict in ["Contradicted", "False"] else "#4F46E5" if verdict in ["Answered", "General Info"] else "#D97706"
                    v_bg = "var(--glass-surface-tint-success)" if verdict in ["Supported", "True"] else "linear-gradient(135deg, rgba(254, 242, 242, 0.75) 0%, rgba(255, 255, 255, 0.35) 100%)" if verdict in ["Contradicted", "False"] else "var(--glass-surface-tint-primary)" if verdict in ["Answered", "General Info"] else "linear-gradient(135deg, rgba(254, 243, 199, 0.70) 0%, rgba(255, 255, 255, 0.35) 100%)"

                    # 1. Straight Answer Section
                    render_html(f"""
                    <div class="glass-card" style="border-left: 6px solid {v_border}; background: {v_bg};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                            <div class="verdict-badge {v_class}">{verdict_display}</div>
                            <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(255, 255, 255, 0.75); padding: 5px 14px; border-radius: 9999px; border: 1px solid var(--glass-border); box-shadow: inset 0 1px 1px rgba(255,255,255,0.9);">
                                <span style="font-size: 0.76em; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">Confidence</span>
                                <span style="font-size: 1.15em; font-weight: 800; color: #0F172A;">{int(confidence*100)}%</span>
                            </div>
                        </div>
                        <div style="font-size: 0.82em; color: {v_border}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">
                            <span class="material-symbols-rounded">track_changes</span> Straight Answer
                        </div>
                        <h3 style="margin-top: 0; color: #0F172A; font-size: 1.35em; font-weight: 750; line-height: 1.4;">{straight_ans}</h3>
                    </div>
                    """)
                    
                    # 2. Detailed Explanation Section
                    st.markdown(f"""
                    <div class="glass-card">
                        <div style="font-size: 0.85em; color: #0284C7; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                            <span class="material-symbols-rounded">menu_book</span> Detailed Explanation
                        </div>
                        <p style="font-size: 1.05em; line-height: 1.6; color: #1E293B; margin-bottom: 15px;">{summary}</p>
                        <div style="font-size: 0.8em; color: #64748B;">
                            Processing Engine: <strong>{engine}</strong> | Execution Time: {pipeline_end_time - pipeline_start_time:.2f}s
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 2b. Multi-Model Consensus & Explainability
                    verdict_icons = {"Supported": ICON_CHECK_CIRCLE, "Contradicted": ICON_CANCEL, "Answered": ICON_CHAT, "Unverified": ICON_HELP}
                    verdict_colors = {"Supported": "#059669", "Contradicted": "#DC2626", "Answered": "#4F46E5", "Unverified": "#D97706"}
                    provider_dots = {"Groq": "#F55036", "Gemini": "#4285F4", "Ollama": "#0D9488"}

                    def esc(s):
                        return html.escape(str(s or ""), quote=True)

                    consensus_body = ""
                    if model_breakdown:
                        row_html = []
                        for mr in model_breakdown:
                            eng = mr.get("engine", "LLM") or "LLM"
                            prov = next((p for p in ("Groq", "Gemini", "Ollama") if p in eng), "LLM")
                            dot = provider_dots.get(prov, "#64748B")
                            v = mr.get("verdict", "Unverified")
                            vcolor = verdict_colors.get(v, "#D97706")
                            conf = int(mr.get("confidence", 0) * 100)
                            snippet = (mr.get("straight_answer") or mr.get("summary") or "").strip()
                            if len(snippet) > 160:
                                snippet = snippet[:160].rsplit(" ", 1)[0] + "…"
                            snippet_html = f'<div class="cs-cc-snippet" title="{esc(snippet)}">{esc(snippet)}</div>' if snippet else ""
                            row_html.append(f"""
                            <div class="cs-cc-row">
                                <div class="cs-cc-meta">
                                    <span class="cs-provider-dot" style="background:{dot}"></span>
                                    <span class="cs-cc-name">{esc(eng)}</span>
                                    <span class="cs-cc-verdict" style="color:{vcolor}; background:{vcolor}18; border:1px solid {vcolor}44;">{verdict_icons.get(v, ICON_HELP)} {v}</span>
                                </div>
                                <div class="cs-cc-meter">
                                    <span class="cs-cc-pct">{conf}%</span>
                                    <div class="cs-cc-track"><div class="cs-cc-fill" style="width:{min(max(conf, 4), 100)}%; background:linear-gradient(90deg,{vcolor},{dot});"></div></div>
                                </div>
                            </div>
                            {snippet_html}""")
                        consensus_body = "".join(row_html)
                    else:
                        consensus_body = """
                            <div class="cs-fallback-note">
                                <strong>No live LLM models were available.</strong> This verdict was produced by the
                                built-in Local Heuristic Engine. Add working Groq / Gemini API keys or start Ollama
                                to see the per-model comparison below.
                            </div>"""

                    agreement_html = ""
                    if agreement_score is not None:
                        agr_pct = int(agreement_score * 100)
                        converged = agreement_score >= 0.7
                        fill_color = "linear-gradient(90deg,#059669,#0284C7)" if converged else "linear-gradient(90deg,#D97706,#DC2626)"
                        note_color = "#059669" if converged else "#D97706"
                        note_text = ("The models converged on this verdict." if converged
                                     else "The models diverged — treat this verdict with lower confidence.")
                        agreement_html = f"""
                        <div class="cs-agreement-compact">
                            <div class="cs-agree-top">
                                <span class="cs-agree-note" style="color:{note_color};">{ICON_CHECK if converged else ICON_WARNING} {note_text}</span>
                                <span class="cs-agree-pct" style="color:{note_color};">{agr_pct}% agreement</span>
                            </div>
                            <div class="cs-cc-track"><div class="cs-cc-fill" style="width:{agr_pct}%; background:{fill_color};"></div></div>
                        </div>"""

                    render_html(f"""
                    <div class="glass-card" style="border-left: 4px solid #D97706; padding: 16px 18px;">
                        <div style="display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:6px;">
                            <div style="font-size: 0.85em; color: #D97706; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                                <span class="material-symbols-rounded">handshake</span> Multi-Model Consensus &amp; Explainability
                            </div>
                        </div>
                        {consensus_body}
                        {agreement_html}
                        <div style="font-size: 0.72em; color: #94A3B8; margin-top: 10px;">
                            Each model evaluates the same evidence independently; the verdict reflects their weighted consensus.
                        </div>
                    </div>
                    """)

                    # 2c. Downloadable PDF verification report
                    try:
                        report_bytes = pdf_report_bytes({**pipeline_result, "agreement_score": agreement_score})
                        if report_bytes:
                            st.download_button(
                                "Download Verification Report (PDF)",
                                icon=f":material/{DESCRIPTION}:",
                                data=report_bytes,
                                file_name=f"claimshield_report_{time.strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                            )
                        else:
                            st.caption("PDF report unavailable — install 'reportlab' (pip install reportlab).")
                    except Exception as e:
                        st.caption(f"PDF report unavailable: {e}")

                    # Evidence Summary
                    ev_summary = pipeline_result.get("evidence_summary", "")
                    if ev_summary:
                        st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid #4F46E5;">
                            <div style="font-size: 0.85em; color: #4F46E5; font-weight: 700; margin-bottom: 8px;"><span class="material-symbols-rounded">edit_note</span> Extractive Evidence Highlights</div>
                            <p style="font-size: 1.0em; line-height: 1.6; color: #1E293B;">{ev_summary}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    # Scikit-Learn ML Stance
                    ml_info = pipeline_result.get("ml_classification", {})
                    if ml_info:
                        st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid #059669;">
                            <div style="font-size: 0.85em; color: #059669; font-weight: 700; margin-bottom: 4px;"><span class="material-symbols-rounded">bolt</span> Scikit-Learn ML Credibility Analysis</div>
                            <div style="color: #1E293B;">Prediction Label: <strong>{ml_info.get('label', 'N/A')}</strong> | Confidence: <strong>{int(ml_info.get('confidence', 0)*100)}%</strong></div>
                            <div style="font-size: 0.8em; color: #64748B;">Engine: {ml_info.get('engine', 'TF-IDF Vectorizer')}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Persona Debate Transcript
                    autogen_info = pipeline_result.get("autogen_debate", {})
                    if autogen_info:
                        stage_cfg = {
                            "FactCheckerAgent": {"icon": ICON_SEARCH, "label": "Fact Checker", "color": "#0284C7"},
                            "CriticAgent": {"icon": ICON_BALANCE, "label": "Critic", "color": "#D97706"},
                            "ConsensusAgent": {"icon": ICON_TRACK_CHANGES, "label": "Consensus", "color": "#059669"},
                        }
                        turn_html = []
                        for msg in autogen_info.get("debate_log", []):
                            agent = msg.get("agent", "")
                            cfg = stage_cfg.get(agent, {"icon": ICON_CHAT, "label": agent or "Agent", "color": "#64748B"})
                            color = cfg["color"]
                            model_badge = ""
                            if msg.get("model"):
                                model_badge = (f'<span class="cs-debate-verdict" style="color:#1E293B; background:rgba(241,245,249,0.9); '
                                               f'border:1px solid rgba(203,213,225,0.8);">{esc(msg["model"])}</span>')
                            verdict_badge = ""
                            if msg.get("verdict"):
                                vcolor = verdict_colors.get(msg["verdict"], "#64748B")
                                verdict_badge = (f'<span class="cs-debate-verdict" style="color:{vcolor}; background:{vcolor}18; '
                                                 f'border:1px solid {vcolor}44;">{verdict_icons.get(msg["verdict"], ICON_HELP)} {esc(msg["verdict"])}</span>')
                            conf_badge = ""
                            if msg.get("confidence") is not None:
                                conf_badge = (f'<span style="font-size:0.75em; color:#64748B; font-weight:600;">{int(msg["confidence"])}% confidence</span>')
                            turn_html.append(f"""
                            <div class="cs-debate-turn" style="border-left: 4px solid {color};">
                                <div class="cs-debate-head">
                                    <span class="cs-debate-stage" style="color:{color}; background:{color}18; border:1px solid {color}44;">{cfg["icon"]} {cfg["label"]}</span>
                                    {model_badge}
                                    {verdict_badge}
                                    {conf_badge}
                                </div>
                                <div class="cs-debate-message">{esc(msg.get("message", ""))}</div>
                            </div>""")

                        consensus_verdict = autogen_info.get("consensus") or autogen_info.get("message", "")
                        consensus_box = f"""
                        <div class="cs-consensus-box">
                            <div class="cs-consensus-title"><span class="material-symbols-rounded">track_changes</span> Final Consensus</div>
                            <div class="cs-consensus-text">{esc(consensus_verdict)}</div>
                        </div>"""

                        with st.expander(f"{icon_md(RECORD_VOICE_OVER)} Multi-Agent Debate Transcript", expanded=True):
                            render_html(f"""
                            <div style="font-size: 0.85em; color: #64748B; margin-bottom: 12px;">
                                Fueled by <strong style="color: #4F46E5;">{esc(autogen_info.get("engine"))}</strong> — every statement is grounded in an actual model response, never fabricated.
                            </div>
                            """)
                            render_html("".join(turn_html) + consensus_box)

                    # Columns for concepts & quotes (collapsed by default for a compact report)
                    c1, c2 = st.columns(2)
                    with c1:
                        with st.expander(f"{icon_md(SELL)} Key Extracted Concepts (spaCy NER)", expanded=False):
                            if entities:
                                for ent in entities:
                                    if not isinstance(ent, dict):
                                        continue
                                    ent_text = ent.get("text") or "Unknown"
                                    ent_label = ent.get("label") or "MISC"
                                    st.markdown(f"""
                                    <span class='verdict-badge badge-secondary' style='margin-right: 5px; margin-bottom: 5px;'>
                                        <strong>{ent_text}</strong> ({ent_label})
                                    </span>
                                    """, unsafe_allow_html=True)
                            else:
                                st.caption("No specific named entities extracted.")

                    with c2:
                        with st.expander(f"{icon_md(PUSH_PIN)} Key Takeaways & Quotes", expanded=False):
                            if citations:
                                for cit in citations:
                                    if not isinstance(cit, dict):
                                        continue
                                    art_label = f"Article #{cit.get('article_id')}" if cit.get('article_id') else "General Evidence"
                                    cit_quote = cit.get("quote") or "No quote provided."
                                    cit_explanation = cit.get("explanation") or ""
                                    st.markdown(f"""
                                    <div class="citation-box">
                                        <div style="font-size: 0.85em; font-weight: 700; color: #7C3AED; margin-bottom: 5px;">
                                            {art_label}:
                                        </div>
                                        <div style="font-style: italic; font-size: 0.9em; margin-bottom: 8px; color: #1E293B;">
                                            "{cit_quote}"
                                        </div>
                                        <div style="font-size: 0.8em; color: #64748B;">
                                            <strong>Insight:</strong> {cit_explanation}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.caption("No additional citations required for this response.")
                            
                    # Referenced Links (collapsed by default for a compact report)
                    st.markdown("---")
                    with st.expander(f"{icon_md(LINK)} Referenced Sources & Verified Article Links", expanded=False):
                        if ret_articles:
                            live_web_articles = [a for a in ret_articles if "Live Web" in a.get("source", "")]
                            db_articles = [a for a in ret_articles if "Live Web" not in a.get("source", "")]
                            article_dates = [a.get("date", "") for a in ret_articles if a.get("date")]
                            newest_date = max(article_dates) if article_dates else "unknown"
                            total_found = pipeline_result.get("total_resources_found", len(ret_articles))
                            is_pro = pipeline_result.get("is_pro_plan", current_role in ["pro", "premium", "newsroom_admin"])

                            if not is_pro:
                                render_html(f"""
                                <div style="font-size: 0.84em; background: rgba(79, 70, 229, 0.08); border: 1px solid rgba(79, 70, 229, 0.25); border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; color: #334155;">
                                    <span class="material-symbols-rounded">lock</span> <strong style="color: #4F46E5;">Free Plan Display:</strong> Showing <strong>{len(ret_articles)}</strong> resources (Free plan displays maximum 2 of {total_found} retrieved). <span style="color: #64748B;">Upgrade to <strong>Pro Plan</strong> to view at least 3 (if available) and up to 5 maximum resources!</span>
                                </div>
                                """)
                            else:
                                render_html(f"""
                                <div style="font-size: 0.84em; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; color: #334155;">
                                    <span class="material-symbols-rounded">star</span> <strong style="color: #059669;">Pro Plan Active:</strong> Displaying <strong>{len(ret_articles)}</strong> verified resources (Pro tier displays at least 3 if available, up to 5 maximum).
                                </div>
                                """)

                            render_html(f"""
                            <div style="font-size: 0.82em; color: #475569; background: rgba(241, 245, 249, 0.8); border: 1px solid rgba(226, 232, 240, 0.9); border-radius: 8px; padding: 8px 12px; margin-bottom: 12px;">
                                <span class="material-symbols-rounded">receipt_long</span> <strong style="color:#0F172A;">Evidence used for this verdict:</strong> {len(ret_articles)} source(s) — {len(db_articles)} from local knowledge base · {len(live_web_articles)} from live web · newest article: {newest_date}
                            </div>
                            """)
                            if live_web_articles:
                                st.markdown("The following live web sources were matched against the claim:")
                            else:
                                st.markdown("The following source articles were retrieved and cross-referenced by FAISS vector similarity:")
                            for idx, art in enumerate(ret_articles):
                                url_link = art.get('url', '#')
                                st.markdown(f"""
                                <div class="article-card" style="border-left: 4px solid #0284C7;">
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                        <div class="article-title" style="font-size: 1.1em; font-weight: 700; color: #0F172A;">
                                            [{idx+1}] {art['title']}
                                        </div>
                                        <span class="badge-secondary" style="font-size: 0.8em; padding: 2px 8px; border-radius: 4px;">
                                            Score: {art['score']:.4f}
                                        </span>
                                    </div>
                                    <div class="article-meta" style="margin-top: 4px; margin-bottom: 8px; color: #64748B; font-size: 0.85em;">
                                        <span class="material-symbols-rounded">newspaper</span> <strong>Source:</strong> {art['source']} | <span class="material-symbols-rounded">calendar_today</span> <strong>Date:</strong> {art['date']}
                                    </div>
                                    <div style="font-size: 0.9em; color: #334155; line-height: 1.5; margin-bottom: 10px;">
                                        {art['content']}
                                    </div>
                                    <div style="background: rgba(241, 245, 249, 0.85); border: 1px solid rgba(226, 232, 240, 0.85); padding: 8px 12px; border-radius: 8px; font-size: 0.85em;">
                                        <span class="material-symbols-rounded">link</span> <strong>Verified Link:</strong> <a href="{url_link}" target="_blank" style="color: #0284C7; font-weight: 600; text-decoration: underline;">{url_link}</a>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info(f"{icon_md(LIGHTBULB)} General knowledge query: No local database links were required. Answer generated using internal facts.")

                    # Persist recommended claims to a cache rendered after the
                    # run block below, so the panel stays clickable across runs.
                    st.session_state.recommendations_cache = pipeline_result.get("recommendations", [])

                else:
                    st.error(f"Fact checking pipeline failed: {pipeline_result.get('message')}")

    # Recommended related claims — click one to verify it next.
    recommendations = st.session_state.get("recommendations_cache", [])
    if recommendations:
        st.markdown("---")
        st.markdown(f"### {icon_md(EXPLORE)} Explore Related Claims")
        st.markdown("High-value claims related to this verification. Select one to run it through the full pipeline.")
        for rec_i, rec_entry in enumerate(recommendations):
            rec_claim = rec_entry.get("claim", "")
            rec_source = rec_entry.get("source", "Related claim")
            rec_sim = int(float(rec_entry.get("similarity", 0.0)) * 100)
            if st.button(
                rec_claim,
                key=f"rec_claim_{rec_i}",
                icon=f":material/{ARROW_FORWARD}:",
                use_container_width=True,
                help="Verify this claim next",
            ):
                st.session_state.claim_text_val = rec_claim
                st.session_state.pending_auto_verify = rec_claim
                st.rerun()
            st.caption(f"{rec_source} · ~{rec_sim}% related")

