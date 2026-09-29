import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router';
import { ShieldCheck, LayoutDashboard, Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { useAuth } from '@/context/AuthContext';
import { ModeToggle } from '@/components/mode-toggle';
import { cn } from '@/lib/utils';

const NAV_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/plans', label: 'Plans' },
  { to: '/responsible-ai', label: 'Ethics & AI' },
];

export default function Navbar({ openAuth }) {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const desktopLinkClass = ({ isActive }) =>
    cn(
      'rounded-xl px-3.5 py-1.5 text-sm font-medium transition-all duration-150',
      isActive
        ? 'glass-pill font-semibold text-foreground'
        : 'text-muted-foreground hover:bg-[var(--glass-secondary-bg)] hover:text-foreground'
    );

  const mobileLinkClass = ({ isActive }) =>
    cn(
      'flex items-center rounded-xl px-3.5 py-2.5 text-base font-medium transition-all',
      isActive
        ? 'glass-pill font-semibold text-foreground'
        : 'text-muted-foreground hover:bg-[var(--glass-secondary-bg)] hover:text-foreground'
    );

  return (
    <header className="sticky top-0 z-40 glass-navbar transition-all">
      <div className="relative z-10 mx-auto flex h-14 max-w-6xl items-center gap-2 px-4 sm:gap-4">
        <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
          <SheetTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="size-10 shrink-0 sm:hidden"
              aria-label="Open navigation menu"
            >
              <Menu />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-72 gap-0">
            <SheetHeader className="border-b pb-4">
              <SheetTitle className="flex items-center gap-2 font-heading text-base">
                <span className="flex size-7 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-xs shadow-primary/30">
                  <ShieldCheck className="size-4" />
                </span>
                ClaimShield AI
              </SheetTitle>
            </SheetHeader>
            <nav className="flex flex-col gap-1 px-4" aria-label="Main menu">
              {NAV_LINKS.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  end={link.end}
                  onClick={() => setMenuOpen(false)}
                  className={mobileLinkClass}
                >
                  {link.label}
                </NavLink>
              ))}
            </nav>
          </SheetContent>
        </Sheet>

        <NavLink to="/" className="flex items-center gap-2 font-semibold">
          <span className="flex size-7 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-xs shadow-primary/30">
            <ShieldCheck className="size-4" />
          </span>
          <span className="hidden font-heading text-base tracking-tight min-[480px]:inline">
            ClaimShield AI
          </span>
        </NavLink>

        <nav className="ml-4 hidden items-center gap-1 sm:flex" aria-label="Main menu">
          {NAV_LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end} className={desktopLinkClass}>
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          {isAuthenticated ? (
            <Button onClick={() => navigate('/dashboard')}>
              <LayoutDashboard data-icon="inline-start" />
              Dashboard
            </Button>
          ) : (
            <>
              <Button variant="ghost" onClick={() => openAuth('login')}>
                Sign in
              </Button>
              <Button onClick={() => openAuth('register')}>Get started</Button>
            </>
          )}
          <ModeToggle />
        </div>
      </div>
    </header>
  );
}
