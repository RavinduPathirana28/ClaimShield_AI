import React, { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import {
  UserRound,
  Activity,
  Gauge,
  BadgeCheck,
  Flame,
  Hourglass,
  CircleCheck,
  Rocket,
  Gem,
  BarChart3,
  Lock,
  KeyRound,
  ShieldCheck,
  Users,
  Wrench,
  Loader2,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Field, FieldGroup, FieldLabel, FieldTitle, FieldError } from '@/components/ui/field';

import PaymentDialog from '@/components/PaymentDialog';
import { PLANS, PLAN_MATRIX, renderFeature } from '@/lib/plans';
import { useAuth } from '@/context/AuthContext';
import * as api from '@/services/api';

const MATRIX = PLAN_MATRIX;

function decodeJwt(token) {
  try {
    const part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = part + '='.repeat((4 - (part.length % 4)) % 4);
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
}

function PlanCard({ plan, active, onUpgrade, onDowngrade }) {
  const isProPlan = plan.id === 'pro';
  return (
    <Card
      className={
        active
          ? 'border-2 border-primary shadow-lg shadow-primary/15'
          : isProPlan
            ? 'border-2 border-primary/50 shadow-md shadow-primary/10'
            : 'border border-border/60'
      }
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="font-heading">{plan.name}</CardTitle>
          {active ? (
            <Badge className="gap-1">
              <CircleCheck className="size-3" />
              Active Plan
            </Badge>
          ) : (
            isProPlan && <Badge>Popular</Badge>
          )}
        </div>
        <CardDescription>{plan.tagline}</CardDescription>
        <p className={isProPlan ? 'text-3xl font-extrabold text-primary' : 'text-3xl font-extrabold'}>
          {plan.priceLabel}
          {plan.price > 0 && (
            <span className="text-sm font-normal text-muted-foreground">/mo</span>
          )}
        </p>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <ul className="flex flex-col gap-1.5 text-sm text-muted-foreground">
          {plan.features.map((feature) => (
            <li key={feature} className="flex items-start gap-2">
              <CircleCheck className="mt-0.5 size-3.5 shrink-0 text-primary" />
              <span>{renderFeature(feature)}</span>
            </li>
          ))}
        </ul>
        {active ? (
          <Button className="w-full" variant="secondary" disabled>
            <CircleCheck data-icon="inline-start" />
            Current Active Plan
          </Button>
        ) : isProPlan ? (
          <Button className="w-full" onClick={onUpgrade}>
            <Flame data-icon="inline-start" />
            Upgrade to Pro Plan
          </Button>
        ) : (
          <Button className="w-full" variant="outline" onClick={onDowngrade}>
            Downgrade to Free Plan
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export default function AccountPage() {
  const { token, user, profile, isPro, isAdmin, refreshProfile, saveToken } = useAuth();
  const [checkoutOpen, setCheckoutOpen] = useState(false);

  const [pwd, setPwd] = useState({ current: '', next: '', confirm: '' });
  const [pwdErrors, setPwdErrors] = useState({});
  const [pwdBusy, setPwdBusy] = useState(false);

  const [members, setMembers] = useState(null);
  const [membersError, setMembersError] = useState(null);
  const [targetUser, setTargetUser] = useState('');
  const [targetRole, setTargetRole] = useState('user');
  const [applying, setApplying] = useState(false);

  const loadMembers = useCallback(async () => {
    if (!isAdmin) return;
    try {
      const users = await api.adminListUsers(token);
      setMembers(users);
      setMembersError(null);
      setTargetUser((prev) => prev || users[0]?.username || '');
    } catch (err) {
      setMembersError(err.message);
    }
  }, [isAdmin, token]);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  const username = profile?.username || user?.username || 'User';
  const role = profile?.role || user?.role || 'user';
  const activeFree = !isPro;
  const claimsVerified = profile?.claims_verified ?? 0;

  const tokens = profile?.tokens ?? 0;
  const capacity = profile?.capacity ?? 3;
  const refillRate = profile?.refill_rate ?? 3;
  const refillPeriodHours = profile?.refill_period_hours ?? 1;
  const tokenPct = Math.max(0, Math.min(100, (tokens / capacity) * 100));
  const needed = Math.max(0, capacity - tokens);
  const secondsToFull = needed * ((refillPeriodHours * 3600) / refillRate);
  const minutesToFull = Math.ceil(secondsToFull / 60);

  const jwtPayload = decodeJwt(token || '');

  const downgrade = async () => {
    try {
      const res = await api.changePlan(token, 'user');
      saveToken(res.token);
      await refreshProfile();
      toast.success('Successfully switched to Free Plan!');
    } catch (err) {
      toast.error(err.message);
    }
  };

  const setPassword = (key) => (e) => setPwd((p) => ({ ...p, [key]: e.target.value }));

  const submitPassword = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!pwd.current) errs.current = 'Current password is required.';
    if (!pwd.next) errs.next = 'New password is required.';
    else if (pwd.next.length < 4) errs.next = 'At least 4 characters.';
    if (pwd.next !== pwd.confirm) errs.confirm = 'Passwords do not match.';
    setPwdErrors(errs);
    if (Object.keys(errs).length) return;

    setPwdBusy(true);
    try {
      const res = await api.changePassword(token, pwd.current, pwd.next);
      toast.success(res.message || 'Password updated successfully.');
      setPwd({ current: '', next: '', confirm: '' });
    } catch (err) {
      toast.error(err.message);
    } finally {
      setPwdBusy(false);
    }
  };

  const applyRole = async () => {
    if (!targetUser || !targetRole) return;
    setApplying(true);
    try {
      const res = await api.adminSetRole(token, targetUser, targetRole);
      toast.success(res.message || 'Role updated.');
      await loadMembers();
      if (targetUser === username) await refreshProfile();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="flex flex-col gap-8">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h2 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <UserRound className="size-6 text-primary" />
            User Account &amp; Subscription Management
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage your profile, monitor real-time token quotas, and switch subscription plans
            seamlessly.
          </p>
        </div>
      </header>

      {/* Profile banner */}
      <Card className="shadow-sm">
        <CardContent className="flex flex-wrap items-center gap-4 pt-6">
          <span className="flex size-14 items-center justify-center rounded-full bg-primary/15 text-2xl font-bold text-primary">
            {username.charAt(0).toUpperCase()}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-3">
              <h3 className="text-xl font-bold">{username}</h3>
              <Badge variant="outline" className="gap-1.5 border-emerald-600/40 bg-emerald-600/10 text-emerald-700 dark:text-emerald-400">
                <span className="size-1.5 animate-pulse rounded-full bg-emerald-600" />
                Active Session
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Subscription Plan:{' '}
              <strong className="text-primary">{isPro ? 'Pro Plan' : 'Free Plan'}</strong> ·
              Authentication: <strong className="text-emerald-600">JWT Signed (HS256)</strong>
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Metric row */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="shadow-sm">
          <CardHeader className="pb-1">
            <CardDescription className="flex items-center gap-1.5">
              <BadgeCheck className="size-3.5" /> Current Active Plan
            </CardDescription>
            <CardTitle className="text-2xl font-extrabold text-primary">
              {isPro ? 'Pro Plan' : 'Free Plan'}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            {isPro
              ? 'Unlimited / Up to 5 resources'
              : '3 Tokens / 2 Resources displayed'}
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader className="pb-1">
            <CardDescription className="flex items-center gap-1.5">
              <Gauge className="size-3.5" /> {isPro ? 'Verification Quota' : 'Remaining Tokens'}
            </CardDescription>
            <CardTitle className={isPro ? 'text-2xl font-extrabold text-emerald-600' : 'text-2xl font-extrabold text-sky-600'}>
              {isPro ? 'Unlimited ∞' : `${tokens.toFixed(1)} / ${capacity}`}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            {isPro
              ? 'Rate Limit Bypassed · 3–5 Resources'
              : `Refills ${refillRate} / hour · Only 2 resources shown`}
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader className="pb-1">
            <CardDescription className="flex items-center gap-1.5">
              <Activity className="size-3.5" /> Lifetime Claims Verified
            </CardDescription>
            <CardTitle className="text-2xl font-extrabold text-primary">
              {claimsVerified}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            Recorded in Encrypted Audit Trail
          </CardContent>
        </Card>
      </div>

      <Separator />

      {/* Quota status */}
      <section className="flex flex-col gap-3">
        <div>
          <h3 className="flex items-center gap-2 text-lg font-bold">
            <Flame className="size-5 text-primary" />
            Real-Time Plan Quotas &amp; Token Bucket Status
          </h3>
          <p className="text-sm text-muted-foreground">
            <strong>Free Plan</strong> has a 3-token capacity with 2 displayed resources, while{' '}
            <strong>Pro Plan</strong> enjoys unlimited verification quota and up to 5 verified
            resources per query.
          </p>
        </div>

        {isPro ? (
          <Alert className="border-emerald-600/40 bg-emerald-600/10">
            <Rocket className="size-4 text-emerald-600" />
            <AlertTitle className="text-emerald-700 dark:text-emerald-400">
              Unlimited Pro Plan Active
            </AlertTitle>
            <AlertDescription>
              Zero request throttles, priority execution in the verification queue, and at least 3
              (if available) up to 5 maximum verified resources per query.
            </AlertDescription>
          </Alert>
        ) : (
          <Card className="shadow-sm">
            <CardContent className="flex flex-col gap-4 pt-6">
              <div>
                <div className="mb-1.5 flex items-center justify-between text-sm">
                  <span className="font-semibold">
                    Token Capacity Utilization ({tokens.toFixed(1)} / {capacity} available)
                  </span>
                  <span className="font-bold tabular-nums text-primary">
                    {Math.round(tokenPct)}%
                  </span>
                </div>
                <Progress value={tokenPct} className="h-2" />
                <p className="mt-1.5 text-xs text-muted-foreground">
                  Refill rate:{' '}
                  <strong>
                    {refillRate} tokens per hour
                  </strong>{' '}
                  ({Math.round((refillPeriodHours * 3600) / refillRate)} seconds per token) ·
                  Displays only 2 resources.
                </p>
              </div>
              <Separator />
              {needed > 0 ? (
                <p className="flex items-center gap-2 text-sm text-sky-700 dark:text-sky-400">
                  <Hourglass className="size-4" />
                  Estimated time until 100% capacity:{' '}
                  <strong>~{minutesToFull} minute{minutesToFull === 1 ? '' : 's'}</strong>.
                </p>
              ) : (
                <p className="flex items-center gap-2 text-sm text-emerald-700 dark:text-emerald-400">
                  <CircleCheck className="size-4" />
                  Your token bucket is currently at <strong>100% full capacity</strong>.
                </p>
              )}
            </CardContent>
          </Card>
        )}
      </section>

      <Separator />

      {/* Plan switcher */}
      <section className="flex flex-col gap-3">
        <div>
          <h3 className="flex items-center gap-2 text-lg font-bold">
            <Gem className="size-5 text-primary" />
            Subscription Plan Switcher
          </h3>
          <p className="text-sm text-muted-foreground">
            Switch between plans instantly with real-time role updates and quota privileges.
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <PlanCard plan={PLANS.free} active={activeFree} onDowngrade={downgrade} />
          <PlanCard plan={PLANS.pro} active={isPro} onUpgrade={() => setCheckoutOpen(true)} />
        </div>
      </section>

      <Separator />

      {/* Comparison matrix */}
      <section className="flex flex-col gap-3">
        <h3 className="flex items-center gap-2 text-lg font-bold">
          <BarChart3 className="size-5 text-primary" />
          Subscription Plan Comparison Matrix
        </h3>
        <div className="overflow-x-auto rounded-2xl glass-panel">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Feature / Capability</TableHead>
                <TableHead>Free Plan ($0)</TableHead>
                <TableHead className="text-primary">Pro Plan ($19/mo)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {MATRIX.map(([feature, free, pro]) => (
                <TableRow key={feature}>
                  <TableCell className="font-medium">{feature}</TableCell>
                  <TableCell className="text-muted-foreground">{free}</TableCell>
                  <TableCell className="font-semibold text-primary">{pro}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>

      <Separator />

      {/* Security */}
      <section className="flex flex-col gap-3">
        <h3 className="flex items-center gap-2 text-lg font-bold">
          <Lock className="size-5 text-primary" />
          Security, Credentials &amp; Session Management
        </h3>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base font-bold text-primary">
                <ShieldCheck className="size-4" />
                Session JWT Token Inspector
              </CardTitle>
              <CardDescription>
                Your session is protected with JSON Web Tokens signed via HMAC-SHA256 with
                automated expiration.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {jwtPayload ? (
                <div className="flex flex-col gap-1.5 rounded-lg border bg-muted/40 p-3 font-mono text-xs">
                  {Object.entries(jwtPayload).map(([key, value]) => (
                    <div key={key} className="flex gap-2">
                      <span className="w-16 shrink-0 text-muted-foreground">{key}</span>
                      <span className="break-all">
                        {key === 'exp' || key === 'iat'
                          ? `${value} (${new Date(value * 1000).toISOString()})`
                          : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No decodable session token found.</p>
              )}
            </CardContent>
          </Card>

          <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base font-bold text-emerald-600">
                <KeyRound className="size-4" />
                Update Account Password
              </CardTitle>
              <CardDescription>
                Passwords are encrypted with PBKDF2-SHA256 with 100,000 salt iterations before
                storage.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={submitPassword} className="flex flex-col gap-3">
                <FieldGroup>
                  <Field data-invalid={!!pwdErrors.current}>
                    <FieldLabel htmlFor="pwd-current">
                      <FieldTitle>Current Password</FieldTitle>
                    </FieldLabel>
                    <Input
                      id="pwd-current"
                      type="password"
                      value={pwd.current}
                      onChange={setPassword('current')}
                      autoComplete="current-password"
                    />
                    {pwdErrors.current && <FieldError>{pwdErrors.current}</FieldError>}
                  </Field>
                  <div className="grid grid-cols-2 gap-3">
                    <Field data-invalid={!!pwdErrors.next}>
                      <FieldLabel htmlFor="pwd-next">
                        <FieldTitle>New Password</FieldTitle>
                      </FieldLabel>
                      <Input
                        id="pwd-next"
                        type="password"
                        value={pwd.next}
                        onChange={setPassword('next')}
                        autoComplete="new-password"
                      />
                      {pwdErrors.next && <FieldError>{pwdErrors.next}</FieldError>}
                    </Field>
                    <Field data-invalid={!!pwdErrors.confirm}>
                      <FieldLabel htmlFor="pwd-confirm">
                        <FieldTitle>Confirm</FieldTitle>
                      </FieldLabel>
                      <Input
                        id="pwd-confirm"
                        type="password"
                        value={pwd.confirm}
                        onChange={setPassword('confirm')}
                        autoComplete="new-password"
                      />
                      {pwdErrors.confirm && <FieldError>{pwdErrors.confirm}</FieldError>}
                    </Field>
                  </div>
                </FieldGroup>
                <Button type="submit" className="w-full" disabled={pwdBusy}>
                  {pwdBusy && <Loader2 data-icon="inline-start" className="animate-spin" />}
                  Update Password
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Admin directory */}
      {isAdmin && (
        <>
          <Separator />
          <section className="flex flex-col gap-3">
            <h3 className="flex items-center gap-2 text-lg font-bold">
              <Users className="size-5 text-primary" />
              Member Directory &amp; Access Management
            </h3>
            <p className="text-sm text-muted-foreground">
              Administrator console for reviewing registered member accounts and managing their
              subscription plan.
            </p>

            {membersError && (
              <Alert variant="destructive">
                <AlertDescription>{membersError}</AlertDescription>
              </Alert>
            )}

            {members && (
              <>
                <p className="text-sm">
                  Total Registered Members:{' '}
                  <Badge variant="secondary" className="font-mono">
                    {members.length}
                  </Badge>
                </p>
                <div className="overflow-x-auto rounded-lg border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Username</TableHead>
                        <TableHead>Quota</TableHead>
                        <TableHead>Plan</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {members.map((m) => {
                        const proMember = ['pro', 'premium', 'newsroom_admin'].includes(m.role);
                        return (
                          <TableRow key={m.id ?? m.username}>
                            <TableCell className="font-mono text-muted-foreground">
                              #{m.id}
                            </TableCell>
                            <TableCell className="font-medium">{m.username}</TableCell>
                            <TableCell className="tabular-nums">
                              {proMember ? 'Unlimited' : `${Number(m.tokens ?? 0).toFixed(1)} / ${capacity}`}
                            </TableCell>
                            <TableCell>
                              <Badge variant={proMember ? 'default' : 'secondary'}>
                                {proMember ? 'PRO PLAN' : 'FREE PLAN'}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>

                <Card className="shadow-sm">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-base font-bold">
                      <Wrench className="size-4" />
                      Member Plan Modifier
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex flex-wrap items-end gap-3">
                    <div className="min-w-[200px] flex-1">
                      <p className="mb-1.5 text-sm font-medium">Select User Account</p>
                      <Select value={targetUser} onValueChange={setTargetUser}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Choose a member" />
                        </SelectTrigger>
                        <SelectContent>
                          {members.map((m) => (
                            <SelectItem key={m.username} value={m.username}>
                              {m.username}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="min-w-[220px] flex-1">
                      <p className="mb-1.5 text-sm font-medium">Assign Subscription Plan</p>
                      <Select value={targetRole} onValueChange={setTargetRole}>
                        <SelectTrigger className="w-full">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="user">
                            Free Plan (3 capacity, 2 resources)
                          </SelectItem>
                          <SelectItem value="pro">
                            Pro Plan (Unlimited, 3–5 resources)
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <Button onClick={applyRole} disabled={applying || !targetUser}>
                      {applying && <Loader2 data-icon="inline-start" className="animate-spin" />}
                      Apply Plan Change
                    </Button>
                  </CardContent>
                </Card>
              </>
            )}
          </section>
        </>
      )}

      <PaymentDialog open={checkoutOpen} onOpenChange={setCheckoutOpen} planId="pro" />
    </div>
  );
}
