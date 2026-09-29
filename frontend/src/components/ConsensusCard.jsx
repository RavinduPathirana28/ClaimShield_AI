import React from 'react';
import { Handshake, CircleCheck, TriangleAlert } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { verdictInfo, providerDot, truncate } from '@/lib/verdicts';

function ModelRow({ model }) {
  const conf = Math.round((model.confidence || 0) * 100);
  const info = verdictInfo(model.verdict);
  const snippet = truncate(model.straight_answer || model.summary || '');

  return (
    <div className="flex flex-col gap-2 rounded-xl glass-panel p-3.5">
      <div className="flex flex-wrap items-center gap-2">
        <span className={cn('size-2.5 shrink-0 rounded-full', providerDot(model.engine))} />
        <span className="text-sm font-medium">{model.engine || 'LLM'}</span>
        <Badge variant="outline" className={cn('ml-auto gap-1', info.badge)}>
          <info.icon className="size-3" />
          {model.verdict || 'Unverified'}
        </Badge>
      </div>
      <div className="flex items-center gap-2">
        <span className="w-10 shrink-0 text-right text-xs font-bold tabular-nums">{conf}%</span>
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
          <div
            className={cn('h-full rounded-full transition-all', info.bar)}
            style={{ width: `${Math.min(Math.max(conf, 4), 100)}%` }}
          />
        </div>
      </div>
      {snippet && <p className="text-xs leading-snug text-muted-foreground">{snippet}</p>}
    </div>
  );
}

export default function ConsensusCard({ agreementScore, modelResults = [] }) {
  const hasModels = modelResults.length > 0;
  const converged = agreementScore != null && agreementScore >= 0.7;
  const agreePct = agreementScore != null ? Math.round(agreementScore * 100) : null;

  return (
    <section className="flex flex-col gap-3">
      <h4 className="flex items-center gap-2 text-sm font-semibold tracking-tight">
        <Handshake className="size-4 text-muted-foreground" />
        Model consensus
      </h4>

      {hasModels ? (
        <div className="flex flex-col gap-2">
          {modelResults.map((model, idx) => (
            <ModelRow key={idx} model={model} />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-[var(--glass-secondary-border)] glass-panel p-3.5 text-sm leading-relaxed text-muted-foreground">
          <strong className="font-semibold text-foreground">No live LLM models were available.</strong>{' '}
          This verdict was produced by the built-in Local Heuristic Engine. Add working
          Groq / Gemini API keys or start Ollama to see the per-model comparison here.
        </div>
      )}

      {agreePct != null && (
        <div className="flex flex-col gap-1.5 rounded-xl glass-panel p-3.5">
          <div className="flex items-center justify-between gap-2 text-xs font-semibold">
            <span className={converged ? 'text-emerald-600' : 'text-amber-600'}>
              {converged ? (
                <span className="inline-flex items-center gap-1">
                  <CircleCheck className="size-3.5" /> The models converged on this verdict.
                </span>
              ) : (
                <span className="inline-flex items-center gap-1">
                  <TriangleAlert className="size-3.5" /> The models diverged — treat this verdict
                  with lower confidence.
                </span>
              )}
            </span>
            <span className={converged ? 'text-emerald-600' : 'text-amber-600'}>
              {agreePct}% agreement
            </span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
            <div
              className={cn('h-full rounded-full transition-all', converged ? 'bg-emerald-600' : 'bg-amber-600')}
              style={{ width: `${agreePct}%` }}
            />
          </div>
        </div>
      )}
    </section>
  );
}
