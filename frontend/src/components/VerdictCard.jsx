import React, { useState } from 'react';
import * as api from '../services/api';

const VERDICT_CONFIG = {
  Supported: {
    color: '#059669',
    bg: 'rgba(16, 185, 129, 0.12)',
    border: 'rgba(16, 185, 129, 0.35)',
    icon: 'check_circle',
    label: 'Supported (Verified True)'
  },
  Contradicted: {
    color: '#DC2626',
    bg: 'rgba(239, 68, 68, 0.12)',
    border: 'rgba(239, 68, 68, 0.35)',
    icon: 'cancel',
    label: 'Contradicted (Debunked / False)'
  },
  Answered: {
    color: '#0284C7',
    bg: 'rgba(2, 132, 199, 0.12)',
    border: 'rgba(2, 132, 199, 0.35)',
    icon: 'lightbulb',
    label: 'Answered (Direct Answer)'
  },
  'General Info': {
    color: '#0284C7',
    bg: 'rgba(2, 132, 199, 0.12)',
    border: 'rgba(2, 132, 199, 0.35)',
    icon: 'lightbulb',
    label: 'Answered (Direct Answer)'
  },
  Unverified: {
    color: '#D97706',
    bg: 'rgba(245, 158, 11, 0.12)',
    border: 'rgba(245, 158, 11, 0.35)',
    icon: 'warning',
    label: 'Unverified (Insufficient Evidence)'
  }
};

export default function VerdictCard({ result, onExportPdf }) {
  const [downloading, setDownloading] = useState(false);

  if (!result) return null;

  const verdict = result.verdict || 'Unclear';
  const conf = Math.round((result.confidence || 0) * 100);
  const cfg = VERDICT_CONFIG[verdict] || {
    color: '#64748B',
    bg: 'rgba(100, 116, 139, 0.12)',
    border: 'rgba(100, 116, 139, 0.35)',
    icon: 'help',
    label: verdict
  };

  const handleDownload = async () => {
    setDownloading(true);
    try {
      if (onExportPdf) {
        await onExportPdf(result);
      } else {
        const blob = await api.exportPdf(result);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `claimshield_report_${Date.now()}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (e) {
      alert(`Export failed: ${e.message}`);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="glass-card" style={{
      borderLeft: `6px solid ${cfg.color}`,
      padding: '28px',
      marginBottom: '24px'
    }}>
      {/* Header Row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
        <div>
          <div style={{ fontSize: '0.82rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748B', marginBottom: '6px' }}>
            Multi-Agent AI Verdict
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              className="verdict-badge"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                background: cfg.bg,
                color: cfg.color,
                border: `1px solid ${cfg.border}`,
                padding: '6px 14px',
                borderRadius: '9999px',
                fontWeight: '800',
                fontSize: '1rem'
              }}
            >
              <span className="material-symbols-rounded">{cfg.icon}</span>
              <span>{cfg.label}</span>
            </span>
          </div>
        </div>

        {/* Confidence Meter */}
        <div style={{ minWidth: '180px', textAlign: 'right' }}>
          <div style={{ fontSize: '0.8rem', color: '#64748B', fontWeight: '600', marginBottom: '4px' }}>
            Confidence Level: <strong style={{ color: cfg.color }}>{conf}%</strong>
          </div>
          <div style={{ height: '8px', background: '#E2E8F0', borderRadius: '6px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${conf}%`,
                height: '100%',
                background: cfg.color,
                borderRadius: '6px',
                transition: 'width 0.8s ease'
              }}
            />
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: '4px' }}>
            Verified via {result.engine || 'Multi-LLM Consensus'}
          </div>
        </div>
      </div>

      {/* Straight Answer (If general question) */}
      {result.straight_answer && (
        <div style={{
          background: 'rgba(240, 249, 255, 0.7)',
          border: '1px solid rgba(186, 230, 253, 0.8)',
          borderRadius: '12px',
          padding: '16px 20px',
          marginBottom: '18px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#0369A1', fontWeight: '700', fontSize: '0.88rem', marginBottom: '6px' }}>
            <span className="material-symbols-rounded" style={{ fontSize: '1.2rem' }}>chat</span>
            <span>Direct Answer:</span>
          </div>
          <p style={{ margin: 0, color: '#0C4A6E', fontSize: '0.96rem', lineHeight: '1.6' }}>
            {result.straight_answer}
          </p>
        </div>
      )}

      {/* Reasoning & Evidence Summary */}
      {result.summary && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#334155', fontWeight: '700', fontSize: '0.88rem', marginBottom: '8px' }}>
            <span className="material-symbols-rounded" style={{ fontSize: '1.2rem', color: '#4F46E5' }}>menu_book</span>
            <span>Reasoning & Explanation:</span>
          </div>
          <p style={{ margin: 0, color: '#475569', fontSize: '0.94rem', lineHeight: '1.65' }}>
            {result.summary}
          </p>
        </div>
      )}

      {/* Action Footer */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '12px', borderTop: '1px solid rgba(226, 232, 240, 0.7)' }}>
        <button
          onClick={handleDownload}
          disabled={downloading}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            background: 'linear-gradient(135deg, #0F172A, #1E293B)',
            color: 'white',
            border: 'none',
            padding: '9px 18px',
            borderRadius: '10px',
            fontWeight: '600',
            fontSize: '0.85rem',
            cursor: downloading ? 'not-allowed' : 'pointer',
            boxShadow: '0 4px 12px rgba(15, 23, 42, 0.15)'
          }}
        >
          <span className="material-symbols-rounded">download</span>
          <span>{downloading ? 'Generating PDF...' : 'Download Verification Report (PDF)'}</span>
        </button>
      </div>
    </div>
  );
}
