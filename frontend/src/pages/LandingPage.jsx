import React from 'react';

export default function LandingPage({ onGetStarted, onSelectPlan }) {
  return (
    <div style={{ maxWidth: '1160px', margin: '0 auto', padding: '30px 20px 80px' }}>
      {/* Hero Section */}
      <section className="hero-section" style={{ textAlign: 'center', padding: '50px 0 40px' }}>
        <div className="hero-badge" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
          <span className="hero-badge-dot" />
          <span>Now Live — Multi-Agent AI System</span>
        </div>

        <h1 className="hero-title" style={{
          fontSize: '3.4rem',
          fontWeight: '900',
          letterSpacing: '-0.035em',
          lineHeight: '1.15',
          margin: '0 auto 18px',
          maxWidth: '880px',
          color: '#0F172A'
        }}>
          Defend Truth with <span style={{
            background: 'linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>Autonomous Multi-Agent</span> Intelligence
        </h1>

        <p style={{
          fontSize: '1.15rem',
          color: '#475569',
          maxWidth: '720px',
          margin: '0 auto 32px',
          lineHeight: '1.65'
        }}>
          ClaimShield AI orchestrates 5 specialized AI agents, vector RAG retrieval, and multi-LLM consensus
          to deliver transparent, evidence-backed verdicts instantly.
        </p>

        {/* Hero CTA Button */}
        <div>
          <button
            className="hero-animated-wave-btn"
            onClick={onGetStarted}
            style={{
              background: 'linear-gradient(135deg, #4F46E5 0%, #3730A3 100%)',
              color: 'white',
              border: 'none',
              padding: '16px 36px',
              fontSize: '1.1rem',
              fontWeight: '700',
              borderRadius: '16px',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '10px',
              boxShadow: '0 10px 25px -5px rgba(79, 70, 229, 0.4)'
            }}
          >
            <span className="material-symbols-rounded">shield</span>
            <span>Start Verifying Claims</span>
            <span className="material-symbols-rounded">arrow_forward</span>
          </button>
        </div>
      </section>

      {/* Stats Row */}
      <section style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        margin: '40px 0 60px'
      }}>
        {[
          { num: '98.4%', label: 'Fact-Check Accuracy' },
          { num: '5 Agents', label: 'Sequential Pipeline' },
          { num: '2.1s', label: 'Average Response Time' },
          { num: '100%', label: 'Cryptographic Audit Trail' }
        ].map((stat, i) => (
          <div key={i} className="glass-card" style={{ textAlign: 'center', padding: '24px 16px' }}>
            <div style={{ fontSize: '2rem', fontWeight: '800', color: '#4F46E5', marginBottom: '4px' }}>
              {stat.num}
            </div>
            <div style={{ fontSize: '0.85rem', color: '#64748B', fontWeight: '600' }}>
              {stat.label}
            </div>
          </div>
        ))}
      </section>

      {/* 5-Agent Pipeline Visual */}
      <section style={{ margin: '60px 0' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div className="section-eyebrow">How It Works</div>
          <h2 className="section-title">The 5-Agent Verification Pipeline</h2>
          <div className="section-desc">Each statement flows sequentially through our specialized agent network.</div>
        </div>

        <div className="glass-card" style={{ padding: '36px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-around', flexWrap: 'wrap', gap: '16px' }}>
            {[
              { icon: 'key', name: 'Security Agent', color: '#EF4444' },
              { icon: 'biotech', name: 'NLP Agent', color: '#38BDF8' },
              { icon: 'search', name: 'Retrieval Agent', color: '#F59E0B' },
              { icon: 'balance', name: 'Verification Agent', color: '#A855F7' },
              { icon: 'lightbulb', name: 'Explainer Agent', color: '#10B981' },
              { icon: 'check_circle', name: 'Verdict & Audit', color: '#4F46E5' }
            ].map((ag, i, arr) => (
              <React.Fragment key={i}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    width: '60px',
                    height: '60px',
                    borderRadius: '16px',
                    background: `${ag.color}15`,
                    border: `2px solid ${ag.color}`,
                    color: ag.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 8px',
                    boxShadow: `0 8px 20px ${ag.color}25`
                  }}>
                    <span className="material-symbols-rounded" style={{ fontSize: '1.8rem' }}>{ag.icon}</span>
                  </div>
                  <div style={{ fontWeight: '700', fontSize: '0.86rem', color: '#1E293B' }}>{ag.name}</div>
                </div>
                {i < arr.length - 1 && (
                  <span className="material-symbols-rounded" style={{ color: '#CBD5E1', fontSize: '1.5rem' }}>
                    arrow_forward
                  </span>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Comparison (2-Tier: Free vs Pro) */}
      <section style={{ margin: '70px 0' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div className="section-eyebrow">Pricing Plans</div>
          <h2 className="section-title">Transparent Commercialization Plans</h2>
          <div className="section-desc">Get started with Free or upgrade to Pro for expanded evidence depth.</div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
          {/* Free Plan */}
          <div className="plan-card" style={{ padding: '32px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '1.3rem', color: '#0F172A' }}>Free Plan</h4>
              <div style={{ fontSize: '2.5rem', fontWeight: '900', color: '#0F172A', marginBottom: '8px' }}>
                $0
              </div>
              <p style={{ color: '#64748B', fontSize: '0.88rem', marginBottom: '20px' }}>
                Essential fact-checking tools for individual users
              </p>
              <ul className="plan-feature-list" style={{ listStyle: 'none', padding: 0, margin: '0 0 24px 0', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#334155' }}>
                  <span className="material-symbols-rounded" style={{ color: '#059669', fontSize: '1.2rem' }}>check</span>
                  <span><strong>3 requests</strong> token bucket capacity</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#334155' }}>
                  <span className="material-symbols-rounded" style={{ color: '#059669', fontSize: '1.2rem' }}>check</span>
                  <span><strong>Displays only 2 resources</strong> per claim</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#334155' }}>
                  <span className="material-symbols-rounded" style={{ color: '#059669', fontSize: '1.2rem' }}>check</span>
                  <span>Refills 3 tokens / hour</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#334155' }}>
                  <span className="material-symbols-rounded" style={{ color: '#059669', fontSize: '1.2rem' }}>check</span>
                  <span>Standard NLP & FAISS vector search</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#334155' }}>
                  <span className="material-symbols-rounded" style={{ color: '#059669', fontSize: '1.2rem' }}>check</span>
                  <span>Encrypted audit logging</span>
                </li>
              </ul>
            </div>
            <button
              onClick={() => onSelectPlan('free')}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '12px',
                border: '1px solid #CBD5E1',
                background: '#FFFFFF',
                color: '#1E293B',
                fontWeight: '700',
                cursor: 'pointer'
              }}
            >
              Get Started Free
            </button>
          </div>

          {/* Pro Plan */}
          <div className="plan-card" style={{
            padding: '32px',
            border: '2px solid #4F46E5',
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: '0 12px 35px -8px rgba(79, 70, 229, 0.25)'
          }}>
            <div className="plan-popular-tag" style={{
              position: 'absolute',
              top: '-12px',
              right: '24px',
              background: '#4F46E5',
              color: 'white',
              padding: '4px 12px',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: '800',
              textTransform: 'uppercase'
            }}>
              Popular
            </div>
            <div>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '1.3rem', color: '#4F46E5' }}>Pro Plan</h4>
              <div style={{ fontSize: '2.5rem', fontWeight: '900', color: '#4F46E5', marginBottom: '8px' }}>
                $19 <span style={{ fontSize: '1rem', color: '#64748B', fontWeight: '500' }}>/ month</span>
              </div>
              <p style={{ color: '#64748B', fontSize: '0.88rem', marginBottom: '20px' }}>
                For journalists, researchers & media professionals
              </p>
              <ul className="plan-feature-list" style={{ listStyle: 'none', padding: 0, margin: '0 0 24px 0', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#334155' }}>
                  <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '1.2rem' }}>check_circle</span>
                  <span><strong>Unlimited</strong> claim checks (Zero throttles)</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#334155' }}>
                  <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '1.2rem' }}>check_circle</span>
                  <span><strong>Displays at least 3 & up to 5 max</strong> resources</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#334155' }}>
                  <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '1.2rem' }}>check_circle</span>
                  <span>Priority LLM reasoning queue</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#334155' }}>
                  <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '1.2rem' }}>check_circle</span>
                  <span>Multi-Agent Persona Debate & LangGraph</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#334155' }}>
                  <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '1.2rem' }}>check_circle</span>
                  <span>Downloadable PDF verification certificates</span>
                </li>
              </ul>
            </div>
            <button
              onClick={() => onSelectPlan('pro')}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '12px',
                border: 'none',
                background: 'linear-gradient(135deg, #4F46E5, #3730A3)',
                color: '#FFFFFF',
                fontWeight: '700',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(79, 70, 229, 0.3)'
              }}
            >
              Upgrade to Pro ($19/mo)
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
