import React from 'react';

export const PLANS = {
  free: {
    id: 'free',
    role: 'user',
    name: 'Free Plan',
    price: 0,
    priceLabel: '$0',
    tagline: 'Essential tools for individual fact-checkers',
    features: [
      '**3 verification tokens** capacity',
      '**Displays only 2 resources** per claim',
      'Refills 3 tokens / hour',
      'Standard NLP & spaCy extraction',
      'FAISS vector similarity search',
      'Encrypted audit logging',
    ],
  },
  pro: {
    id: 'pro',
    role: 'pro',
    name: 'Pro Plan',
    price: 19.0,
    priceLabel: '$19',
    tagline: 'For freelance reporters, researchers and journalists',
    popular: true,
    features: [
      '**Unlimited** verification checks',
      '**At least 3 (if available) & up to 5** resources displayed',
      'Bypassed token bucket rate limits',
      'Priority LLM execution queue',
      'Multi-Agent Persona Debate & LangGraph',
    ],
  },
};

export const PRO_FEATURES_SHORT = [
  'Unlimited claim checks',
  '3–5 cited resources per verdict',
  'Priority LLM queue',
];

export const PLAN_MATRIX = [
  ['Verification Quota', '3 Checks / Bucket (3/hr refill)', 'Unlimited'],
  ['Resources Displayed', 'Only 2 Resources', 'At least 3 (if available) · 5 Maximum'],
  ['Rate Limiter Status', 'Token-Bucket Active (3 capacity)', 'Bypassed (Zero Throttles)'],
  ['LLM Verification Models', 'Standard Heuristic + LLM', 'Priority Gemini / Groq Queue'],
  ['FAISS Vector Search & Retrieval', 'Top 3 Articles retrieved (2 displayed)', 'Top 5 Articles retrieved (3–5 displayed)'],
  ['Persona Debate (FactChecker → Critic → Consensus)', 'Standard Sequential', 'Full Consensus Debate'],
  ['LangGraph Stateful Graph', 'Standard Graph', 'Full Graph Execution'],
  ['Audit Trail Encryption', 'Fernet AES-128-CBC', 'Fernet AES-128-CBC + Telemetry'],
];

export function renderFeature(text) {
  const parts = text.split(/\*\*(.+?)\*\*/g);
  return parts.map((part, i) =>
    i % 2 === 1 ? (
      <strong key={i} className="font-semibold text-foreground">
        {part}
      </strong>
    ) : (
      <React.Fragment key={i}>{part}</React.Fragment>
    )
  );
}
