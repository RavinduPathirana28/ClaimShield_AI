import React from 'react';
import { Compass, ArrowRight } from 'lucide-react';

// Category chip tones for LLM-generated suggestions. Kept inside the site's
// amber/rose/sky/blue/teal/emerald palette so no off-palette hues creep in.
const CATEGORY_TONES = {
  'myth check': 'border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400',
  'counter-claim': 'border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-400',
  'key statistic': 'border-sky-500/30 bg-sky-500/10 text-sky-600 dark:text-sky-400',
  statistic: 'border-sky-500/30 bg-sky-500/10 text-sky-600 dark:text-sky-400',
  'follow-up fact': 'border-blue-500/30 bg-blue-500/10 text-blue-600 dark:text-blue-400',
  'recent development': 'border-teal-500/30 bg-teal-500/10 text-teal-600 dark:text-teal-400',
  'new development': 'border-teal-500/30 bg-teal-500/10 text-teal-600 dark:text-teal-400',
  'broader context': 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  context: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
};

const toneFor = (label) =>
  CATEGORY_TONES[String(label || '').toLowerCase().trim()] ||
  'border-primary/30 bg-primary/10 text-primary';

export default function Recommendations({ recommendations, onSelectClaim }) {
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <section className="rounded-2xl glass-card p-5 sm:p-6">
      <div className="flex items-center gap-2">
        <span className="flex size-8 items-center justify-center rounded-xl bg-primary/10 text-primary shadow-xs">
          <Compass className="size-4.5" />
        </span>
        <h3 className="text-base font-bold leading-tight">Explore Related Claims</h3>
      </div>

      <div className="mt-3 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
        {recommendations.map((rec, idx) => {
          const claim = typeof rec === 'string' ? rec : rec.claim || rec.title || '';
          const source = typeof rec === 'object' ? rec.source || 'Related claim' : 'Related claim';
          const sim =
            typeof rec === 'object' && rec.similarity != null
              ? Math.round(Number(rec.similarity) * 100)
              : null;

          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectClaim(claim)}
              className="group rounded-xl glass-card glass-card-interactive p-3.5 text-left"
            >
              <span className="flex items-center gap-2">
                <span className="flex size-5 shrink-0 items-center justify-center rounded-md bg-primary/10 text-[0.7rem] font-bold text-primary">
                  {idx + 1}
                </span>
                <span
                  className={`truncate rounded-full border px-2 py-0.5 text-[0.65rem] font-semibold ${toneFor(
                    source,
                  )}`}
                >
                  {source}
                </span>
                <ArrowRight className="ml-auto size-4 shrink-0 text-primary transition-transform group-hover:translate-x-0.5" />
              </span>
              <span className="mt-2 line-clamp-2 block text-sm font-medium leading-snug group-hover:text-primary">
                {claim}
              </span>
              <span className="mt-1.5 block text-xs text-muted-foreground">
                {sim != null ? `~${sim}% related` : 'Related claim'}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
