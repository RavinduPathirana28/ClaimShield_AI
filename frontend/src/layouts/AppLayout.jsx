import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router';
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';
import AppSidebar from '@/components/AppSidebar';
import AmbientBackground from '@/components/AmbientBackground';
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
      <AmbientBackground />
      <AppSidebar />
      <SidebarInset className="bg-transparent">
        <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-3 glass-navbar border-b border-black/[0.14] dark:border-white/10 px-4 transition-all">
          <SidebarTrigger className="-ml-1 size-8.5 rounded-xl border border-black/20 bg-white/90 text-black shadow-xs transition-colors hover:border-black/40 hover:bg-white hover:text-black dark:border-white/10 dark:bg-transparent dark:text-white dark:hover:bg-white/10 dark:hover:text-white [&_svg]:size-4.5 [&_svg]:stroke-[2.4] [&_svg]:text-black dark:[&_svg]:text-white" />
          <div className="h-5 w-[1.5px] rounded-full bg-black/60 dark:bg-slate-600 shrink-0 self-center" aria-hidden="true" />
          <span className="truncate text-[0.95rem] font-bold tracking-tight text-black dark:text-white">{title}</span>
          <span className="ml-auto flex items-center gap-2">
            <span
              className={`hidden rounded-full border px-2.5 py-0.5 text-xs font-bold sm:inline ${
                isPro
                  ? 'border-primary/50 bg-primary/15 text-primary shadow-xs'
                  : 'border-black/20 bg-white/90 text-black dark:border-white/10 dark:glass-pill dark:text-muted-foreground'
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
