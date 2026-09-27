import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import * as api from '../services/api';

export default function AuditPage() {
  const { token } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (token) {
      api.getAuditLogs(token)
        .then((data) => setLogs(data))
        .catch((err) => setError(err.message || 'Failed to fetch audit logs'))
        .finally(() => setLoading(false));
    }
  }, [token]);

  return (
    <div style={{ maxWidth: '1040px', margin: '0 auto', padding: '24px 20px 80px' }}>
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: '800', color: '#0F172A', margin: '0 0 6px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '2rem' }}>history_edu</span>
          <span>System Audit Logs & Cryptographic Trail</span>
        </h2>
        <p style={{ margin: 0, color: '#64748B', fontSize: '0.94rem' }}>
          All verified claims are cryptographically encrypted with AES-256 for transparency and auditability.
        </p>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#DC2626', padding: '12px 16px', borderRadius: '10px', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div className="glass-card" style={{ padding: '36px', textAlign: 'center', color: '#64748B' }}>
          <span className="material-symbols-rounded" style={{ fontSize: '2rem', animation: 'spin 1s linear infinite' }}>sync</span>
          <div style={{ marginTop: '8px' }}>Decrypting user audit records...</div>
        </div>
      ) : logs.length === 0 ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: '#64748B' }}>
          <span className="material-symbols-rounded" style={{ fontSize: '2.5rem', color: '#CBD5E1', marginBottom: '8px' }}>inbox</span>
          <div style={{ fontWeight: '600', color: '#334155' }}>No verification audit logs found yet.</div>
          <div style={{ fontSize: '0.86rem', marginTop: '4px' }}>Verify your first claim on the Verification Dashboard!</div>
        </div>
      ) : (
        <div className="glass-card" style={{ padding: '20px', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #E2E8F0', color: '#475569' }}>
                <th style={{ padding: '10px 14px' }}>Timestamp</th>
                <th style={{ padding: '10px 14px' }}>Claim / Query</th>
                <th style={{ padding: '10px 14px' }}>Verdict</th>
                <th style={{ padding: '10px 14px' }}>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((row, idx) => {
                const dateStr = row.timestamp ? new Date(row.timestamp * 1000).toLocaleString() : 'N/A';
                const conf = typeof row.confidence === 'number' ? Math.round(row.confidence * 100) : 'N/A';
                return (
                  <tr key={idx} style={{ borderBottom: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '12px 14px', color: '#64748B', whiteSpace: 'nowrap' }}>{dateStr}</td>
                    <td style={{ padding: '12px 14px', color: '#0F172A', fontWeight: '500' }}>{row.claim}</td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{
                        padding: '4px 10px',
                        borderRadius: '9999px',
                        fontSize: '0.78rem',
                        fontWeight: '700',
                        background: row.verdict === 'Supported' ? 'rgba(16, 185, 129, 0.15)' : row.verdict === 'Contradicted' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(2, 132, 199, 0.15)',
                        color: row.verdict === 'Supported' ? '#047857' : row.verdict === 'Contradicted' ? '#B91C1C' : '#0369A1'
                      }}>
                        {row.verdict || 'Unclear'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', color: '#334155', fontWeight: '600' }}>
                      {conf}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
