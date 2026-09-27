import React from 'react';
import { useAuth } from '../context/AuthContext';

export default function EvidenceList({ result, onUpgradeClick }) {
  const { isPro } = useAuth();
  if (!result) return null;

  const displayArticles = result.display_articles || result.articles || [];
  const totalFound = result.total_resources_found || displayArticles.length;
  const citations = result.citations || [];

  if (displayArticles.length === 0) return null;

  return (
    <div style={{ marginTop: '28px', marginBottom: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#0F172A', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="material-symbols-rounded" style={{ color: '#4F46E5' }}>search</span>
            <span>Retrieved Evidence & Live Citations</span>
          </h3>
          <div style={{ fontSize: '0.82rem', color: '#64748B', marginTop: '2px' }}>
            Showing <strong>{displayArticles.length}</strong> of <strong>{totalFound}</strong> retrieved resources for your plan.
          </div>
        </div>

        {!isPro && totalFound > 2 && (
          <button
            onClick={onUpgradeClick}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.1), rgba(124, 58, 237, 0.15))',
              border: '1px solid rgba(79, 70, 229, 0.35)',
              color: '#4F46E5',
              padding: '6px 14px',
              borderRadius: '9999px',
              fontSize: '0.82rem',
              fontWeight: '700',
              cursor: 'pointer'
            }}
          >
            <span className="material-symbols-rounded" style={{ fontSize: '1.1rem' }}>bolt</span>
            <span>Upgrade to Pro to view all 3–5 resources</span>
          </button>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {displayArticles.map((article, idx) => {
          const score = typeof article.score === 'number' ? Math.round(article.score * 100) : null;
          return (
            <div
              key={idx}
              className="glass-card"
              style={{
                padding: '18px 20px',
                borderLeft: '4px solid #4F46E5',
                background: 'rgba(255, 255, 255, 0.85)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', marginBottom: '8px' }}>
                <h4 style={{ margin: 0, fontSize: '0.98rem', color: '#0F172A', fontWeight: '700' }}>
                  {article.title || `Evidence Source #${idx + 1}`}
                </h4>
                {score !== null && (
                  <span style={{
                    fontSize: '0.74rem',
                    fontWeight: '700',
                    color: '#4F46E5',
                    background: 'rgba(79, 70, 229, 0.1)',
                    padding: '3px 8px',
                    borderRadius: '6px',
                    whiteSpace: 'nowrap'
                  }}>
                    {score}% Match
                  </span>
                )}
              </div>

              {article.snippet && (
                <p style={{ margin: '0 0 10px 0', fontSize: '0.86rem', color: '#475569', lineHeight: '1.55' }}>
                  "{article.snippet}"
                </p>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.76rem', color: '#94A3B8' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span className="material-symbols-rounded" style={{ fontSize: '0.95rem' }}>link</span>
                  <span>Source: {article.source || 'Verified Corpus'}</span>
                </span>
                {article.url && (
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: '#4F46E5', textDecoration: 'none', fontWeight: '600' }}
                  >
                    View Original ↗
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
