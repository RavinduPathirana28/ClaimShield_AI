import React from 'react';
import { useAuth } from '../context/AuthContext';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Verification Dashboard', icon: 'shield' },
  { id: 'plans', label: 'Account & Plan Management', icon: 'person' },
  { id: 'audit', label: 'System Audit Logs', icon: 'history_edu' },
  { id: 'a2a', label: 'A2A Protocol Monitor', icon: 'settings' },
  { id: 'responsible_ai', label: 'Responsible AI & Governance', icon: 'smart_toy' },
];

export default function Sidebar({ activePage, setActivePage, engineMode, setEngineMode }) {
  const { user, profile, isPro, logout } = useAuth();

  const tokens = profile?.tokens ?? 3.0;
  const capacity = profile?.capacity ?? 3.0;
  const pct = Math.min(Math.max((tokens / capacity) * 100, 0), 100);

  return (
    <aside style={{
      width: '300px',
      minWidth: '300px',
      background: 'rgba(255, 255, 255, 0.85)',
      backdropFilter: 'blur(20px) saturate(180%)',
      WebkitBackdropFilter: 'blur(20px) saturate(180%)',
      borderRight: '1px solid rgba(226, 232, 240, 0.9)',
      height: '100vh',
      position: 'sticky',
      top: 0,
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 20px',
      boxSizing: 'border-box',
      overflowY: 'auto',
      zIndex: 50
    }}>
      {/* Brand & Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <img
          src="/logo.jpg"
          alt="ClaimShield AI"
          style={{ width: '42px', height: '42px', borderRadius: '12px', objectFit: 'cover', boxShadow: '0 2px 8px rgba(79,70,229,0.2)' }}
          onError={(e) => { e.target.style.display = 'none'; }}
        />
        <div>
          <div style={{ fontWeight: '800', fontSize: '1.2rem', color: '#0F172A', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '6px' }}>
            ClaimShield <span style={{ color: '#4F46E5' }}>AI</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748B', fontWeight: '500' }}>
            Multi-Agent Fact Verification
          </div>
        </div>
      </div>

      {/* User Status Badge */}
      <div style={{
        background: '#F8FAFC',
        border: '1px solid #E2E8F0',
        borderRadius: '12px',
        padding: '12px 14px',
        marginBottom: '20px'
      }}>
        <div style={{ fontSize: '0.74rem', color: '#64748B', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          Active Session
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '4px' }}>
          <div style={{ fontWeight: '700', fontSize: '0.95rem', color: '#0F172A' }}>
            {user?.username}
          </div>
          <span style={{
            background: isPro ? 'rgba(79, 70, 229, 0.12)' : 'rgba(100, 116, 139, 0.12)',
            color: isPro ? '#4F46E5' : '#475569',
            fontSize: '0.72rem',
            fontWeight: '700',
            padding: '2px 8px',
            borderRadius: '9999px',
            textTransform: 'uppercase'
          }}>
            {isPro ? 'Pro Tier' : 'Free Tier'}
          </span>
        </div>
      </div>

      {/* Navigation Radio Menu */}
      <div style={{ marginBottom: '24px', flex: 1 }}>
        <div style={{ fontSize: '0.75rem', fontWeight: '700', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>
          Navigation
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {NAV_ITEMS.map((item) => {
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActivePage(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  border: 'none',
                  background: isActive ? 'linear-gradient(135deg, rgba(79, 70, 229, 0.12), rgba(124, 58, 237, 0.08))' : 'transparent',
                  color: isActive ? '#4F46E5' : '#475569',
                  fontWeight: isActive ? '700' : '500',
                  fontSize: '0.88rem',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  borderLeft: isActive ? '3px solid #4F46E5' : '3px solid transparent'
                }}
              >
                <span className="material-symbols-rounded" style={{ fontSize: '1.25rem', color: isActive ? '#4F46E5' : '#64748B' }}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <hr style={{ border: 'none', borderTop: '1px solid #E2E8F0', margin: '0 0 18px 0' }} />

      {/* Plan Quota Widget */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ fontSize: '0.78rem', fontWeight: '700', color: '#475569', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className="material-symbols-rounded" style={{ fontSize: '1.1rem', color: '#4F46E5' }}>bolt</span>
          <span>Plan Quota</span>
        </div>

        {isPro ? (
          <div style={{
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            padding: '10px 12px',
            borderRadius: '10px',
            fontSize: '0.82rem',
            color: '#047857',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontWeight: '600'
          }}>
            <span className="material-symbols-rounded" style={{ fontSize: '1.2rem' }}>rocket_launch</span>
            <span>Pro Plan: Unlimited Access Active</span>
          </div>
        ) : (
          <div style={{
            background: '#F8FAFC',
            border: '1px solid #E2E8F0',
            borderRadius: '10px',
            padding: '12px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: '#64748B', marginBottom: '6px' }}>
              <span>Tokens Remaining:</span>
              <strong style={{ color: '#0F172A' }}>{tokens.toFixed(1)} / {capacity}</strong>
            </div>
            <div style={{ height: '6px', background: '#E2E8F0', borderRadius: '4px', overflow: 'hidden', marginBottom: '6px' }}>
              <div style={{ width: `${pct}%`, height: '100%', background: '#4F46E5', borderRadius: '4px' }} />
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748B' }}>
              Refills 3 tokens / hr · Displays 2 resources
            </div>
          </div>
        )}
      </div>

      {/* Multi-Agent Engine Selector */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '0.78rem', fontWeight: '700', color: '#475569', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className="material-symbols-rounded" style={{ fontSize: '1.1rem', color: '#4F46E5' }}>smart_toy</span>
          <span>Multi-Agent Engine</span>
        </div>
        <select
          value={engineMode}
          onChange={(e) => setEngineMode(e.target.value)}
          style={{
            width: '100%',
            padding: '9px 12px',
            borderRadius: '8px',
            border: '1px solid #CBD5E1',
            fontSize: '0.85rem',
            outline: 'none',
            background: '#FFFFFF',
            color: '#1E293B',
            fontWeight: '600'
          }}
        >
          <option value="Standard A2A Protocol">Standard A2A Protocol</option>
          <option value="LangGraph Stateful Workflow">LangGraph Stateful Workflow</option>
          <option value="AutoGen Agent Debate">AutoGen Agent Debate</option>
        </select>
        <div style={{ fontSize: '0.7rem', color: '#94A3B8', marginTop: '4px', lineHeight: '1.3' }}>
          Select sequential, LangGraph graph, or Persona debate.
        </div>
      </div>

      {/* Logout Button */}
      <button
        onClick={logout}
        style={{
          width: '100%',
          padding: '10px',
          borderRadius: '10px',
          border: '1px solid #E2E8F0',
          background: '#FFFFFF',
          color: '#DC2626',
          fontWeight: '700',
          fontSize: '0.86rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '6px',
          cursor: 'pointer',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(239, 68, 68, 0.08)'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = '#FFFFFF'; }}
      >
        <span className="material-symbols-rounded" style={{ fontSize: '1.1rem' }}>logout</span>
        <span>Sign Out</span>
      </button>
    </aside>
  );
}
