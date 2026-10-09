import React, { useEffect, useState, useCallback } from 'react';
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

function GoogleIcon(props) {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" {...props}>
      <path
        fill="#4285F4"
        d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
      />
      <path
        fill="#FBBC05"
        d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.98 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
      />
      <path
        fill="#EA4335"
        d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
      />
    </svg>
  );
}

const EMPTY = { username: '', password: '', confirm: '' };

export default function AuthDialog({ open, onOpenChange, mode = 'login', plan }) {
  const { login, register, loginWithGoogle } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const googleClientId =
    import.meta.env.VITE_GOOGLE_CLIENT_ID ||
    import.meta.env.GOOGLE_CLIENT_ID ||
    '';
  const [googleBusy, setGoogleBusy] = useState(false);
  const [googlePromptOpen, setGooglePromptOpen] = useState(false);
  const [demoGoogleEmail, setDemoGoogleEmail] = useState('alex.researcher@gmail.com');

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

  const handleGoogleSuccess = useCallback(async (credential) => {
    setServerError(null);
    setGoogleBusy(true);
    try {
      const res = await loginWithGoogle(credential);
      notifyLoginSuccess(res);
      afterAuth(res);
    } catch (err) {
      setServerError(err.message || 'Google sign-in failed.');
    } finally {
      setGoogleBusy(false);
    }
  }, [loginWithGoogle]);

  // Render Google Identity Services button whenever container mounts
  const renderGoogleBtn = useCallback((node) => {
    if (!node || !googleClientId || !window.google?.accounts?.id) return;
    try {
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: (resp) => {
          if (resp.credential) handleGoogleSuccess(resp.credential);
        },
        auto_select: false,
      });
      node.innerHTML = '';
      window.google.accounts.id.renderButton(node, {
        theme: 'outline',
        size: 'large',
        width: 320,
        text: tab === 'register' ? 'signup_with' : 'signin_with',
        shape: 'pill',
      });
    } catch (err) {
      console.warn('GIS renderButton note:', err);
    }
  }, [googleClientId, tab, handleGoogleSuccess]);

  const onGoogleBtnClick = () => {
    if (!googleClientId) {
      setGooglePromptOpen(true);
      return;
    }

    // Modern Google OAuth 2.0 Token Client popup (guaranteed popup on click)
    if (window.google?.accounts?.oauth2) {
      try {
        const tokenClient = window.google.accounts.oauth2.initTokenClient({
          client_id: googleClientId,
          scope: 'openid email profile',
          callback: async (tokenResponse) => {
            if (tokenResponse.error) {
              setServerError(`Google sign-in canceled or failed: ${tokenResponse.error}`);
              return;
            }
            if (tokenResponse.access_token) {
              setGoogleBusy(true);
              try {
                const userRes = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
                  headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
                });
                const profile = await userRes.json();
                if (profile.email) {
                  const authRes = await loginWithGoogle(`demo_google_${profile.email}`);
                  notifyLoginSuccess(authRes);
                  afterAuth(authRes);
                } else {
                  throw new Error('Google did not return an email address.');
                }
              } catch (err) {
                setServerError(err.message || 'Failed to retrieve Google profile.');
              } finally {
                setGoogleBusy(false);
              }
            }
          },
        });
        tokenClient.requestAccessToken({ prompt: 'select_account' });
        return;
      } catch (e) {
        console.warn('Google tokenClient initialization note:', e);
      }
    }

    // Fallback: try One Tap or open quick sign-in modal
    if (window.google?.accounts?.id) {
      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          setGooglePromptOpen(true);
        }
      });
    } else {
      setGooglePromptOpen(true);
    }
  };

  const handleDemoGoogleLogin = async () => {
    setGooglePromptOpen(false);
    setServerError(null);
    setGoogleBusy(true);
    try {
      const email = demoGoogleEmail.trim() || 'alex.researcher@gmail.com';
      const res = await loginWithGoogle(`demo_google_${email}`);
      notifyLoginSuccess(res);
      afterAuth(res);
    } catch (err) {
      setServerError(err.message || 'Google sign-in failed.');
    } finally {
      setGoogleBusy(false);
    }
  };


  const notifyLoginSuccess = (userRes) => {
    const isPro = ['pro', 'premium'].includes(userRes.role);
    const isAdmin = userRes.role === 'newsroom_admin';

    const roleLabel = isAdmin ? 'Newsroom Admin' : isPro ? 'Pro Member' : 'Free Tier';
    const roleDescription = isAdmin
      ? 'Administrative tools, full audit logs, and member governance are active.'
      : isPro
      ? 'Pro plan active — 5-source retrieval and multi-model consensus ready.'
      : 'Ready to verify claims with AI consensus and live web search.';

    toast.success(`Welcome back, ${userRes.username}`, {
      className: '!p-4 sm:!p-5 !min-w-[340px] sm:!min-w-[420px] !rounded-2xl !border-border/80 shadow-2xl backdrop-blur-md',
      classNames: {
        title: '!text-base sm:!text-lg !font-semibold text-foreground tracking-tight',
        description: '!text-sm text-muted-foreground mt-1',
        icon: '!size-5 sm:!size-6 text-emerald-500',
      },
      description: (
        <div className="flex flex-col gap-2.5 mt-1.5">
          <p className="text-sm font-normal text-muted-foreground leading-relaxed">
            {roleDescription}
          </p>
          <div className="flex items-center gap-2 pt-0.5">
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary border border-primary/20">
              <ShieldCheck className="size-3.5 text-primary" />
              {roleLabel}
            </span>
            <span className="text-xs text-muted-foreground font-medium">• Session active</span>
          </div>
        </div>
      ),
      duration: 5000,
    });
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
      notifyLoginSuccess(res);
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
        toast.success(`Welcome to ClaimShield, ${res.username}`, {
          className: '!p-4 sm:!p-5 !min-w-[340px] sm:!min-w-[420px] !rounded-2xl !border-border/80 shadow-2xl backdrop-blur-md',
          classNames: {
            title: '!text-base sm:!text-lg !font-semibold text-foreground tracking-tight',
            description: '!text-sm text-muted-foreground mt-1',
            icon: '!size-5 sm:!size-6 text-emerald-500',
          },
          description: 'Account created successfully. Complete checkout to activate Pro features.',
          duration: 5000,
        });
      } else {
        toast.success(`Welcome to ClaimShield, ${res.username}`, {
          className: '!p-4 sm:!p-5 !min-w-[340px] sm:!min-w-[420px] !rounded-2xl !border-border/80 shadow-2xl backdrop-blur-md',
          classNames: {
            title: '!text-base sm:!text-lg !font-semibold text-foreground tracking-tight',
            description: '!text-sm text-muted-foreground mt-1',
            icon: '!size-5 sm:!size-6 text-emerald-500',
          },
          description: 'Your account is ready. Start verifying claims and exploring facts.',
          duration: 5000,
        });
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
      notifyLoginSuccess(res);
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

          {/* Google Sign In Section */}
          <div className="flex flex-col gap-2.5 pt-1">
            {googleClientId ? (
              <div ref={renderGoogleBtn} className="w-full flex justify-center min-h-[40px]" />
            ) : null}

            <Button
              type="button"
              variant="outline"
              disabled={busy || googleBusy}
              onClick={onGoogleBtnClick}
              className="w-full flex items-center justify-center gap-2.5 rounded-xl border-border/80 hover:bg-accent/60 transition-all font-medium py-2.5 shadow-xs"
            >
              {googleBusy ? (
                <Loader2 className="size-4 animate-spin text-muted-foreground" />
              ) : (
                <GoogleIcon />
              )}
              <span>Continue with Google</span>
              {!googleClientId && (
                <span className="ml-1 text-[10px] text-muted-foreground font-mono bg-muted/80 border px-1.5 py-0.5 rounded">
                  Demo ready
                </span>
              )}
            </Button>

            <div className="relative my-1 flex items-center justify-center">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border/80" />
              </div>
              <span className="relative bg-background px-3 text-[11px] uppercase tracking-wider text-muted-foreground font-medium">
                Or with credentials
              </span>
            </div>
          </div>

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
                      className="flex items-center justify-between gap-1 rounded-xl glass-panel px-3 py-2 text-left transition-all hover:border-primary/40 hover:bg-primary/5 disabled:opacity-50"
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

      {/* Google Setup / Quick-Sign-in Dialog */}
      <Dialog open={googlePromptOpen} onOpenChange={setGooglePromptOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 font-heading">
              <GoogleIcon />
              Sign in with Google
            </DialogTitle>
            <DialogDescription>
              Single Sign-On authentication for ClaimShield AI.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4 py-2">
            <Alert className="border-primary/20 bg-primary/5">
              <AlertDescription className="text-xs text-muted-foreground leading-relaxed">
                <strong>Google Identity Setup:</strong> To link a production Google Cloud client, configure{' '}
                <code className="text-foreground font-mono text-[11px] bg-muted px-1 py-0.5 rounded">
                  VITE_GOOGLE_CLIENT_ID
                </code>{' '}
                and backend{' '}
                <code className="text-foreground font-mono text-[11px] bg-muted px-1 py-0.5 rounded">
                  GOOGLE_CLIENT_ID
                </code>. You can also sign in instantly using the demo profile below:
              </AlertDescription>
            </Alert>

            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="demo-google-email">
                  <FieldTitle>Google Account Email</FieldTitle>
                </FieldLabel>
                <Input
                  id="demo-google-email"
                  value={demoGoogleEmail}
                  onChange={(e) => setDemoGoogleEmail(e.target.value)}
                  placeholder="e.g. alex.researcher@gmail.com"
                />
              </Field>
            </FieldGroup>

            <div className="flex gap-2 justify-end pt-2">
              <Button variant="ghost" onClick={() => setGooglePromptOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleDemoGoogleLogin} disabled={googleBusy} className="gap-2">
                {googleBusy ? <Loader2 className="size-4 animate-spin" /> : <GoogleIcon />}
                Sign in with Google
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
