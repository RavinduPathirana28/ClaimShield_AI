import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import * as api from '../services/api';
import PipelineLoader from '../components/PipelineLoader';
import VerdictCard from '../components/VerdictCard';
import EvidenceList from '../components/EvidenceList';
import Recommendations from '../components/Recommendations';

const SAMPLES = [
  { label: 'What is AI?', query: 'What is Artificial Intelligence?', icon: 'smart_toy' },
  { label: 'iPhone 18 in 2026?', query: 'Apple will launch the iPhone 18 in July 2026.', icon: 'smartphone' },
  { label: 'Why is sky blue?', query: 'Why is the sky blue?', icon: 'nightlight' },
  { label: 'Is coffee healthy?', query: 'Is drinking coffee good for heart health?', icon: 'coffee' },
];

export default function DashboardPage({ engineMode = 'Standard A2A Protocol', onUpgradeClick, onNewAgentLogs }) {
  const { token, refreshProfile } = useAuth();
  const [claim, setClaim] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [currentLogs, setCurrentLogs] = useState([]);

  const handleVerify = async (textToVerify = null) => {
    const query = (textToVerify !== null ? textToVerify : claim).trim();
    if (!query) {
      setError('Please enter a claim or question to verify.');
      return;
    }

    if (textToVerify !== null) {
      setClaim(textToVerify);
    }

    setError('');
    setLoading(true);
    setResult(null);

    try {
      const response = await api.verifyClaim(token, query, engineMode);
      setResult(response.result);
      if (response.agent_logs) {
        setCurrentLogs(response.agent_logs);
        if (onNewAgentLogs) onNewAgentLogs(response.agent_logs);
      }
      await refreshProfile();
    } catch (err) {
      setError(err.message || 'Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '16px 20px 80px' }}>
      {/* Title */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: '800', color: '#0F172A', margin: '0 0 6px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '2rem' }}>search</span>
          <span>Ask a Question or Verify a Claim</span>
        </h2>
        <p style={{ margin: 0, color: '#64748B', fontSize: '0.94rem' }}>
          Type any general question or factual statement below. Our multi-agent AI system will evaluate it and provide a realistic, easy-to-understand explanation.
        </p>
      </div>

      {/* Preset Samples */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ fontSize: '0.8rem', fontWeight: '700', color: '#64748B', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          Sample Questions & Claims:
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {SAMPLES.map((s, idx) => (
            <button
              key={idx}
              onClick={() => { setClaim(s.query); }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                background: 'rgba(255, 255, 255, 0.85)',
                border: '1px solid #CBD5E1',
                padding: '7px 14px',
                borderRadius: '9999px',
                fontSize: '0.82rem',
                color: '#334155',
                cursor: 'pointer',
                fontWeight: '500',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#4F46E5';
                e.currentTarget.style.color = '#4F46E5';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#CBD5E1';
                e.currentTarget.style.color = '#334155';
              }}
            >
              <span className="material-symbols-rounded" style={{ fontSize: '1.05rem' }}>{s.icon}</span>
              <span>{s.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Input Form Box */}
      <div className="glass-card" style={{ padding: '24px', marginBottom: '24px' }}>
        <textarea
          rows={3}
          value={claim}
          onChange={(e) => setClaim(e.target.value)}
          placeholder="e.g. 'What is quantum computing?', 'Why is the sky blue?', or 'Apple will launch iPhone 18 in July 2026'"
          style={{
            width: '100%',
            padding: '14px 16px',
            borderRadius: '12px',
            border: '1px solid #CBD5E1',
            fontSize: '1rem',
            outline: 'none',
            resize: 'vertical',
            boxSizing: 'border-box',
            fontFamily: 'inherit',
            lineHeight: '1.5'
          }}
        />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ fontSize: '0.82rem', color: '#64748B' }}>
            Supports general knowledge questions as well as factual news verification.
          </div>

          {/* Submit Button */}
          <button
            onClick={() => handleVerify()}
            disabled={loading}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 28px',
              borderRadius: '12px',
              border: 'none',
              background: 'linear-gradient(135deg, #4F46E5 0%, #3730A3 100%)',
              color: 'white',
              fontWeight: '700',
              fontSize: '0.98rem',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
              boxShadow: '0 4px 14px rgba(79, 70, 229, 0.3)'
            }}
          >
            <span className="material-symbols-rounded">shield</span>
            <span>{loading ? 'Verifying with Multi-Agent Pipeline...' : 'Run ClaimShield AI'}</span>
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#DC2626',
          borderRadius: '12px',
          padding: '14px 18px',
          fontSize: '0.92rem',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <span className="material-symbols-rounded">error</span>
          <div>{error}</div>
        </div>
      )}

      {/* Pipeline Loader */}
      {loading && <PipelineLoader />}

      {/* Verification Result */}
      {result && (
        <>
          <VerdictCard result={result} />
          <EvidenceList result={result} onUpgradeClick={onUpgradeClick} />
          <Recommendations recommendations={result.recommendations} onSelectClaim={(c) => handleVerify(c)} />

          {/* Collapsible A2A Protocol Envelopes */}
          {currentLogs.length > 0 && (
            <div className="glass-card" style={{ padding: '20px', marginTop: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <span className="material-symbols-rounded" style={{ color: '#4F46E5' }}>settings</span>
                <h4 style={{ margin: 0, fontSize: '1rem', color: '#0F172A', fontWeight: '700' }}>
                  A2A/1.0 Agent Communication Messages ({currentLogs.length} envelopes)
                </h4>
              </div>
              <div style={{ fontSize: '0.8rem', color: '#64748B', marginBottom: '12px' }}>
                Inspect inter-agent messages fired between Orchestrator, Security, NLP, and Retrieval agents during this run.
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {currentLogs.map((log, i) => (
                  <div key={i} style={{
                    background: '#F8FAFC',
                    border: '1px solid #E2E8F0',
                    borderRadius: '8px',
                    padding: '8px 12px',
                    fontSize: '0.8rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <strong style={{ color: '#4F46E5' }}>{log.from}</strong> → <strong style={{ color: '#059669' }}>{log.to}</strong>
                      <span style={{ color: '#64748B', marginLeft: '8px' }}>({log.action})</span>
                    </div>
                    <span style={{ fontFamily: 'monospace', color: '#94A3B8', fontSize: '0.74rem' }}>{log.timestamp}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
