"""
ClaimShield AI — A2A Protocol Message Tracing Monitor View.
"""

from __future__ import annotations

import streamlit as st
from ui.views.common import (
    icon_md,
    SETTINGS,
    PUBLIC,
    ARROW_FORWARD,
    OUTBOX,
    INBOX,
)


def render_a2a_page(db=None):
    """Renders real-time JSON message tracing for the A2A/1.0 protocol."""
    st.markdown(f"### {icon_md(SETTINGS)} Multi-Agent A2A/1.0 Protocol Message Tracing")
    st.markdown("""
    Inspect the real-time JSON communications occurring between subagents using the **A2A/1.0 (Agent-to-Agent)** protocol.
    Each message includes a protocol version, unique message ID (UUID4), Unix timestamp, sender/recipient identifiers, action verb, and structured data payload.
    """)

    st.markdown("""
    <div class='glass-card' style='border-left: 4px solid #4F46E5;'>
        <h4 style='color: #4F46E5; margin-bottom: 10px;'><span class="material-symbols-rounded">assignment</span> A2A/1.0 Protocol Specification</h4>
        <table style='width: 100%; border-collapse: collapse; color: #1E293B; font-size: 0.9em;'>
            <tr style='border-bottom: 1px solid rgba(226,232,240,0.85);'>
                <td style='padding: 8px; font-weight: 600; color: #4F46E5; width: 25%;'>Protocol</td>
                <td style='padding: 8px;'>A2A/1.0 — Agent-to-Agent messaging over in-process Python function calls</td>
            </tr>
            <tr style='border-bottom: 1px solid rgba(226,232,240,0.85);'>
                <td style='padding: 8px; font-weight: 600; color: #4F46E5;'>Serialization</td>
                <td style='padding: 8px;'>JSON — validated via dumps/loads round-trip for strict compliance</td>
            </tr>
            <tr style='border-bottom: 1px solid rgba(226,232,240,0.85);'>
                <td style='padding: 8px; font-weight: 600; color: #4F46E5;'>Message ID</td>
                <td style='padding: 8px;'>UUID4 — unique identifier for every message for end-to-end traceability</td>
            </tr>
            <tr style='border-bottom: 1px solid rgba(226,232,240,0.85);'>
                <td style='padding: 8px; font-weight: 600; color: #4F46E5;'>Timestamp</td>
                <td style='padding: 8px;'>Unix epoch float — precise timing for performance profiling</td>
            </tr>
            <tr>
                <td style='padding: 8px; font-weight: 600; color: #4F46E5;'>Transport</td>
                <td style='padding: 8px;'>In-process function invocation — zero-latency delivery via BaseAgent.send_message()</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.agent_logs:
        st.info("No query logs in buffer. Run a claim check from the Verification Dashboard to monitor agent communication flows.")
    else:
        for idx, log in enumerate(st.session_state.agent_logs):
            with st.expander(f"{icon_md(PUBLIC)} Trace #{idx+1} [{log['timestamp']}]: {log['from']} {icon_md(ARROW_FORWARD)} {log['to']} (Action: {log['action']})"):
                col_sent, col_recv = st.columns(2)
                with col_sent:
                    st.markdown(f"{icon_md(OUTBOX)} **Outgoing A2A/1.0 Message:**")
                    st.json({
                        "protocol": "A2A/1.0",
                        "sender": log["from"],
                        "recipient": log["to"],
                        "action": log["action"],
                        "data": log["data_sent"]
                    })
                with col_recv:
                    st.markdown(f"{icon_md(INBOX)} **Received Response Payload:**")
                    st.json(log["response_received"])

