import { CircleCheck, CircleX, MessageSquareText, CircleHelp } from 'lucide-react';

const SHARED = {
  supported: {
    label: 'Verified True',
    icon: CircleCheck,
    badge: 'border-emerald-600/40 bg-emerald-600/10 text-emerald-700 dark:text-emerald-400',
    accent: 'text-emerald-600 dark:text-emerald-400',
    border: 'border-emerald-600',
    bar: 'bg-emerald-600',
    dot: 'bg-emerald-600',
  },
  contradicted: {
    label: 'Debunked / False',
    icon: CircleX,
    badge: 'border-red-600/40 bg-red-600/10 text-red-700 dark:text-red-400',
    accent: 'text-red-600 dark:text-red-400',
    border: 'border-red-600',
    bar: 'bg-red-600',
    dot: 'bg-red-600',
  },
  answered: {
    label: 'Direct Answer',
    icon: MessageSquareText,
    badge: 'border-primary/40 bg-primary/10 text-primary',
    accent: 'text-primary',
    border: 'border-primary',
    bar: 'bg-primary',
    dot: 'bg-primary',
  },
  unverified: {
    label: 'Unverified',
    icon: CircleHelp,
    badge: 'border-amber-600/40 bg-amber-600/10 text-amber-700 dark:text-amber-500',
    accent: 'text-amber-600 dark:text-amber-500',
    border: 'border-amber-600',
    bar: 'bg-amber-600',
    dot: 'bg-amber-600',
  },
};

const VERDICT_MAP = {
  Supported: SHARED.supported,
  True: SHARED.supported,
  Contradicted: SHARED.contradicted,
  False: SHARED.contradicted,
  Answered: SHARED.answered,
  'General Info': SHARED.answered,
  Unverified: SHARED.unverified,
  Unclear: SHARED.unverified,
};

export function verdictInfo(verdict) {
  return VERDICT_MAP[verdict] || { ...SHARED.unverified, label: verdict || 'Unverified' };
}

export const PROVIDER_DOTS = [
  ['Groq', 'bg-orange-500'],
  ['Gemini', 'bg-blue-500'],
  ['Ollama', 'bg-teal-600'],
];

export function providerDot(engineName) {
  const match = PROVIDER_DOTS.find(([name]) => (engineName || '').includes(name));
  return match ? match[1] : 'bg-muted-foreground';
}

export function truncate(text, max = 160) {
  const value = (text || '').trim();
  if (value.length <= max) return value;
  return `${value.slice(0, max).replace(/\s+\S*$/, '')}…`;
}
