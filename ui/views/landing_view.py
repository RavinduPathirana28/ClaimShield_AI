"""
ClaimShield AI — Landing Page View (Unauthenticated Visitors).
"""

from __future__ import annotations

import streamlit as st
from ui.views.common import (
    LOGO_SRC,
    render_clean_html,
    render_html,
    get_typewriter_subtitle_html,
    icon_md,
    DIAMOND,
    SMART_TOY,
    CARD_MEMBERSHIP,
    STAR,
)


def render_landing_page(db=None):
    """Renders the comprehensive landing page for unauthenticated visitors."""
    # ---- HERO SECTION ----
    subtitle_text = (
        "ClaimShield AI is an advanced agentic fact-verification platform powered by a collaborative "
        "network of 5 specialized AI agents, vector RAG retrieval, and multi-LLM consensus "
        "— delivering transparent, evidence-backed verdicts instantly."
    )
    subtitle_html = get_typewriter_subtitle_html(subtitle_text)

    hero_markup = f"""
    <div class='hero-section'>
        <div class='hero-logo-wrap'>
            <div style='display:inline-flex; padding: 10px; border-radius: 36px; background: linear-gradient(135deg, rgba(255,255,255,0.65) 0%, rgba(255,255,255,0.20) 100%); backdrop-filter: blur(24px); border: 1px solid rgba(255,255,255,0.85); box-shadow: 0 16px 40px -10px rgba(15,23,42,0.08), inset 0 2px 2px rgba(255,255,255,0.95);'>
                <img src='{LOGO_SRC}' class='hero-logo-img' style='margin:0;' alt='ClaimShield AI'/>
            </div>
        </div>
        <div class='hero-badge'>
            <span class='hero-badge-dot'></span>
            Now Live — Multi-Agent AI System
        </div>
        <div class='hero-title'>Truth Verified.<br/>In Real Time.</div>
        {subtitle_html}
    </div>
    """
    render_clean_html(hero_markup)

    # Hero CTA: Only [ Start Verifying Claims ]
    _, col_hero_btn, _ = st.columns([1.2, 1.6, 1.2])
    with col_hero_btn:
        render_clean_html("<div id='hero-btn-anchor' class='hero-btn-container'></div>")
        if st.button("Start Verifying Claims", icon=":material/shield:", key="btn_hero_start_verifying", type="primary", use_container_width=True):
            st.session_state.show_access_portal = True
            st.rerun()

    # ---- STATS ROW ----
    st.markdown("""
    <div class='stats-row'>
        <div class='stat-item'>
            <div class='stat-value'>5</div>
            <div class='stat-label'>Specialized Agents</div>
        </div>
        <div class='stat-item'>
            <div class='stat-value'>3</div>
            <div class='stat-label'>LLM Consensus Models</div>
        </div>
        <div class='stat-item'>
            <div class='stat-value'>A2A</div>
            <div class='stat-label'>Messaging Protocol</div>
        </div>
        <div class='stat-item'>
            <div class='stat-value'>FAISS</div>
            <div class='stat-label'>Vector Retrieval</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- TRUST BAR ----
    st.markdown("""
    <div class='trust-bar'>
        <div class='trust-item'><span class='trust-icon'><span class="material-symbols-rounded">key</span></span> PBKDF2-SHA256 Hashing</div>
        <div class='trust-item'><span class='trust-icon'><span class="material-symbols-rounded">generating_tokens</span></span> JWT Session Tokens</div>
        <div class='trust-item'><span class='trust-icon'><span class="material-symbols-rounded">bolt</span></span> Token-Bucket Rate Limiting</div>
        <div class='trust-item'><span class='trust-icon'><span class="material-symbols-rounded">assignment</span></span> Encrypted Audit Trails</div>
        <div class='trust-item'><span class='trust-icon'><span class="material-symbols-rounded">public</span></span> LangGraph Stateful Workflow</div>
    </div>
    """, unsafe_allow_html=True)

    # ---- FEATURE CARDS ----
    st.markdown("""
    <div class='section-eyebrow'>Platform Capabilities</div>
    <div class='section-title'>Everything you need to verify the truth</div>
    <div class='section-desc'>Six pillars of our multi-agent verification engine, built for journalists, researchers & news organizations.</div>
    """, unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        st.markdown("""
        <div class='feature-card' style='--card-accent: linear-gradient(90deg, #4338CA, #2563EB);'>
            <div class='feature-icon-wrap' style='background: rgba(67,56,202,0.10);'><span class="material-symbols-rounded">psychology</span></div>
            <div class='feature-card-title'>Multi-Agent Orchestration</div>
            <div class='feature-card-desc'>
                Security, NLP, Retrieval, Verification, and Explainer agents collaborate
                via A2A/1.0 JSON protocol with full message tracing and live audit logs.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with fc2:
        st.markdown("""
        <div class='feature-card' style='--card-accent: linear-gradient(90deg, #0284C7, #38BDF8);'>
            <div class='feature-icon-wrap' style='background: rgba(2,132,199,0.10);'><span class="material-symbols-rounded">bolt</span></div>
            <div class='feature-card-title'>Vector RAG & FAISS Index</div>
            <div class='feature-card-desc'>
                Semantic similarity retrieval over curated news repositories with cosine
                ranking, top-5 expansion, and direct inline source citations.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with fc3:
        st.markdown("""
        <div class='feature-card' style='--card-accent: linear-gradient(90deg, #4F46E5, #6D28D9);'>
            <div class='feature-icon-wrap' style='background: rgba(79,70,229,0.10);'><span class="material-symbols-rounded">smart_toy</span></div>
            <div class='feature-card-title'>Multi-LLM Consensus</div>
            <div class='feature-card-desc'>
                Three independent LLMs independently evaluate claims, then vote on a consensus
                verdict — eliminating single-model hallucination bias.
            </div>
        </div>
        """, unsafe_allow_html=True)

    fc4, fc5, fc6 = st.columns(3)
    with fc4:
        st.markdown("""
        <div class='feature-card' style='--card-accent: linear-gradient(90deg, #059669, #10B981);'>
            <div class='feature-icon-wrap' style='background: rgba(5,150,105,0.10);'><span class="material-symbols-rounded">lock</span></div>
            <div class='feature-card-title'>Enterprise-Grade Security</div>
            <div class='feature-card-desc'>
                PBKDF2-SHA256 password hashing, signed JWT tokens, token-bucket
                rate limiting, and AES-encrypted audit trails at every layer.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with fc5:
        st.markdown("""
        <div class='feature-card' style='--card-accent: linear-gradient(90deg, #D97706, #F59E0B);'>
            <div class='feature-icon-wrap' style='background: rgba(217,119,6,0.10);'><span class="material-symbols-rounded">alt_route</span></div>
            <div class='feature-card-title'>LangGraph Stateful Workflow</div>
            <div class='feature-card-desc'>
                Optional LangGraph execution mode provides a stateful graph-based pipeline
                for complex multi-step reasoning with full state persistence.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with fc6:
        st.markdown("""
        <div class='feature-card' style='--card-accent: linear-gradient(90deg, #DC2626, #EF4444);'>
            <div class='feature-icon-wrap' style='background: rgba(220,38,38,0.10);'><span class="material-symbols-rounded">bar_chart</span></div>
            <div class='feature-card-title'>Explainability & Reports</div>
            <div class='feature-card-desc'>
                Every verdict comes with a cited evidence summary, confidence scores,
                source attribution, and downloadable PDF verification reports.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---- AGENT PIPELINE VISUALIZATION ----
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='section-eyebrow'>How it works</div>
    <div class='section-title'>The 5-Agent Verification Pipeline</div>
    <div class='section-desc'>Each claim flows through our sequential agent network — from authentication to final explanation.</div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='glass-card'>
        <div class='pipeline-flow'>
            <div class='pipeline-agent'>
                <div class='pipeline-agent-icon' style='background: rgba(239,68,68,0.15); border-color: #EF4444; color: #EF4444;'><span class="material-symbols-rounded">key</span></div>
                <div class='pipeline-agent-label'>Security<br/>Agent</div>
            </div>
            <div class='pipeline-arrow'>→</div>
            <div class='pipeline-agent'>
                <div class='pipeline-agent-icon' style='background: rgba(56,189,248,0.15); border-color: #38BDF8; color: #38BDF8;'><span class="material-symbols-rounded">biotech</span></div>
                <div class='pipeline-agent-label'>NLP<br/>Agent</div>
            </div>
            <div class='pipeline-arrow'>→</div>
            <div class='pipeline-agent'>
                <div class='pipeline-agent-icon' style='background: rgba(245,158,11,0.15); border-color: #F59E0B; color: #F59E0B;'><span class="material-symbols-rounded">search</span></div>
                <div class='pipeline-agent-label'>Retrieval<br/>Agent</div>
            </div>
            <div class='pipeline-arrow'>→</div>
            <div class='pipeline-agent'>
                <div class='pipeline-agent-icon' style='background: rgba(168,85,247,0.15); border-color: #A855F7; color: #A855F7;'><span class="material-symbols-rounded">balance</span></div>
                <div class='pipeline-agent-label'>Verification<br/>Agent</div>
            </div>
            <div class='pipeline-arrow'>→</div>
            <div class='pipeline-agent'>
                <div class='pipeline-agent-icon' style='background: rgba(16,185,129,0.15); border-color: #10B981; color: #10B981;'><span class="material-symbols-rounded">lightbulb</span></div>
                <div class='pipeline-agent-label'>Explainer<br/>Agent</div>
            </div>
            <div class='pipeline-arrow'>→</div>
            <div class='pipeline-agent'>
                <div class='pipeline-agent-icon' style='background: rgba(99,102,241,0.2); border-color: #6366F1; color: #818CF8;'><span class="material-symbols-rounded">check_circle</span></div>
                <div class='pipeline-agent-label'>Verdict<br/>& Report</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- PRICING TABS ----
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    landing_tabs = st.tabs([f"{icon_md(DIAMOND)} Subscription Plans", f"{icon_md(SMART_TOY)} Responsible AI & Ethics"])

    with landing_tabs[0]:
        st.markdown("""
        <div class='section-eyebrow'>Pricing</div>
        <div class='section-title'>Simple, Transparent Plans</div>
        <div class='section-desc'>Start with our Free plan or upgrade to Pro for expanded evidence depth.</div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            render_html("""
            <div class='plan-card' style='border: 2px solid rgba(148, 163, 184, 0.35); overflow: visible;'>
                <div>
                    <h4>Free Plan</h4>
                    <div class='plan-price-tag' style='color: #0F172A;'>&#36;0</div>
                    <p style='color: #64748B; font-size: 0.85em;'>Essential tools for individual fact-checking</p>
                    <ul class='plan-feature-list'>
                        <li><strong>3 requests</strong> token capacity</li>
                        <li><strong>Displays only 2 resources</strong> to user</li>
                        <li>Refills 3 tokens / hour</li>
                        <li>Standard NLP & FAISS vector search</li>
                        <li>Encrypted audit logging</li>
                    </ul>
                </div>
            </div>
            """)
            if st.button("Choose Free Plan", icon=f":material/{CARD_MEMBERSHIP}:", key="btn_landing_choose_free", use_container_width=True):
                st.session_state.portal_mode = "Register"
                st.session_state.portal_plan = "user"
                st.session_state.show_access_portal = True
                st.rerun()
        with col2:
            render_html("""
            <div class='plan-card' style='border: 2px solid #4F46E5; overflow: visible;'>
                <div class='plan-popular-tag'>Popular</div>
                <div>
                    <h4>Pro Plan</h4>
                    <div class='plan-price-tag' style='color: #4F46E5;'>&#36;19<span style='font-size: 0.45em; color: #64748B;'>/mo</span></div>
                    <p style='color: #64748B; font-size: 0.85em;'>For journalists, researchers & media professionals</p>
                    <ul class='plan-feature-list'>
                        <li><strong>Unlimited</strong> claim checks (Zero throttles)</li>
                        <li><strong>Displays at least 3 (if available) & up to 5 max</strong></li>
                        <li>Priority LLM reasoning queue</li>
                        <li>Multi-Agent Persona Debate & LangGraph</li>
                        <li>Verified live source citations</li>
                    </ul>
                </div>
            </div>
            """)
            if st.button("Choose Pro Plan", icon=f":material/{STAR}:", key="btn_landing_choose_pro", use_container_width=True):
                st.session_state.portal_mode = "Register"
                st.session_state.portal_plan = "pro"
                st.session_state.show_access_portal = True
                st.rerun()

    with landing_tabs[1]:
        st.markdown(f"### {icon_md(SMART_TOY)} Responsible AI — Ethics & Governance")
        st.markdown("ClaimShield AI enforces fairness, explainability, transparency, and data protection across all tiers.")
