import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router';
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';
import AppSidebar from '@/components/AppSidebar';
import { ModeToggle } from '@/components/mode-toggle';
import { useAuth } from '@/context/AuthContext';

const PAGE_TITLES = [
  ['/dashboard', 'Verification Dashboard'],
  ['/account', 'Account & Plan Management'],
  ['/audit', 'System Audit Logs'],
  ['/a2a', 'A2A Protocol Monitor'],
];

export default function AppLayout() {
  const { isAuthenticated, isPro } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/" state={{ from: location.pathname }} replace />;
  }

  const title = PAGE_TITLES.find(([path]) => location.pathname.startsWith(path))?.[1] ?? 'ClaimShield AI';

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-12 shrink-0 items-center gap-2 border-b bg-background/95 px-3 backdrop-blur supports-[backdrop-filter]:bg-background/80">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-auto" />
          <span className="truncate text-sm font-semibold">{title}</span>
          <span className="ml-auto flex items-center gap-2">
            <span
              className={`hidden rounded-full border px-2 py-0.5 text-xs font-medium sm:inline ${
                isPro
                  ? 'border-primary/30 bg-primary/10 text-primary'
                  : 'border-border bg-muted text-muted-foreground'
              }`}
            >
              {isPro ? 'Pro plan' : 'Free plan'}
            </span>
            <ModeToggle />
          </span>
        </header>
        <main className="flex-1 p-4 md:p-6">
          <div className="mx-auto w-full max-w-6xl">
            <Outlet />
          </div>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
