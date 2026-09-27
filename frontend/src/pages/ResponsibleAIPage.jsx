import React from 'react';

const PILLARS = [
  {
    icon: 'search',
    title: 'Transparency & Auditability',
    badge: 'Fully Traceable',
    badgeColor: '#059669',
    badgeBg: 'rgba(16, 185, 129, 0.15)',
    border: '#059669',
    desc: 'Every verification result provides full source attribution, cosine similarity metrics, and an immutable AES-256 encrypted audit trail for regulatory compliance.'
  },
  {
    icon: 'balance',
    title: 'Algorithmic Fairness',
    badge: 'Uniform Verification',
    badgeColor: '#D97706',
    badgeBg: 'rgba(245, 158, 11, 0.15)',
    border: '#D97706',
    desc: 'Our semantic pipeline evaluates statements without user demographic profiling, ensuring objective verdicts across scientific, historical, and sociopolitical topics.'
  },
  {
    icon: 'psychology',
    title: 'Grounding & Bias Mitigation',
    badge: 'Multi-LLM Consensus',
    badgeColor: '#4F46E5',
    badgeBg: 'rgba(79, 70, 229, 0.15)',
    border: '#4F46E5',
    desc: 'Dual-model consensus (Groq Llama-3.3-70b + Google Gemini-2.5) strictly penalizes ungrounded hallucinations, requiring retrieved factual documents before issuing positive verdicts.'
  },
  {
    icon: 'lightbulb',
    title: 'Multi-Layer Explainability',
    badge: 'Transparent Rationale',
    badgeColor: '#7C3AED',
    badgeBg: 'rgba(124, 58, 237, 0.15)',
    border: '#7C3AED',
    desc: 'Provides plain-language explanations, specific cited article snippets, and confidence scores so end-users can independently verify reasoning.'
  },
  {
    icon: 'lock',
    title: 'Cryptographic Security',
    badge: 'Defense in Depth',
    badgeColor: '#DC2626',
    badgeBg: 'rgba(239, 68, 68, 0.15)',
    border: '#DC2626',
    desc: 'Token-bucket rate limiting against DDoS and prompt injection sanitization protect backend reasoning infrastructure.'
  },
  {
    icon: 'person',
    title: 'User Data Rights & Privacy',
    badge: 'Privacy Protected',
    badgeColor: '#0284C7',
    badgeBg: 'rgba(2, 132, 199, 0.15)',
    border: '#0284C7',
    desc: 'User queries are processed transiently and personal audit records are encrypted. We never sell or train public foundation models on private user submissions.'
  }
];

export default function ResponsibleAIPage() {
  return (
    <div style={{ maxWidth: '1060px', margin: '0 auto', padding: '24px 20px 80px' }}>
      <div style={{ textAlign: 'center', marginBottom: '36px' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: '800', color: '#0F172A', margin: '0 0 8px 0', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
          <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '2rem' }}>smart_toy</span>
          <span>Responsible AI, Ethics & Governance</span>
        </h2>
        <p style={{ color: '#64748B', fontSize: '0.96rem', margin: 0, maxWidth: '720px', marginLeft: 'auto', marginRight: 'auto' }}>
          ClaimShield AI is architected with Responsible AI principles at its foundation — guaranteeing fairness, explainability, safety, and verifiable evidence.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '36px' }}>
        {PILLARS.map((p, idx) => (
          <div
            key={idx}
            className="glass-card"
            style={{
              padding: '24px',
              borderLeft: `5px solid ${p.border}`,
              background: 'rgba(255, 255, 255, 0.88)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
              <h3 style={{ margin: 0, fontSize: '1.05rem', color: p.border, display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="material-symbols-rounded">{p.icon}</span>
                <span>{p.title}</span>
              </h3>
              <span style={{
                background: p.badgeBg,
                color: p.badgeColor,
                padding: '4px 10px',
                borderRadius: '9999px',
                fontSize: '0.74rem',
                fontWeight: '700'
              }}>
                {p.badge}
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '0.88rem', color: '#475569', lineHeight: '1.6' }}>
              {p.desc}
            </p>
          </div>
        ))}
      </div>

      {/* Global commitment banner */}
      <div className="glass-card" style={{
        padding: '32px 24px',
        textAlign: 'center',
        background: 'linear-gradient(135deg, rgba(5, 150, 105, 0.08), rgba(16, 185, 129, 0.12))',
        border: '1px solid rgba(5, 150, 105, 0.3)'
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '46px',
          height: '46px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #059669, #047857)',
          color: 'white',
          marginBottom: '10px'
        }}>
          <span className="material-symbols-rounded">public</span>
        </div>
        <h3 style={{ color: '#065F46', fontSize: '1.25rem', margin: '0 0 6px 0' }}>
          Global Responsible AI Commitment
        </h3>
        <p style={{ color: '#047857', fontSize: '0.92rem', maxWidth: '760px', margin: '0 auto', lineHeight: '1.6' }}>
          We commit to upholding open standards in computational truth verification. Every piece of retrieved
          evidence is cited with transparent scoring, multi-model consensus, and human-in-the-loop oversight.
        </p>
      </div>
    </div>
  );
}
