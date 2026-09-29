import React from 'react';
import { Outlet, useOutletContext } from 'react-router';
import Navbar from '@/components/Navbar';
import AmbientBackground from '@/components/AmbientBackground';

export function useAuthDialog() {
  return useOutletContext();
}

export default function PublicLayout({ openAuth }) {
  return (
    <div className="relative flex min-h-svh flex-col bg-transparent">
      <AmbientBackground />
      <Navbar openAuth={openAuth} />
      <main className="flex-1">
        <Outlet context={{ openAuth }} />
      </main>
      <footer className="border-t border-[var(--glass-secondary-border)] glass-panel">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-6 text-sm text-muted-foreground sm:flex-row">
          <p>© {new Date().getFullYear()} ClaimShield AI — multi-agent claim verification.</p>
          <p className="font-mono text-xs">Evidence-grounded · A2A/1.0 protocol · Demo build</p>
        </div>
      </footer>
    </div>
  );
}
