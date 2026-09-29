import React, { useEffect, useState } from 'react';
import { ShieldCheck, Dna, Search, BookOpen, Handshake, ClipboardCheck, Check } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

const STEPS = [
  { icon: ShieldCheck, title: 'Security Check', detail: 'Sanitizing input & token-bucket rate limits' },
  { icon: Dna, title: 'Parse & Extract', detail: 'spaCy NER extraction & query generation' },
  { icon: Search, title: 'Vector Retrieval', detail: 'FAISS vector search over the corpus' },
  { icon: BookOpen, title: 'Context & Summaries', detail: 'Building extractive evidence summary' },
  { icon: Handshake, title: 'Model Consensus', detail: 'Collecting Groq & Gemini verdicts' },
  { icon: ClipboardCheck, title: 'Verdict & Audit', detail: 'Persisting encrypted audit trail' },
];

/**
 * Live pipeline progress driven by real SSE `step` events (no timers).
 * `events` accumulates `{ step, label, detail }` frames from /api/verify/stream.
 */
export default function PipelineLoader({ events = [] }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const timer = setInterval(() => setElapsed((Date.now() - started) / 1000), 100);
    return () => clearInterval(timer);
  }, []);

  const activeStep = events.reduce((max, ev) => Math.max(max, ev.step ?? -1), -1);
  const lastEvent = events[events.length - 1];
  const detail = lastEvent?.detail || 'Booting the multi-agent pipeline…';
  const pct = activeStep >= 0 ? Math.round(((activeStep + 1) / STEPS.length) * 100) : 0;

  return (
    <div className="my-6 rounded-2xl glass-card p-5">
      <div className="flex items-center gap-2">
        <span className="relative flex size-2.5">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-primary opacity-60" />
          <span className="relative inline-flex size-2.5 rounded-full bg-primary" />
        </span>
        <span className="text-sm font-bold">Multi-Agent Verification Running</span>
        <span className="ml-auto rounded-full glass-pill px-2.5 py-0.5 text-xs font-bold tabular-nums">
          {pct}%
        </span>
      </div>

      <div className="my-4 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {STEPS.map((step, idx) => {
          const isDone = activeStep >= 0 && idx < activeStep;
          const isActive = idx === activeStep;
          return (
            <div
              key={step.title}
              className={cn(
                'flex items-center gap-2.5 rounded-xl border px-3 py-2.5 backdrop-blur-md transition-all duration-150',
                isActive && 'border-primary/60 bg-primary/10 shadow-xs shadow-primary/15',
                isDone && 'border-emerald-600/35 bg-emerald-600/10 text-emerald-700 dark:text-emerald-400',
                !isActive && !isDone && 'glass-panel text-muted-foreground'
              )}
            >
              <span
                className={cn(
                  'flex size-7.5 shrink-0 items-center justify-center rounded-xl',
                  isActive && 'bg-primary text-primary-foreground shadow-xs shadow-primary/30',
                  isDone && 'bg-emerald-600 text-white',
                  !isActive && !isDone && 'bg-muted text-muted-foreground'
                )}
              >
                {isDone ? <Check className="size-4" /> : <step.icon className="size-4" />}
              </span>
              <div className="min-w-0">
                <div
                  className={cn(
                    'truncate text-xs font-semibold',
                    isActive && 'text-primary',
                    isDone && 'text-foreground',
                    !isActive && !isDone && 'text-muted-foreground'
                  )}
                >
                  {step.title}
                </div>
                <div className="text-[0.65rem] text-muted-foreground">
                  {isActive ? 'Running' : isDone ? 'Done' : 'Queued'}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <Progress value={pct} className="h-1.5" />

      <div className="mt-2.5 flex items-center justify-between gap-3 text-xs text-muted-foreground">
        <span className="truncate">
          <strong className="text-primary">{STEPS[Math.max(activeStep, 0)].title}</strong> — {detail}
        </span>
        <span className="shrink-0 tabular-nums">{elapsed.toFixed(1)}s</span>
      </div>
    </div>
  );
}
