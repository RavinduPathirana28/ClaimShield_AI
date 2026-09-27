import React from 'react';
import { useAuth } from '../context/AuthContext';
import * as api from '../services/api';

export default function PlansPage({ onOpenCheckout }) {
  const { user, profile, isPro, token, refreshProfile } = useAuth();

  const handleDowngrade = async () => {
    if (!window.confirm('Are you sure you want to downgrade to the Free Plan?')) return;
    try {
      await api.changePlan(token, 'user');
      await refreshProfile();
      alert('Successfully switched to the Free Plan.');
    } catch (e) {
      alert(`Failed to downgrade: ${e.message}`);
    }
  };

  return (
    <div style={{ maxWidth: '1040px', margin: '0 auto', padding: '24px 20px 80px' }}>
      {/* Title */}
      <div style={{ textAlign: 'center', marginBottom: '36px' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: '800', color: '#0F172A', margin: '0 0 8px 0' }}>
          Subscription & Commercialization Plans
        </h2>
        <p style={{ color: '#64748B', fontSize: '0.96rem', margin: 0 }}>
          Manage your account plan, upgrade to unlimited verification, and view quota entitlements.
        </p>
      </div>

      {/* Plans Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', marginBottom: '48px' }}>
        {/* Free Plan */}
        <div className="plan-card" style={{
          padding: '32px',
          border: !isPro ? '2px solid #059669' : '1px solid rgba(226, 232, 240, 0.8)',
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between'
        }}>
          {!isPro && (
            <div style={{
              position: 'absolute',
              top: '-12px',
              right: '24px',
              background: '#059669',
              color: 'white',
              padding: '4px 12px',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: '800'
            }}>
              Current Active Plan
            </div>
          )}
          <div>
            <h3 style={{ margin: '0 0 6px 0', fontSize: '1.3rem', color: '#0F172A' }}>Free Plan</h3>
            <div style={{ fontSize: '2.5rem', fontWeight: '900', color: '#0F172A', marginBottom: '8px' }}>
              $0
            </div>
            <p style={{ color: '#64748B', fontSize: '0.86rem', marginBottom: '20px' }}>
              Essential tools for individual fact-checkers
            </p>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 24px 0', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: '#334155' }}>
                <span className="material-symbols-rounded" style={{ color: '#059669', fontSize: '1.2rem' }}>check</span>
                <span><strong>3 verification tokens</strong> token bucket capacity</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: '#334155' }}>
                <span className="material-symbols-rounded" style={{ color: '#059669', fontSize: '1.2rem' }}>check</span>
                <span><strong>Displays only 2 resources</strong> per claim</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: '#334155' }}>
                <span className="material-symbols-rounded" style={{ color: '#059669', fontSize: '1.2rem' }}>check</span>
                <span>Refills 3 tokens / hour</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: '#334155' }}>
                <span className="material-symbols-rounded" style={{ color: '#059669', fontSize: '1.2rem' }}>check</span>
                <span>Standard NLP & FAISS vector search</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: '#334155' }}>
                <span className="material-symbols-rounded" style={{ color: '#059669', fontSize: '1.2rem' }}>check</span>
                <span>Encrypted audit logging</span>
              </li>
            </ul>
          </div>

          {!isPro ? (
            <button
              disabled
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '12px',
                border: '1px solid #CBD5E1',
                background: '#F1F5F9',
                color: '#64748B',
                fontWeight: '700',
                cursor: 'default'
              }}
            >
              Current Active Plan
            </button>
          ) : (
            <button
              onClick={handleDowngrade}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '12px',
                border: '1px solid #CBD5E1',
                background: '#FFFFFF',
                color: '#334155',
                fontWeight: '700',
                cursor: 'pointer'
              }}
            >
              Downgrade to Free
            </button>
          )}
        </div>

        {/* Pro Plan */}
        <div className="plan-card" style={{
          padding: '32px',
          border: isPro ? '2px solid #059669' : '2px solid #4F46E5',
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 12px 35px -8px rgba(79, 70, 229, 0.25)'
        }}>
          <div style={{
            position: 'absolute',
            top: '-12px',
            right: '24px',
            background: isPro ? '#059669' : '#4F46E5',
            color: 'white',
            padding: '4px 12px',
            borderRadius: '9999px',
            fontSize: '0.75rem',
            fontWeight: '800'
          }}>
            {isPro ? 'Current Active Plan' : 'Popular'}
          </div>
          <div>
            <h3 style={{ margin: '0 0 6px 0', fontSize: '1.3rem', color: '#4F46E5' }}>Pro Plan</h3>
            <div style={{ fontSize: '2.5rem', fontWeight: '900', color: '#4F46E5', marginBottom: '8px' }}>
              $19 <span style={{ fontSize: '1rem', color: '#64748B', fontWeight: '500' }}>/ month</span>
            </div>
            <p style={{ color: '#64748B', fontSize: '0.86rem', marginBottom: '20px' }}>
              For journalists, researchers & media professionals
            </p>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 24px 0', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: '#334155' }}>
                <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '1.2rem' }}>check_circle</span>
                <span><strong>Unlimited</strong> verification checks (Rate limits bypassed)</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: '#334155' }}>
                <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '1.2rem' }}>check_circle</span>
                <span><strong>Displays at least 3 & up to 5 max</strong> resources</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: '#334155' }}>
                <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '1.2rem' }}>check_circle</span>
                <span>Priority LLM execution queue</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: '#334155' }}>
                <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '1.2rem' }}>check_circle</span>
                <span>Multi-Agent Persona Debate & LangGraph</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: '#334155' }}>
                <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '1.2rem' }}>check_circle</span>
                <span>Downloadable PDF verification certificates</span>
              </li>
            </ul>
          </div>

          {isPro ? (
            <button
              disabled
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '12px',
                border: '1px solid #CBD5E1',
                background: '#F1F5F9',
                color: '#64748B',
                fontWeight: '700',
                cursor: 'default'
              }}
            >
              Current Active Plan
            </button>
          ) : (
            <button
              onClick={onOpenCheckout}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '12px',
                border: 'none',
                background: 'linear-gradient(135deg, #4F46E5 0%, #3730A3 100%)',
                color: '#FFFFFF',
                fontWeight: '700',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(79, 70, 229, 0.3)'
              }}
            >
              Upgrade to Pro ($19/mo)
            </button>
          )}
        </div>
      </div>

      {/* Plan Feature Matrix Table */}
      <div className="glass-card" style={{ padding: '28px' }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '1.2rem', color: '#0F172A', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="material-symbols-rounded" style={{ color: '#4F46E5' }}>bar_chart</span>
          <span>Commercialization Feature Comparison Matrix</span>
        </h3>

        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #E2E8F0' }}>
              <th style={{ padding: '12px 16px', color: '#334155' }}>Feature</th>
              <th style={{ padding: '12px 16px', color: '#334155' }}>Free Plan</th>
              <th style={{ padding: '12px 16px', color: '#4F46E5' }}>Pro Plan</th>
            </tr>
          </thead>
          <tbody>
            {[
              ['Token Bucket Capacity', '3 tokens', 'Unlimited (Bypassed)'],
              ['Evidence Resources Displayed', '2 resources max', '3 to 5 resources'],
              ['Refill Rate', '3 tokens / hour', 'Continuous zero-throttle'],
              ['Vector Semantic Search (FAISS)', 'Included', 'Included (Priority)'],
              ['Multi-LLM Consensus', 'Included', 'Included'],
              ['LangGraph & AutoGen Bridge', 'Limited', 'Full Access'],
              ['Downloadable PDF Report', 'Standard', 'Certified High-Res PDF']
            ].map(([feat, freeVal, proVal], idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid #F1F5F9' }}>
                <td style={{ padding: '12px 16px', color: '#1E293B', fontWeight: '500' }}>{feat}</td>
                <td style={{ padding: '12px 16px', color: '#64748B' }}>{freeVal}</td>
                <td style={{ padding: '12px 16px', color: '#4F46E5', fontWeight: '700' }}>{proVal}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
