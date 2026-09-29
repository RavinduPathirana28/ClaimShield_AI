import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router';
import { toast } from 'sonner';
import { ShieldCheck, Loader2, KeyRound, UserPlus } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Field, FieldGroup, FieldLabel, FieldTitle, FieldError } from '@/components/ui/field';
import { useAuth } from '@/context/AuthContext';
import PaymentDialog from '@/components/PaymentDialog';

const DEMO_ACCOUNTS = [
  { username: 'user', password: 'password', label: 'Free', badge: 'secondary' },
  { username: 'pro', password: 'password', label: 'Pro', badge: 'default' },
  { username: 'premium', password: 'premium', label: 'Premium', badge: 'default' },
  { username: 'newsroom', password: 'newsroom', label: 'Admin', badge: 'outline' },
];

const EMPTY = { username: '', password: '', confirm: '' };

export default function AuthDialog({ open, onOpenChange, mode = 'login', plan }) {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [tab, setTab] = useState(mode);
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [planChoice, setPlanChoice] = useState('free');
  const [checkoutOpen, setCheckoutOpen] = useState(false);

  // Re-sync whenever the dialog opens (fixes stale initialMode-style bugs).
  useEffect(() => {
    if (open) {
      setTab(mode);
      setForm(EMPTY);
      setErrors({});
      setServerError(null);
      setPlanChoice(plan === 'pro' ? 'pro' : 'free');
    }
  }, [open, mode, plan]);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const afterAuth = (res) => {
    onOpenChange(false);
    navigate(location.state?.from || '/dashboard');
    return res;
  };

  const submitLogin = async (e) => {
    e.preventDefault();
    setServerError(null);
    const errs = {};
    if (!form.username.trim()) errs.username = 'Username is required.';
    if (!form.password) errs.password = 'Password is required.';
    setErrors(errs);
    if (Object.keys(errs).length) return;

    setBusy(true);
    try {
      const res = await login(form.username.trim(), form.password);
      toast.success(`Welcome back, ${res.username}`);
      afterAuth(res);
    } catch (err) {
      setServerError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const submitRegister = async (e) => {
    e.preventDefault();
    setServerError(null);
    const errs = {};
    if (form.username.trim().length < 3) errs.username = 'At least 3 characters.';
    if (form.password.length < 4) errs.password = 'At least 4 characters.';
    if (form.password !== form.confirm) errs.confirm = 'Passwords do not match.';
    setErrors(errs);
    if (Object.keys(errs).length) return;

    setBusy(true);
    try {
      // Pro signups register as Free first, then upgrade via checkout —
      // mirrors the Streamlit flow (pending_pro_checkout).
      const res = await register(form.username.trim(), form.password, 'user');
      if (planChoice === 'pro') {
        onOpenChange(false);
        setCheckoutOpen(true);
        toast.success('Account created', { description: 'Complete checkout to activate Pro.' });
      } else {
        toast.success(res.message || 'Account created');
        afterAuth(res);
      }
    } catch (err) {
      setServerError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const demoLogin = async (username, password) => {
    setServerError(null);
    setBusy(true);
    try {
      const res = await login(username, password);
      toast.success(`Welcome back, ${res.username}`);
      afterAuth(res);
    } catch (err) {
      setServerError(err.message);
      setBusy(false);
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 font-heading">
              <span className="flex size-7 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-xs shadow-primary/30">
                <ShieldCheck className="size-4" />
              </span>
              ClaimShield AI
            </DialogTitle>
            <DialogDescription>
              Sign in to run multi-agent claim verifications, or create a free account.
            </DialogDescription>
          </DialogHeader>

          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Sign in</TabsTrigger>
              <TabsTrigger value="register">Register</TabsTrigger>
            </TabsList>

            <TabsContent value="login" className="flex flex-col gap-4">
              <form onSubmit={submitLogin} className="flex flex-col gap-4">
                {serverError && (
                  <Alert variant="destructive">
                    <AlertDescription>{serverError}</AlertDescription>
                  </Alert>
                )}
                <FieldGroup>
                  <Field data-invalid={!!errors.username}>
                    <FieldLabel htmlFor="login-username">
                      <FieldTitle>Username</FieldTitle>
                    </FieldLabel>
                    <Input
                      id="login-username"
                      value={form.username}
                      onChange={set('username')}
                      autoComplete="username"
                      placeholder="e.g. pro"
                    />
                    {errors.username && <FieldError>{errors.username}</FieldError>}
                  </Field>
                  <Field data-invalid={!!errors.password}>
                    <FieldLabel htmlFor="login-password">
                      <FieldTitle>Password</FieldTitle>
                    </FieldLabel>
                    <Input
                      id="login-password"
                      type="password"
                      value={form.password}
                      onChange={set('password')}
                      autoComplete="current-password"
                      placeholder="••••••••"
                    />
                    {errors.password && <FieldError>{errors.password}</FieldError>}
                  </Field>
                </FieldGroup>
                <Button type="submit" className="w-full shadow-sm shadow-primary/25" disabled={busy}>
                  {busy && <Loader2 data-icon="inline-start" className="animate-spin" />}
                  <KeyRound data-icon="inline-start" />
                  Sign in
                </Button>
              </form>

              <div className="flex flex-col gap-2">
                <p className="text-center text-xs font-medium text-muted-foreground">
                  Demo accounts — click to sign in
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {DEMO_ACCOUNTS.map((acct) => (
                    <button
                      key={acct.username}
                      type="button"
                      disabled={busy}
                      onClick={() => demoLogin(acct.username, acct.password)}
                      className="flex items-center justify-between gap-1 rounded-xl border border-border/50 bg-background/50 px-3 py-2 text-left shadow-xs backdrop-blur-xs transition-all hover:border-primary/40 hover:bg-primary/5 disabled:opacity-50 dark:border-white/10 dark:bg-card/40"
                    >
                      <div className="min-w-0">
                        <p className="truncate font-mono text-xs font-medium">{acct.username}</p>
                        <p className="truncate text-[0.65rem] text-muted-foreground">
                          {acct.password}
                        </p>
                      </div>
                      <Badge variant={acct.badge} className="text-[0.6rem]">
                        {acct.label}
                      </Badge>
                    </button>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="register" className="flex flex-col gap-4">
              <form onSubmit={submitRegister} className="flex flex-col gap-4">
                {serverError && (
                  <Alert variant="destructive">
                    <AlertDescription>{serverError}</AlertDescription>
                  </Alert>
                )}
                <FieldGroup>
                  <Field data-invalid={!!errors.username}>
                    <FieldLabel htmlFor="reg-username">
                      <FieldTitle>Username</FieldTitle>
                    </FieldLabel>
                    <Input
                      id="reg-username"
                      value={form.username}
                      onChange={set('username')}
                      autoComplete="username"
                      placeholder="min. 3 characters"
                    />
                    {errors.username && <FieldError>{errors.username}</FieldError>}
                  </Field>
                  <div className="grid grid-cols-2 gap-3">
                    <Field data-invalid={!!errors.password}>
                      <FieldLabel htmlFor="reg-password">
                        <FieldTitle>Password</FieldTitle>
                      </FieldLabel>
                      <Input
                        id="reg-password"
                        type="password"
                        value={form.password}
                        onChange={set('password')}
                        autoComplete="new-password"
                        placeholder="min. 4 chars"
                      />
                      {errors.password && <FieldError>{errors.password}</FieldError>}
                    </Field>
                    <Field data-invalid={!!errors.confirm}>
                      <FieldLabel htmlFor="reg-confirm">
                        <FieldTitle>Confirm</FieldTitle>
                      </FieldLabel>
                      <Input
                        id="reg-confirm"
                        type="password"
                        value={form.confirm}
                        onChange={set('confirm')}
                        autoComplete="new-password"
                        placeholder="repeat"
                      />
                      {errors.confirm && <FieldError>{errors.confirm}</FieldError>}
                    </Field>
                  </div>
                  <Field>
                    <FieldLabel>
                      <FieldTitle>Plan</FieldTitle>
                    </FieldLabel>
                    <ToggleGroup
                      type="single"
                      variant="outline"
                      value={planChoice}
                      onValueChange={(v) => v && setPlanChoice(v)}
                      className="w-full"
                    >
                      <ToggleGroupItem value="free" className="flex-1">
                        Free · $0
                      </ToggleGroupItem>
                      <ToggleGroupItem value="pro" className="flex-1">
                        Pro · $19/mo
                      </ToggleGroupItem>
                    </ToggleGroup>
                    <p className="text-xs text-muted-foreground">
                      {planChoice === 'pro'
                        ? 'You will register, then complete a demo checkout to activate Pro.'
                        : 'Start free — upgrade any time from Account & Plan.'}
                    </p>
                  </Field>
                </FieldGroup>
                <Button type="submit" className="w-full" disabled={busy}>
                  {busy && <Loader2 data-icon="inline-start" className="animate-spin" />}
                  <UserPlus data-icon="inline-start" />
                  Create account
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

      <PaymentDialog open={checkoutOpen} onOpenChange={setCheckoutOpen} planId="pro" />
    </>
  );
}
