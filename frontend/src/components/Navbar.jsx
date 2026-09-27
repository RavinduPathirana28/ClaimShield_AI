import React from 'react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ activePage, setActivePage, openAuthModal }) {
  const { isAuthenticated, user, profile, isPro, logout } = useAuth();

  const tokens = profile?.tokens ?? 3.0;
  const capacity = profile?.capacity ?? 3.0;
  const pct = Math.min(Math.max((tokens / capacity) * 100, 0), 100);

  return (
    <header className="glass-nav" style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      backdropFilter: 'blur(24px) saturate(180%)',
      WebkitBackdropFilter: 'blur(24px) saturate(180%)',
      background: 'rgba(255, 255, 255, 0.75)',
      borderBottom: '1px solid rgba(226, 232, 240, 0.8)',
      boxShadow: '0 4px 20px -2px rgba(15, 23, 42, 0.05)'
    }}>
      {/* Brand */}
      <div 
        style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        onClick={() => setActivePage(isAuthenticated ? 'dashboard' : 'landing')}
      >
        <img 
          src="/logo.jpg" 
          alt="ClaimShield AI" 
          style={{ width: '38px', height: '38px', borderRadius: '10px', objectFit: 'cover', boxShadow: '0 2px 8px rgba(79,70,229,0.2)' }}
          onError={(e) => { e.target.style.display = 'none'; }}
        />
        <div>
          <div style={{ fontWeight: '800', fontSize: '1.15rem', color: '#0F172A', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '6px' }}>
            ClaimShield <span style={{ color: '#4F46E5' }}>AI</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748B', fontWeight: '500' }}>
            Multi-Agent Fact Verification
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {isAuthenticated ? (
          <>
            <button
              className={`nav-tab-btn ${activePage === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActivePage('dashboard')}
            >
              <span className="material-symbols-rounded">shield</span>
              <span>Verification</span>
            </button>
            <button
              className={`nav-tab-btn ${activePage === 'plans' ? 'active' : ''}`}
              onClick={() => setActivePage('plans')}
            >
              <span className="material-symbols-rounded">diamond</span>
              <span>Plans & Account</span>
            </button>
            <button
              className={`nav-tab-btn ${activePage === 'audit' ? 'active' : ''}`}
              onClick={() => setActivePage('audit')}
            >
              <span className="material-symbols-rounded">history_edu</span>
              <span>Audit Logs</span>
            </button>
            <button
              className={`nav-tab-btn ${activePage === 'responsible_ai' ? 'active' : ''}`}
              onClick={() => setActivePage('responsible_ai')}
            >
              <span className="material-symbols-rounded">smart_toy</span>
              <span>Responsible AI</span>
            </button>
          </>
        ) : (
          <>
            <button
              className={`nav-tab-btn ${activePage === 'landing' ? 'active' : ''}`}
              onClick={() => setActivePage('landing')}
            >
              <span className="material-symbols-rounded">home</span>
              <span>Home</span>
            </button>
            <button
              className={`nav-tab-btn ${activePage === 'plans' ? 'active' : ''}`}
              onClick={() => setActivePage('plans')}
            >
              <span className="material-symbols-rounded">diamond</span>
              <span>Plans</span>
            </button>
            <button
              className={`nav-tab-btn ${activePage === 'responsible_ai' ? 'active' : ''}`}
              onClick={() => setActivePage('responsible_ai')}
            >
              <span className="material-symbols-rounded">smart_toy</span>
              <span>Ethics & AI</span>
            </button>
          </>
        )}
      </nav>

      {/* Right User Bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {isAuthenticated ? (
          <>
            {/* Live Token Indicator for Free plan */}
            {!isPro ? (
              <div style={{
                background: 'rgba(241, 245, 249, 0.85)',
                padding: '6px 12px',
                borderRadius: '9999px',
                border: '1px solid rgba(203, 213, 225, 0.8)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '0.8rem'
              }}>
                <span className="material-symbols-rounded" style={{ fontSize: '1.1rem', color: '#4F46E5' }}>bolt</span>
                <div>
                  <strong>{tokens.toFixed(1)} / {capacity}</strong> tokens
                </div>
                <div style={{ width: '50px', height: '6px', background: '#E2E8F0', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${pct}%`, height: '100%', background: '#4F46E5', borderRadius: '4px' }} />
                </div>
              </div>
            ) : (
              <div style={{
                background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.15), rgba(147, 51, 234, 0.15))',
                color: '#4F46E5',
                padding: '6px 14px',
                borderRadius: '9999px',
                border: '1px solid rgba(79, 70, 229, 0.3)',
                fontWeight: '700',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <span className="material-symbols-rounded" style={{ fontSize: '1.1rem', color: '#7C3AED' }}>star</span>
                <span>Pro Unlimited</span>
              </div>
            )}

            {/* User pill */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="material-symbols-rounded" style={{ color: '#64748B' }}>account_circle</span>
              <span style={{ fontWeight: '600', fontSize: '0.88rem', color: '#1E293B' }}>{user?.username}</span>
            </div>

            <button
              onClick={logout}
              style={{
                background: 'transparent',
                border: '1px solid #E2E8F0',
                padding: '6px 12px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.82rem',
                color: '#64748B',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <span className="material-symbols-rounded" style={{ fontSize: '1rem' }}>logout</span>
              <span>Sign Out</span>
            </button>
          </>
        ) : (
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => openAuthModal('login')}
              style={{
                background: 'transparent',
                border: '1px solid #CBD5E1',
                padding: '7px 16px',
                borderRadius: '10px',
                fontWeight: '600',
                fontSize: '0.85rem',
                cursor: 'pointer',
                color: '#1E293B'
              }}
            >
              Sign In
            </button>
            <button
              onClick={() => openAuthModal('register')}
              style={{
                background: 'linear-gradient(135deg, #4F46E5 0%, #3730A3 100%)',
                border: 'none',
                color: '#FFFFFF',
                padding: '7px 16px',
                borderRadius: '10px',
                fontWeight: '600',
                fontSize: '0.85rem',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(79, 70, 229, 0.25)'
              }}
            >
              Get Started
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
