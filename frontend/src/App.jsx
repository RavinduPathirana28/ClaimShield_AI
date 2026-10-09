import React, { useState, useCallback, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router';
import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ThemeProvider } from '@/components/theme-provider';
import { AuthProvider } from '@/context/AuthContext';
import { RunProvider } from '@/context/RunContext';

import PublicLayout from '@/layouts/PublicLayout';
import AppLayout from '@/layouts/AppLayout';
import AuthDialog from '@/components/AuthDialog';

// Route-level code splitting: only the shell loads up front; each page is
// fetched on first navigation.
const LandingPage = React.lazy(() => import('@/pages/LandingPage'));
const PlansPage = React.lazy(() => import('@/pages/PlansPage'));
const ResponsibleAIPage = React.lazy(() => import('@/pages/ResponsibleAIPage'));
const DashboardPage = React.lazy(() => import('@/pages/DashboardPage'));
const AccountPage = React.lazy(() => import('@/pages/AccountPage'));
const AuditPage = React.lazy(() => import('@/pages/AuditPage'));
const A2AMonitorPage = React.lazy(() => import('@/pages/A2AMonitorPage'));

function RouteFallback() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <div className="size-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>
  );
}

export default function App() {
  const [auth, setAuth] = useState({ open: false, mode: 'login', plan: undefined });
  const openAuth = useCallback(
    (mode = 'login', plan) => setAuth({ open: true, mode, plan }),
    []
  );

  return (
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <AuthProvider>
        <RunProvider>
          <TooltipProvider delayDuration={150}>
            <BrowserRouter basename={import.meta.env.BASE_URL}>
              <Suspense fallback={<RouteFallback />}>
                <Routes>
                  <Route element={<PublicLayout openAuth={openAuth} />}>
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/plans" element={<PlansPage />} />
                    <Route path="/responsible-ai" element={<ResponsibleAIPage />} />
                  </Route>
                  <Route element={<AppLayout />}>
                    <Route path="/dashboard" element={<DashboardPage />} />
                    <Route path="/account" element={<AccountPage />} />
                    <Route path="/audit" element={<AuditPage />} />
                    <Route path="/a2a" element={<A2AMonitorPage />} />
                  </Route>
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
              <AuthDialog
                open={auth.open}
                mode={auth.mode}
                plan={auth.plan}
                onOpenChange={(open) => setAuth((a) => ({ ...a, open }))}
              />
              <Toaster position="top-right" richColors closeButton />
            </BrowserRouter>
          </TooltipProvider>
        </RunProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
