import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { toast } from 'sonner';
import { CreditCard, Lock, ShieldCheck, CircleCheck, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Field, FieldGroup, FieldLabel, FieldTitle, FieldError } from '@/components/ui/field';
import { PLANS, PRO_FEATURES_SHORT } from '@/lib/plans';
import { useAuth } from '@/context/AuthContext';
import * as api from '@/services/api';

const EMPTY_FORM = {
  cardholder_name: '',
  card_number: '',
  expiry: '',
  cvv: '',
};

export default function PaymentDialog({ open, onOpenChange, planId = 'pro' }) {
  const plan = PLANS[planId] || PLANS.pro;
  const { token, saveToken, refreshProfile } = useAuth();
  const navigate = useNavigate();

  const [step, setStep] = useState('form');
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [receipt, setReceipt] = useState(null);

  useEffect(() => {
    if (open) {
      setStep('form');
      setForm(EMPTY_FORM);
      setErrors({});
      setServerError(null);
      setReceipt(null);
    }
  }, [open]);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const validate = () => {
    const errs = {};
    if (!form.cardholder_name.trim()) errs.cardholder_name = 'Cardholder name is required.';
    const digits = form.card_number.replace(/\D/g, '');
    if (digits.length < 15 || digits.length > 16) errs.card_number = 'Enter a 15–16 digit card number.';
    if (!/^\d{2}\/\d{2}$/.test(form.expiry.trim())) errs.expiry = 'Use MM/YY format.';
    if (!/^\d{3,4}$/.test(form.cvv.trim())) errs.cvv = '3 or 4 digits.';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const submit = async (e) => {
    e.preventDefault();
    setServerError(null);
    if (!validate()) return;
    setSubmitting(true);
    try {
      const res = await api.checkout(token, { ...form, plan: plan.id });
      saveToken(res.token);
      await refreshProfile();
      setReceipt(res.receipt);
      setStep('success');
      toast.success('Pro plan activated', {
        description: `Transaction ${res.receipt?.transaction_id ?? ''} approved.`,
      });
    } catch (err) {
      setServerError(err.message || 'Payment failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const goTo = (path) => {
    onOpenChange(false);
    navigate(path);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 font-heading">
            {step === 'form' ? (
              <>
                <CreditCard className="size-4 text-primary" />
                Secure Checkout
              </>
            ) : (
              <>
                <CircleCheck className="size-4 text-primary" />
                Payment Approved
              </>
            )}
          </DialogTitle>
          <DialogDescription>
            {step === 'form'
              ? 'Demo gateway — no real charge is made.'
              : 'Your plan has been upgraded and your new session token is active.'}
          </DialogDescription>
        </DialogHeader>

        {step === 'form' ? (
          <form onSubmit={submit} className="flex flex-col gap-4">
            <div className="rounded-xl border border-border/50 bg-background/50 p-3.5 shadow-xs backdrop-blur-xs dark:border-white/10 dark:bg-card/40">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold">{plan.name}</p>
                  <p className="text-xs text-muted-foreground">Billed monthly · cancel anytime</p>
                </div>
                <p className="text-lg font-semibold text-primary">
                  {plan.priceLabel}
                  <span className="text-xs font-normal text-muted-foreground">/mo</span>
                </p>
              </div>
              <ul className="mt-2 flex flex-col gap-1">
                {PRO_FEATURES_SHORT.map((f) => (
                  <li key={f} className="flex items-start gap-1.5 text-xs text-muted-foreground">
                    <ShieldCheck className="mt-0.5 size-3 shrink-0 text-primary" />
                    {f}
                  </li>
                ))}
              </ul>
            </div>

            {serverError && (
              <Alert variant="destructive">
                <AlertDescription>{serverError}</AlertDescription>
              </Alert>
            )}

            <FieldGroup>
              <Field data-invalid={!!errors.cardholder_name}>
                <FieldLabel htmlFor="cardholder_name">
                  <FieldTitle>Cardholder name</FieldTitle>
                </FieldLabel>
                <Input
                  id="cardholder_name"
                  value={form.cardholder_name}
                  onChange={set('cardholder_name')}
                  placeholder="Name as printed on card"
                  autoComplete="cc-name"
                />
                {errors.cardholder_name && <FieldError>{errors.cardholder_name}</FieldError>}
              </Field>

              <Field data-invalid={!!errors.card_number}>
                <FieldLabel htmlFor="card_number">
                  <FieldTitle>Card number</FieldTitle>
                </FieldLabel>
                <div className="relative">
                  <Input
                    id="card_number"
                    value={form.card_number}
                    onChange={set('card_number')}
                    placeholder="1234 5678 9012 3456"
                    inputMode="numeric"
                    autoComplete="cc-number"
                    className="pr-9 font-mono"
                  />
                  <CreditCard className="absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                </div>
                {errors.card_number && <FieldError>{errors.card_number}</FieldError>}
              </Field>

              <div className="grid grid-cols-2 gap-3">
                <Field data-invalid={!!errors.expiry}>
                  <FieldLabel htmlFor="expiry">
                    <FieldTitle>Expiry</FieldTitle>
                  </FieldLabel>
                  <Input
                    id="expiry"
                    value={form.expiry}
                    onChange={set('expiry')}
                    placeholder="MM/YY"
                    autoComplete="cc-exp"
                    className="font-mono"
                  />
                  {errors.expiry && <FieldError>{errors.expiry}</FieldError>}
                </Field>

                <Field data-invalid={!!errors.cvv}>
                  <FieldLabel htmlFor="cvv">
                    <FieldTitle>CVV</FieldTitle>
                  </FieldLabel>
                  <Input
                    id="cvv"
                    value={form.cvv}
                    onChange={set('cvv')}
                    type="password"
                    placeholder="CVV"
                    inputMode="numeric"
                    autoComplete="cc-csc"
                    className="font-mono"
                  />
                  {errors.cvv && <FieldError>{errors.cvv}</FieldError>}
                </Field>
              </div>
            </FieldGroup>

            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Lock className="size-3" />
              Encrypted in transit · demo test card <span className="font-mono">4242 4242 4242 4242</span>
            </p>

            <DialogFooter className="gap-2 sm:gap-2">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="shadow-sm shadow-primary/25">
                {submitting && <Loader2 data-icon="inline-start" className="animate-spin" />}
                Pay {plan.priceLabel}.00
              </Button>
            </DialogFooter>
          </form>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4 text-center backdrop-blur-xs">
              <CircleCheck className="mx-auto size-8 text-primary" />
              <p className="mt-2 text-lg font-semibold">
                {receipt?.plan_name ?? plan.name} active
              </p>
              <p className="text-sm text-muted-foreground">
                ${Number(receipt?.amount ?? plan.price).toFixed(2)} {receipt?.currency ?? 'USD'} ·{' '}
                {receipt?.gateway ?? 'ClaimShield Pay (Demo)'}
              </p>
            </div>

            <div className="flex flex-col gap-1.5 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Transaction ID</span>
                <span className="font-mono">{receipt?.transaction_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Card</span>
                <span className="font-mono">
                  {receipt?.card_brand} •••• {receipt?.card_last4}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Time</span>
                <span className="font-mono text-xs">{receipt?.timestamp}</span>
              </div>
            </div>

            <Separator />

            <div className="flex flex-col gap-2 sm:flex-row-reverse">
              <Button className="flex-1" onClick={() => goTo('/dashboard')}>
                Go to Dashboard
              </Button>
              <Button variant="outline" className="flex-1" onClick={() => goTo('/account')}>
                Account Details
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
