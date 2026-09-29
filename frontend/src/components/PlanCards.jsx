import React from 'react';
import { CircleCheck, Flame, Sparkles } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { PLANS, renderFeature } from '@/lib/plans';

/**
 * Shared Free/Pro plan cards — used by the landing preview and the public
 * plans page (kills the LandingPage ≈ PlansPage duplication).
 *
 * `onChoose('free' | 'pro')` is page-specific: register, checkout, etc.
 */
export default function PlanCards({ onChoose }) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {[PLANS.free, PLANS.pro].map((plan) => {
        const isPro = plan.id === 'pro';
        return (
          <Card
            key={plan.id}
            className={cn(
              'relative flex flex-col transition-all duration-200 hover:-translate-y-1',
              isPro
                ? 'border-2 border-primary/80 bg-primary/[0.02] shadow-xl shadow-primary/15'
                : 'border border-border/60 hover:border-border'
            )}
          >
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between gap-2">
                <CardTitle className="font-heading text-lg">{plan.name}</CardTitle>
                {isPro && (
                  <Badge className="gap-1">
                    <Sparkles className="size-3" />
                    Popular
                  </Badge>
                )}
              </div>
              <CardDescription>{plan.tagline}</CardDescription>
              <p className={cn('text-4xl font-extrabold', isPro ? 'text-primary' : '')}>
                {plan.priceLabel}
                {plan.price > 0 && (
                  <span className="text-sm font-normal text-muted-foreground">/mo</span>
                )}
              </p>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col">
              <ul className="mb-6 flex flex-col gap-2 text-sm text-muted-foreground">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2">
                    <CircleCheck
                      className={cn('mt-0.5 size-4 shrink-0', isPro ? 'text-primary' : 'text-emerald-600')}
                    />
                    <span>{renderFeature(feature)}</span>
                  </li>
                ))}
              </ul>
              <Button
                className="mt-auto w-full"
                variant={isPro ? 'default' : 'outline'}
                onClick={() => onChoose?.(plan.id)}
              >
                {isPro ? (
                  <>
                    <Flame data-icon="inline-start" />
                    Choose Pro Plan
                  </>
                ) : (
                  'Choose Free Plan'
                )}
              </Button>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
