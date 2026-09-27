import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function AuthModal({ isOpen, onClose, initialMode = 'login', onAuthSuccess }) {
  const [mode, setMode] = useState(initialMode); // 'login' or 'register'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login, register } = useAuth();

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'login') {
        await login(username, password);
      } else {
        await register(username, password, role);
      }
      onClose();
      if (onAuthSuccess) onAuthSuccess();
    } catch (err) {
      setError(err.message || 'Authentication error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'rgba(15, 23, 42, 0.45)',
      backdropFilter: 'blur(8px)',
      padding: '16px'
    }}>
      <div className="glass-card" style={{
        maxWidth: '440px',
        width: '100%',
        padding: '32px',
        position: 'relative',
        boxShadow: '0 25px 60px -15px rgba(0,0,0,0.25)',
        background: 'rgba(255, 255, 255, 0.92)'
      }}>
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: '#94A3B8'
          }}
        >
          <span className="material-symbols-rounded">close</span>
        </button>

        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '54px',
            height: '54px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #4F46E5, #3730A3)',
            color: 'white',
            marginBottom: '12px',
            boxShadow: '0 8px 18px rgba(79, 70, 229, 0.25)'
          }}>
            <span className="material-symbols-rounded" style={{ fontSize: '1.8rem' }}>shield</span>
          </div>
          <h2 style={{ margin: '0 0 6px 0', fontSize: '1.5rem', color: '#0F172A', fontWeight: '800' }}>
            {mode === 'login' ? 'Sign In to ClaimShield' : 'Create Free Account'}
          </h2>
          <p style={{ margin: 0, color: '#64748B', fontSize: '0.88rem' }}>
            {mode === 'login' ? 'Access real-time verification and your saved audit logs' : 'Verify claims instantly with our multi-agent AI network'}
          </p>
        </div>

        {/* Tab switch */}
        <div style={{
          display: 'flex',
          background: '#F1F5F9',
          borderRadius: '12px',
          padding: '4px',
          marginBottom: '20px'
        }}>
          <button
            type="button"
            onClick={() => { setMode('login'); setError(''); }}
            style={{
              flex: 1,
              padding: '8px 0',
              border: 'none',
              background: mode === 'login' ? '#FFFFFF' : 'transparent',
              borderRadius: '9px',
              fontWeight: '600',
              fontSize: '0.85rem',
              color: mode === 'login' ? '#4F46E5' : '#64748B',
              boxShadow: mode === 'login' ? '0 2px 6px rgba(0,0,0,0.06)' : 'none',
              cursor: 'pointer'
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setMode('register'); setError(''); }}
            style={{
              flex: 1,
              padding: '8px 0',
              border: 'none',
              background: mode === 'register' ? '#FFFFFF' : 'transparent',
              borderRadius: '9px',
              fontWeight: '600',
              fontSize: '0.85rem',
              color: mode === 'register' ? '#4F46E5' : '#64748B',
              boxShadow: mode === 'register' ? '0 2px 6px rgba(0,0,0,0.06)' : 'none',
              cursor: 'pointer'
            }}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#DC2626',
            borderRadius: '10px',
            padding: '10px 14px',
            fontSize: '0.85rem',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span className="material-symbols-rounded" style={{ fontSize: '1.2rem' }}>error</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: '600', color: '#334155', marginBottom: '6px' }}>
              Username
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. journalist_alex"
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '10px',
                border: '1px solid #CBD5E1',
                fontSize: '0.9rem',
                outline: 'none',
                background: '#FFFFFF',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: '600', color: '#334155', marginBottom: '6px' }}>
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '10px',
                border: '1px solid #CBD5E1',
                fontSize: '0.9rem',
                outline: 'none',
                background: '#FFFFFF',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {mode === 'register' && (
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: '600', color: '#334155', marginBottom: '6px' }}>
                Initial Commercialization Plan
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  border: '1px solid #CBD5E1',
                  fontSize: '0.9rem',
                  outline: 'none',
                  background: '#FFFFFF',
                  boxSizing: 'border-box'
                }}
              >
                <option value="user">Free Plan (3 capacity, displays 2 resources)</option>
                <option value="pro">Pro Plan (Unlimited, displays 3–5 resources)</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: '8px',
              padding: '12px',
              borderRadius: '10px',
              border: 'none',
              background: 'linear-gradient(135deg, #4F46E5 0%, #3730A3 100%)',
              color: '#FFFFFF',
              fontWeight: '700',
              fontSize: '0.95rem',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
              boxShadow: '0 4px 14px rgba(79, 70, 229, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            {loading ? (
              <span>Authenticating...</span>
            ) : (
              <>
                <span className="material-symbols-rounded">
                  {mode === 'login' ? 'login' : 'rocket_launch'}
                </span>
                <span>{mode === 'login' ? 'Sign In' : 'Create Account'}</span>
              </>
            )}
          </button>
        </form>

        <div style={{ marginTop: '18px', textAlign: 'center', fontSize: '0.8rem', color: '#64748B' }}>
          Demo test accounts:{' '}
          <strong style={{ color: '#4F46E5' }}>user</strong> / password (Free) ·{' '}
          <strong style={{ color: '#4F46E5' }}>pro</strong> / password (Pro)
        </div>
      </div>
    </div>
  );
}
