import React, { useState, useEffect } from 'react';

const STEPS = [
  { icon: 'shield', title: 'Security & Sanitization', detail: 'Token-bucket rate limits & prompt injection filtering' },
  { icon: 'biotech', title: 'NLP Extraction', detail: 'spaCy entity extraction & keyword normalization' },
  { icon: 'search', title: 'Vector Retrieval', detail: 'FAISS semantic search across the verified corpus' },
  { icon: 'menu_book', title: 'Context & Summaries', detail: 'Extractive evidence summarization' },
  { icon: 'handshake', title: 'Multi-LLM Consensus', detail: 'Groq (Llama-3.3-70b) & Google Gemini validation' },
  { icon: 'fact_check', title: 'Verdict & Encrypted Audit', detail: 'Final scoring, citation mapping & audit logging' },
];

export default function PipelineLoader() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 1200);
    return () => clearInterval(timer);
  }, []);

  const pct = Math.round(((currentStep + 1) / STEPS.length) * 100);

  return (
    <div className="cs-run-loader" style={{ margin: '24px 0' }}>
      <div className="cs-run-head">
        <span className="cs-run-dot" />
        <span style={{ fontWeight: '700', color: '#0F172A' }}>
          Multi-Agent Verification In Progress
        </span>
        <span className="cs-run-tag">{pct}%</span>
      </div>

      <div className="cs-steps" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '8px', margin: '16px 0' }}>
        {STEPS.map((step, idx) => {
          const isDone = idx < currentStep;
          const isActive = idx === currentStep;

          return (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                borderRadius: '10px',
                background: isActive ? 'rgba(79, 70, 229, 0.1)' : isDone ? 'rgba(16, 185, 129, 0.08)' : 'rgba(241, 245, 249, 0.6)',
                border: `1px solid ${isActive ? '#4F46E5' : isDone ? '#10B981' : '#E2E8F0'}`,
                transition: 'all 0.3s ease'
              }}
            >
              <span
                className="material-symbols-rounded"
                style={{
                  fontSize: '1.2rem',
                  color: isActive ? '#4F46E5' : isDone ? '#10B981' : '#94A3B8'
                }}
              >
                {isDone ? 'check_circle' : step.icon}
              </span>
              <div style={{ overflow: 'hidden' }}>
                <div style={{
                  fontSize: '0.8rem',
                  fontWeight: isActive || isDone ? '700' : '500',
                  color: isActive ? '#4F46E5' : isDone ? '#0F172A' : '#64748B',
                  whiteSpace: 'nowrap',
                  textOverflow: 'ellipsis',
                  overflow: 'hidden'
                }}>
                  {step.title}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="cs-bar" style={{ height: '6px', background: '#E2E8F0', borderRadius: '4px', overflow: 'hidden' }}>
        <div
          className="cs-bar-fill"
          style={{
            width: `${pct}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #4F46E5, #06B6D4)',
            transition: 'width 0.4s ease'
          }}
        />
      </div>

      <div className="cs-run-detail" style={{ marginTop: '10px', fontSize: '0.82rem', color: '#64748B', textAlign: 'center' }}>
        Active: <strong style={{ color: '#4F46E5' }}>{STEPS[currentStep].title}</strong> — {STEPS[currentStep].detail}
      </div>
    </div>
  );
}
