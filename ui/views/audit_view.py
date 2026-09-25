"""
ClaimShield AI — System Audit Logs View.
"""

from __future__ import annotations

import json
import streamlit as st
from app.utils.security import decrypt_data
from ui.views.common import (
    render_clean_html,
    render_html,
    icon_md,
    NEWSPAPER,
    SCHEDULE,
    SELL,
)


def render_audit_page(db):
    """Renders cryptographic verification ledger and decrypted audit logs."""
    render_html("""
    <div class='glass-card' style='border-left: 5px solid #10B981; margin-bottom: 22px; background: var(--glass-surface-tint-success);'>
        <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;'>
            <div>
                <h3 style='margin: 0 0 4px 0; color: #065F46; font-size: 1.25em;'><span class="material-symbols-rounded">shield</span> Cryptographic Verification Ledger</h3>
                <p style='color: #047857; margin: 0; font-size: 0.88em; line-height: 1.5;'>
                    Immutable audit trail. Every verified query, model reasoning trace, and citation is encrypted at rest using <strong>Fernet AES-128-CBC</strong>.
                </p>
            </div>
            <div style='display: flex; gap: 8px; flex-wrap: wrap;'>
                <span class='verdict-badge' style='background: rgba(16, 185, 129, 0.2); color: #047857; border: 1px solid rgba(16, 185, 129, 0.4); font-size: 0.74em;'>
                    <span class="material-symbols-rounded">lock</span> Fernet AES-128-CBC
                </span>
                <span class='verdict-badge' style='background: rgba(79, 70, 229, 0.15); color: #4338CA; border: 1px solid rgba(79, 70, 229, 0.35); font-size: 0.74em;'>
                    <span class="material-symbols-rounded">generating_tokens</span> PBKDF2 Salted
                </span>
            </div>
        </div>
    </div>
    """)
    
    user_logs = db.get_logs_by_user(st.session_state.username)
    
    if not user_logs:
        st.info("You haven't run any fact checks yet. Check a claim on the Verification Dashboard to populate this audit table.")
    else:
        for l in user_logs:
            details = {}
            try:
                raw = l["details_json"]
                decrypted_json = decrypt_data(raw)
                details = json.loads(decrypted_json)
            except Exception:
                try:
                    details = json.loads(l["details_json"])
                except Exception:
                    pass
            
            verdict = l["verdict"]
            v_class = "verdict-unclear"
            if verdict in ["Supported", "True"]:
                v_class = "verdict-supported"
            elif verdict in ["Contradicted", "False"]:
                v_class = "verdict-contradicted"
            elif verdict in ["Answered", "General Info"]:
                v_class = "verdict-answered"
            
            expander_label = f"{icon_md(SCHEDULE)} {l['timestamp']} ── Claim: \"{l['claim'][:65]}...\""
            with st.expander(expander_label):
                render_html(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 8px; border-bottom: 1px solid rgba(226,232,240,0.8); padding-bottom: 10px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span class="verdict-badge {v_class}">{verdict}</span>
                        <span style="font-family:'JetBrains Mono',monospace; font-size: 0.78em; color: #64748B; background: rgba(241,245,249,0.85); padding: 4px 10px; border-radius: 9999px; border: 1px solid rgba(226,232,240,0.85);">
                            UTC: {l['timestamp']}
                        </span>
                    </div>
                    <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(255, 255, 255, 0.75); padding: 4px 12px; border-radius: 9999px; border: 1px solid var(--glass-border); font-size: 0.85em;">
                        <span style="color: #64748B; font-weight: 600;">Certainty:</span>
                        <strong style="color: #0F172A;">{int(l['confidence']*100)}%</strong>
                    </div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.5); border-left: 4px solid #4F46E5; padding: 12px 16px; border-radius: 10px; margin-bottom: 14px;">
                    <div style="font-size: 0.78em; color: #4F46E5; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px;">Audited Model Rationale</div>
                    <div style="font-size: 0.94em; color: #1E293B; line-height: 1.6;">
                        {details.get('summary', 'No reasoning logged.')}
                    </div>
                </div>
                """)
                
                if details.get("entities"):
                    st.markdown(f"**{icon_md(SELL)} Extracted Named Entities:**")
                    ents_html = "<div style='display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;'>"
                    for ent in details["entities"]:
                        if not isinstance(ent, dict):
                            continue
                        ents_html += f"<span class='verdict-badge badge-secondary' style='font-size: 0.78em;'>{ent.get('text','')} <span style='opacity: 0.7;'>({ent.get('label','MISC')})</span></span>"
                    ents_html += "</div>"
                    render_html(ents_html)

                if details.get("articles_retrieved"):
                    st.markdown(f"**{icon_md(NEWSPAPER)} Referenced Source Articles (FAISS Cosine Similarity):**")
                    for s in details["articles_retrieved"]:
                        if not isinstance(s, dict):
                            continue
                        st.markdown(f"- **{s.get('source','Unknown')}**: {s.get('title','')} `(Score: {s.get('score', 0.0):.4f})`")

