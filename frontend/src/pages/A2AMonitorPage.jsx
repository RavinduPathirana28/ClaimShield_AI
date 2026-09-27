import React, { useState } from 'react';

export default function A2AMonitorPage({ agentLogs = [] }) {
  const [expandedIndex, setExpandedIndex] = useState(null);

  const toggle = (idx) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  return (
    <div style={{ maxWidth: '1040px', margin: '0 auto', padding: '24px 20px 80px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: '800', color: '#0F172A', margin: '0 0 6px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="material-symbols-rounded" style={{ color: '#4F46E5', fontSize: '2rem' }}>settings</span>
          <span>Multi-Agent A2A/1.0 Protocol Message Tracing</span>
        </h2>
        <p style={{ margin: 0, color: '#64748B', fontSize: '0.94rem' }}>
          Inspect the real-time JSON communications occurring between subagents using the <strong>A2A/1.0 (Agent-to-Agent)</strong> protocol specification.
        </p>
      </div>

      {/* Protocol Spec Card */}
      <div className="glass-card" style={{ borderLeft: '5px solid #4F46E5', padding: '24px', marginBottom: '28px' }}>
        <h3 style={{ color: '#4F46E5', margin: '0 0 14px 0', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="material-symbols-rounded">assignment</span>
          <span>A2A/1.0 Protocol Specification</span>
        </h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', color: '#1E293B', fontSize: '0.9rem' }}>
          <tbody>
            {[
              ['Protocol', 'A2A/1.0 — Agent-to-Agent messaging over in-process Python function calls'],
              ['Serialization', 'JSON — validated via dumps/loads round-trip for strict compliance'],
              ['Message ID', 'UUID4 — unique identifier for every message for end-to-end traceability'],
              ['Timestamp', 'Unix epoch float — precise timing for performance profiling'],
              ['Transport', 'In-process function invocation — zero-latency delivery via BaseAgent.send_message()']
            ].map(([k, v], idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid rgba(226,232,240,0.85)' }}>
                <td style={{ padding: '10px 12px', fontWeight: '700', color: '#4F46E5', width: '22%' }}>{k}</td>
                <td style={{ padding: '10px 12px', color: '#334155' }}>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Log Traces */}
      {agentLogs.length === 0 ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: '#64748B' }}>
          <span className="material-symbols-rounded" style={{ fontSize: '2.5rem', color: '#CBD5E1', marginBottom: '8px' }}>inbox</span>
          <div style={{ fontWeight: '600', color: '#334155' }}>No active query logs in buffer.</div>
          <div style={{ fontSize: '0.86rem', marginTop: '4px' }}>
            Run a claim check on the <strong>Verification Dashboard</strong> to populate live A2A envelope logs.
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {agentLogs.map((log, idx) => {
            const isExp = expandedIndex === idx;
            return (
              <div key={idx} className="glass-card" style={{ padding: '16px 20px' }}>
                <div
                  onClick={() => toggle(idx)}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className="material-symbols-rounded" style={{ color: '#4F46E5' }}>public</span>
                    <strong style={{ color: '#0F172A', fontSize: '0.94rem' }}>
                      Trace #{idx + 1} [{log.timestamp}]: {log.from} → {log.to}
                    </strong>
                    <span style={{
                      background: 'rgba(79, 70, 229, 0.1)',
                      color: '#4F46E5',
                      padding: '2px 8px',
                      borderRadius: '6px',
                      fontSize: '0.76rem',
                      fontWeight: '700'
                    }}>
                      Action: {log.action}
                    </span>
                  </div>
                  <span className="material-symbols-rounded" style={{ color: '#64748B' }}>
                    {isExp ? 'expand_less' : 'expand_more'}
                  </span>
                </div>

                {isExp && (
                  <div style={{
                    marginTop: '16px',
                    paddingTop: '16px',
                    borderTop: '1px solid #E2E8F0',
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '16px'
                  }}>
                    <div>
                      <div style={{ fontSize: '0.82rem', fontWeight: '700', color: '#475569', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span className="material-symbols-rounded" style={{ color: '#0284C7', fontSize: '1.1rem' }}>outbox</span>
                        <span>Outgoing A2A/1.0 Envelope:</span>
                      </div>
                      <pre style={{
                        background: '#0F172A',
                        color: '#38BDF8',
                        padding: '12px',
                        borderRadius: '8px',
                        fontSize: '0.78rem',
                        overflowX: 'auto',
                        maxHeight: '260px'
                      }}>
                        {JSON.stringify({
                          protocol: 'A2A/1.0',
                          sender: log.from,
                          recipient: log.to,
                          action: log.action,
                          data: log.data_sent
                        }, null, 2)}
                      </pre>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.82rem', fontWeight: '700', color: '#475569', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span className="material-symbols-rounded" style={{ color: '#059669', fontSize: '1.1rem' }}>inbox</span>
                        <span>Received Response Payload:</span>
                      </div>
                      <pre style={{
                        background: '#0F172A',
                        color: '#4ADE80',
                        padding: '12px',
                        borderRadius: '8px',
                        fontSize: '0.78rem',
                        overflowX: 'auto',
                        maxHeight: '260px'
                      }}>
                        {JSON.stringify(log.response_received, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
