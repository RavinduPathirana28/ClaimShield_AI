import React, { useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router';
import { toast } from 'sonner';
import { Gem, BarChart3 } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import PlanCards from '@/components/PlanCards';
import PaymentDialog from '@/components/PaymentDialog';
import { PLAN_MATRIX } from '@/lib/plans';
import { useAuth } from '@/context/AuthContext';

export default function PlansPage() {
  const { openAuth } = useOutletContext();
  const { isAuthenticated, isPro } = useAuth();
  const navigate = useNavigate();
  const [checkoutOpen, setCheckoutOpen] = useState(false);

  const handleChoose = (planId) => {
    if (planId === 'free') {
      if (!isAuthenticated) openAuth('register');
      else navigate('/account');
      return;
    }
    if (!isAuthenticated) {
      openAuth('register', 'pro');
    } else if (!isPro) {
      setCheckoutOpen(true);
    } else {
      toast.success('You are already on the Pro Plan.');
      navigate('/account');
    }
  };

  return (
    <div className="mx-auto max-w-5xl flex flex-col gap-10 px-4 py-12">
      <header className="text-center">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Pricing</p>
        <h1 className="mt-2 font-heading text-3xl font-extrabold tracking-tight sm:text-4xl">
          Simple, Transparent Plans
        </h1>
        <p className="mx-auto mt-2 max-w-xl text-sm text-muted-foreground sm:text-base">
          Start with our Free plan or upgrade to Pro for expanded evidence depth. Demo gateway —
          no real charge is made at checkout.
        </p>
      </header>

      <PlanCards onChoose={handleChoose} />

      <section className="flex flex-col gap-4">
        <h2 className="flex items-center gap-2 text-xl font-bold">
          <BarChart3 className="size-5 text-primary" />
          Subscription Plan Comparison Matrix
        </h2>
        <div className="overflow-x-auto rounded-2xl border border-border/60 bg-card/75 shadow-[0_8px_24px_-4px_rgba(0,0,0,0.03)] backdrop-blur-xl dark:border-white/10 dark:bg-card/65">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Feature / Capability</TableHead>
                <TableHead>Free Plan ($0)</TableHead>
                <TableHead className="text-primary">Pro Plan ($19/mo)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {PLAN_MATRIX.map(([feature, free, pro]) => (
                <TableRow key={feature}>
                  <TableCell className="font-medium">{feature}</TableCell>
                  <TableCell className="text-muted-foreground">{free}</TableCell>
                  <TableCell className="font-semibold text-primary">{pro}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Gem className="size-3.5" />
          Both plans include the full 5-agent pipeline, A2A protocol tracing, encrypted audit
          logs, and downloadable PDF reports.
        </p>
      </section>

      <PaymentDialog open={checkoutOpen} onOpenChange={setCheckoutOpen} planId="pro" />
    </div>
  );
}
