import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import * as api from '../services/api';

export default function PaymentModal({ isOpen, onClose, onSuccess }) {
  const { token, refreshProfile } = useAuth();
  const [holder, setHolder] = useState('Alex Mercer');
  const [cardNumber, setCardNumber] = useState('4242 4242 4242 4242');
  const [expiry, setExpiry] = useState('12/28');
  const [cvv, setCvv] = useState('123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await api.checkout(token, {
        cardholder_name: holder,
        card_number: cardNumber,
        expiry,
        cvv,
        plan: 'pro'
      });
      await refreshProfile();
      if (onSuccess) onSuccess(res);
      onClose();
    } catch (err) {
      setError(err.message || 'Payment processing failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 1100,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'rgba(15, 23, 42, 0.5)',
      backdropFilter: 'blur(8px)',
      padding: '16px'
    }}>
      <div className="glass-card" style={{
        maxWidth: '460px',
        width: '100%',
        padding: '32px',
        position: 'relative',
        background: 'rgba(255, 255, 255, 0.95)',
        boxShadow: '0 25px 60px -15px rgba(0,0,0,0.3)'
      }}>
        {/* Close */}
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

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '50px',
            height: '50px',
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #4F46E5, #7C3AED)',
            color: 'white',
            marginBottom: '10px'
          }}>
            <span className="material-symbols-rounded" style={{ fontSize: '1.6rem' }}>credit_card</span>
          </div>
          <h3 style={{ margin: '0 0 4px 0', fontSize: '1.35rem', color: '#0F172A', fontWeight: '800' }}>
            Upgrade to Pro Plan
          </h3>
          <div style={{ color: '#4F46E5', fontWeight: '800', fontSize: '1.25rem' }}>
            $19.00 <span style={{ fontSize: '0.85rem', color: '#64748B', fontWeight: '500' }}>/ month</span>
          </div>
          <p style={{ margin: '6px 0 0 0', color: '#64748B', fontSize: '0.82rem' }}>
            Unlimited claim verification · Displays 3–5 resources · Zero throttles
          </p>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#DC2626',
            borderRadius: '8px',
            padding: '10px 14px',
            fontSize: '0.84rem',
            marginBottom: '16px'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
              Cardholder Name
            </label>
            <input
              type="text"
              required
              value={holder}
              onChange={(e) => setHolder(e.target.value)}
              style={{
                width: '100%',
                padding: '9px 12px',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.88rem',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
              Card Number (Demo Visa)
            </label>
            <input
              type="text"
              required
              value={cardNumber}
              onChange={(e) => setCardNumber(e.target.value)}
              style={{
                width: '100%',
                padding: '9px 12px',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '0.88rem',
                boxSizing: 'border-box'
              }}
            />
            <div style={{ fontSize: '0.74rem', color: '#64748B', marginTop: '3px' }}>
              Test card: <strong>4242 4242 4242 4242</strong>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
                Expiry (MM/YY)
              </label>
              <input
                type="text"
                required
                value={expiry}
                onChange={(e) => setExpiry(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '8px',
                  border: '1px solid #CBD5E1',
                  fontSize: '0.88rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#334155', marginBottom: '4px' }}>
                CVV
              </label>
              <input
                type="password"
                required
                value={cvv}
                onChange={(e) => setCvv(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '8px',
                  border: '1px solid #CBD5E1',
                  fontSize: '0.88rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>
          </div>

          <div style={{
            background: '#F8FAFC',
            border: '1px solid #E2E8F0',
            borderRadius: '8px',
            padding: '10px 12px',
            fontSize: '0.76rem',
            color: '#64748B',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <span className="material-symbols-rounded" style={{ fontSize: '1.1rem', color: '#059669' }}>lock</span>
            <span>Simulated ClaimShield Pay Gateway. No real card will be charged.</span>
          </div>

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
              boxShadow: '0 4px 14px rgba(79, 70, 229, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <span className="material-symbols-rounded">verified</span>
            <span>{loading ? 'Processing Payment...' : 'Pay $19.00 & Upgrade to Pro'}</span>
          </button>
        </form>
      </div>
    </div>
  );
}
