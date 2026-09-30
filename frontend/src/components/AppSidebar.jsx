import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router';
import {
  ShieldCheck,
  UserRound,
  ScrollText,
  Network,
  LogOut,
} from 'lucide-react';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from '@/components/ui/sidebar';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Verification', icon: ShieldCheck },
  { to: '/account', label: 'Account & Plan', icon: UserRound },
  { to: '/audit', label: 'Audit Logs', icon: ScrollText },
  { to: '/a2a', label: 'A2A Monitor', icon: Network },
];

function QuotaCard() {
  const { profile, isPro } = useAuth();

  const tokens = profile?.tokens ?? 0;
  const capacity = profile?.capacity ?? 3;
  const pct = isPro ? 100 : Math.max(0, Math.min(100, (tokens / capacity) * 100));

  return (
    <div className="rounded-2xl glass-card p-4 shadow-xs">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-bold text-slate-800 dark:text-sidebar-foreground/90">Token quota</span>
        <Badge
          variant={isPro ? 'default' : 'secondary'}
          className={cn(
            'text-[0.65rem] font-bold px-2 py-0.5 rounded-full',
            isPro
              ? 'border border-primary/40 bg-primary/20 text-primary shadow-xs backdrop-blur-md'
              : 'border border-slate-300/80 bg-white/70 text-slate-700 dark:border-white/10 dark:glass-pill dark:text-muted-foreground'
          )}
        >
          {isPro ? 'Pro' : 'Free'}
        </Badge>
      </div>
      <div className="mt-2.5 flex items-baseline gap-1.5">
        {isPro ? (
          <>
            <span className="text-xl font-black leading-none text-primary">∞</span>
            <span className="text-xs font-semibold text-slate-600 dark:text-muted-foreground">unlimited</span>
          </>
        ) : (
          <>
            <span className="text-lg font-bold leading-none tabular-nums text-slate-950 dark:text-foreground">
              {Math.floor(tokens)}
            </span>
            <span className="text-xs font-medium text-slate-600 dark:text-muted-foreground">/ {capacity} left</span>
          </>
        )}
      </div>
      <Progress value={pct} className="mt-2.5 h-1.5 overflow-hidden rounded-full bg-slate-200/80 dark:bg-muted/40" />
      <p className="mt-2 text-[0.72rem] font-medium leading-snug text-slate-600 dark:text-muted-foreground">
        {isPro
          ? 'Rate limits bypassed'
          : tokens < capacity
            ? `Refills ${profile?.refill_rate ?? 3} every hour`
            : 'Fully refilled — ready to verify'}
      </p>
    </div>
  );
}

export default function AppSidebar() {
  const { user, isPro, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const { setOpenMobile } = useSidebar();

  const initial = (user?.username || '?').charAt(0).toUpperCase();

  const handleLogout = () => {
    logout();
    setOpenMobile(false);
    navigate('/');
  };

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="p-3">
        <NavLink
          to="/"
          className="flex items-center gap-2.5 rounded-xl px-2 py-1.5 transition-all duration-150 hover:bg-[var(--glass-secondary-bg)] group-data-[collapsible=icon]:justify-center"
          title="ClaimShield AI — Home"
        >
          <span className="flex size-9.5 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-primary/85 text-primary-foreground shadow-md shadow-primary/25 ring-1 ring-primary/30 group-data-[collapsible=icon]:size-8">
            <ShieldCheck className="size-5" />
          </span>
          <span className="font-heading text-[1.05rem] font-black tracking-tight text-black dark:text-white group-data-[collapsible=icon]:hidden">
            ClaimShield AI
          </span>
        </NavLink>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="px-3 text-[0.72rem] font-bold uppercase tracking-[0.14em] text-slate-600 dark:text-muted-foreground/75">
            Menu
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1 px-1">
              {NAV_ITEMS.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <SidebarMenuButton
                    asChild
                    isActive={location.pathname === item.to}
                    tooltip={item.label}
                    className="font-medium text-slate-700 hover:text-slate-950 hover:bg-slate-900/[0.05] data-[active=true]:font-bold data-[active=true]:text-primary dark:text-sidebar-foreground dark:hover:text-foreground"
                  >
                    <NavLink to={item.to}>
                      <item.icon className="[&_svg]:stroke-[2]" />
                      <span>{item.label}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="px-2 group-data-[collapsible=icon]:hidden">
          <SidebarGroupContent>
            <QuotaCard />
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="mt-auto px-1">
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton tooltip="Sign out" onClick={handleLogout} className="font-medium text-slate-700 hover:text-red-600 hover:bg-red-500/10 dark:text-sidebar-foreground dark:hover:text-red-400">
                  <LogOut />
                  <span>Sign out</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-3">
        <div
          className={cn(
            'flex items-center gap-3 rounded-2xl glass-card p-2.5 shadow-xs transition-all duration-150',
            'group-data-[collapsible=icon]:mx-auto group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:p-0'
          )}
          title={user?.username}
        >
          <span
            className={cn(
              'flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/15 text-sm font-bold text-primary shadow-xs ring-1 ring-primary/25',
              'group-data-[collapsible=icon]:size-7'
            )}
          >
            {initial}
          </span>
          <div className="min-w-0 flex-1 group-data-[collapsible=icon]:hidden">
            <p className="truncate text-sm font-bold leading-tight text-slate-950 dark:text-foreground">{user?.username}</p>
            <p className="text-xs font-semibold text-slate-500 dark:text-muted-foreground">{isPro ? 'Pro plan' : 'Free plan'}</p>
          </div>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
