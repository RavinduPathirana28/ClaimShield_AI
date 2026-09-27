import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import AuthModal from './components/AuthModal';
import PaymentModal from './components/PaymentModal';

import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import PlansPage from './pages/PlansPage';
import AuditPage from './pages/AuditPage';
import A2AMonitorPage from './pages/A2AMonitorPage';
import ResponsibleAIPage from './pages/ResponsibleAIPage';

function MainApp() {
  const { isAuthenticated, loading } = useAuth();
  const [activePage, setActivePage] = useState('landing');
  const [engineMode, setEngineMode] = useState('Standard A2A Protocol');
  const [agentLogs, setAgentLogs] = useState([]);

  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authInitialMode, setAuthInitialMode] = useState('login');
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);

  // When user logs in, immediately switch to the verification dashboard (just like Streamlit)
  useEffect(() => {
    if (!loading) {
      if (isAuthenticated) {
        if (activePage === 'landing') {
          setActivePage('dashboard');
        }
      } else {
        if (activePage === 'dashboard' || activePage === 'audit' || activePage === 'a2a') {
          setActivePage('landing');
        }
      }
    }
  }, [isAuthenticated, loading]);

  const openAuth = (mode = 'login') => {
    setAuthInitialMode(mode);
    setAuthModalOpen(true);
  };

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#F8FAFC',
        color: '#4F46E5',
        flexDirection: 'column',
        gap: '12px'
      }}>
        <span className="material-symbols-rounded" style={{ fontSize: '3rem', animation: 'spin 1.2s linear infinite' }}>
          sync
        </span>
        <div style={{ fontWeight: '700', fontSize: '1.1rem', color: '#0F172A' }}>
          Loading ClaimShield AI...
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // AUTHENTICATED USER LAYOUT (Streamlit Sidebar + Main Verification Area)
  // -------------------------------------------------------------------------
  if (isAuthenticated) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', background: '#F8FAFC' }}>
        {/* Left Sidebar */}
        <Sidebar
          activePage={activePage}
          setActivePage={setActivePage}
          engineMode={engineMode}
          setEngineMode={setEngineMode}
        />

        {/* Right Main Content Area */}
        <main style={{ flex: 1, padding: '24px 32px', overflowY: 'auto', maxHeight: '100vh' }}>
          {activePage === 'dashboard' && (
            <DashboardPage
              engineMode={engineMode}
              onUpgradeClick={() => setPaymentModalOpen(true)}
              onNewAgentLogs={(newLogs) => setAgentLogs(newLogs)}
            />
          )}

          {activePage === 'plans' && (
            <PlansPage
              onOpenCheckout={() => setPaymentModalOpen(true)}
            />
          )}

          {activePage === 'audit' && <AuditPage />}

          {activePage === 'a2a' && <A2AMonitorPage agentLogs={agentLogs} />}

          {activePage === 'responsible_ai' && <ResponsibleAIPage />}
        </main>

        {/* Payment Checkout Modal */}
        <PaymentModal
          isOpen={paymentModalOpen}
          onClose={() => setPaymentModalOpen(false)}
          onSuccess={() => alert('Congratulations! Your Pro Plan is now active. Enjoy unlimited verifications!')}
        />
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // UNAUTHENTICATED VISITOR LAYOUT (Top Navbar + Landing Page)
  // -------------------------------------------------------------------------
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#F8FAFC' }}>
      <Navbar
        activePage={activePage}
        setActivePage={setActivePage}
        openAuthModal={openAuth}
      />

      <main style={{ flex: 1 }}>
        {activePage === 'landing' && (
          <LandingPage
            onGetStarted={() => openAuth('login')}
            onSelectPlan={(plan) => {
              openAuth('register');
            }}
          />
        )}

        {activePage === 'plans' && (
          <PlansPage
            onOpenCheckout={() => openAuth('login')}
          />
        )}

        {activePage === 'responsible_ai' && <ResponsibleAIPage />}
      </main>

      <footer style={{
        borderTop: '1px solid rgba(226, 232, 240, 0.8)',
        background: 'rgba(255, 255, 255, 0.7)',
        padding: '24px 20px',
        textAlign: 'center',
        fontSize: '0.84rem',
        color: '#64748B'
      }}>
        ClaimShield AI · Autonomous Multi-Agent Truth Verification System · Built with React & FastAPI
      </footer>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        initialMode={authInitialMode}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={() => setActivePage('dashboard')}
      />

      {/* Payment Checkout Modal */}
      <PaymentModal
        isOpen={paymentModalOpen}
        onClose={() => setPaymentModalOpen(false)}
        onSuccess={() => alert('Congratulations! Your Pro Plan is now active. Enjoy unlimited verifications!')}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
