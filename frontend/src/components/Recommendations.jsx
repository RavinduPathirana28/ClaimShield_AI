import React from 'react';

export default function Recommendations({ recommendations, onSelectClaim }) {
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <div style={{ marginTop: '24px', marginBottom: '28px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <span className="material-symbols-rounded" style={{ color: '#0284C7' }}>explore</span>
        <h4 style={{ margin: 0, fontSize: '1.05rem', color: '#0F172A', fontWeight: '700' }}>
          Related Claims & Inquiries
        </h4>
      </div>
      <p style={{ margin: '0 0 14px 0', fontSize: '0.84rem', color: '#64748B' }}>
        Similar topics verified by ClaimShield AI. Click any statement below to analyze it instantly:
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
        {recommendations.map((rec, idx) => {
          const claimText = typeof rec === 'string' ? rec : (rec.claim || rec.title || '');
          const score = typeof rec === 'object' && rec.similarity ? Math.round(rec.similarity * 100) : null;

          return (
            <div
              key={idx}
              className="glass-card"
              onClick={() => onSelectClaim(claimText)}
              style={{
                padding: '14px 16px',
                cursor: 'pointer',
                border: '1px solid rgba(226, 232, 240, 0.9)',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '10px'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#4F46E5';
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 6px 16px rgba(79,70,229,0.12)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'rgba(226, 232, 240, 0.9)';
                e.currentTarget.style.transform = 'none';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={{ fontSize: '0.88rem', color: '#1E293B', fontWeight: '500', lineHeight: '1.4' }}>
                {claimText}
              </div>
              <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '1.1rem', flexShrink: 0 }}>
                arrow_forward
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
