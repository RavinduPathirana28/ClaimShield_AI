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
    <div className="rounded-2xl glass-panel p-3.5 shadow-xs">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-sidebar-foreground/80">Token quota</span>
        <Badge variant={isPro ? 'default' : 'secondary'} className="text-[0.65rem]">
          {isPro ? 'Pro' : 'Free'}
        </Badge>
      </div>
      <div className="mt-2 flex items-baseline gap-1">
        {isPro ? (
          <>
            <span className="text-lg font-semibold leading-none">∞</span>
            <span className="text-xs text-muted-foreground">unlimited</span>
          </>
        ) : (
          <>
            <span className="text-lg font-semibold leading-none tabular-nums">
              {Math.floor(tokens)}
            </span>
            <span className="text-xs text-muted-foreground">/ {capacity} left</span>
          </>
        )}
      </div>
      <Progress value={pct} className="mt-2 h-1.5" />
      <p className="mt-2 text-[0.7rem] leading-snug text-muted-foreground">
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
      <SidebarHeader>
        <NavLink
          to="/"
          className="flex items-center gap-2 px-1 py-1.5 group-data-[collapsible=icon]:justify-center"
          title="ClaimShield AI — Home"
        >
          <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-xs shadow-primary/30 group-data-[collapsible=icon]:size-7">
            <ShieldCheck className="size-5" />
          </span>
          <span className="font-heading text-sm font-semibold group-data-[collapsible=icon]:hidden">
            ClaimShield AI
          </span>
        </NavLink>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Menu</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <SidebarMenuButton
                    asChild
                    isActive={location.pathname === item.to}
                    tooltip={item.label}
                  >
                    <NavLink to={item.to}>
                      <item.icon />
                      <span>{item.label}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="group-data-[collapsible=icon]:hidden">
          <SidebarGroupContent>
            <QuotaCard />
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="mt-auto">
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton tooltip="Sign out" onClick={handleLogout}>
                  <LogOut />
                  <span>Sign out</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <div
          className={cn(
            'flex items-center gap-3 rounded-2xl glass-panel p-2.5 shadow-xs',
            'group-data-[collapsible=icon]:mx-auto group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:p-0'
          )}
          title={user?.username}
        >
          <span
            className={cn(
              'flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-sm font-semibold text-primary',
              'group-data-[collapsible=icon]:size-6'
            )}
          >
            {initial}
          </span>
          <div className="min-w-0 flex-1 group-data-[collapsible=icon]:hidden">
            <p className="truncate text-sm font-medium leading-tight">{user?.username}</p>
            <p className="text-xs text-muted-foreground">{isPro ? 'Pro plan' : 'Free plan'}</p>
          </div>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
