import React from 'react';
import {
  Bot,
  Search,
  Scale,
  Brain,
  Lightbulb,
  Lock,
  UserRound,
  Globe,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

const PILLARS = [
  {
    icon: Search,
    title: 'Transparency & Auditability',
    badge: 'Fully Traceable',
    tone: 'text-emerald-600',
    badgeTone: 'border-emerald-600/40 bg-emerald-600/10 text-emerald-700 dark:text-emerald-400',
    desc: 'Every verification result provides full source attribution, cosine similarity metrics, and an immutable AES-256 encrypted audit trail for regulatory compliance.',
  },
  {
    icon: Scale,
    title: 'Algorithmic Fairness',
    badge: 'Uniform Verification',
    tone: 'text-amber-600',
    badgeTone: 'border-amber-600/40 bg-amber-600/10 text-amber-700 dark:text-amber-500',
    desc: 'Our semantic pipeline evaluates statements without user demographic profiling, ensuring objective verdicts across scientific, historical, and sociopolitical topics.',
  },
  {
    icon: Brain,
    title: 'Grounding & Bias Mitigation',
    badge: 'Multi-LLM Consensus',
    tone: 'text-primary',
    badgeTone: 'border-primary/40 bg-primary/10 text-primary',
    desc: 'Dual-model consensus (Groq Llama-3.3-70b + Google Gemini-2.5) strictly penalizes ungrounded hallucinations, requiring retrieved factual documents before issuing positive verdicts.',
  },
  {
    icon: Lightbulb,
    title: 'Multi-Layer Explainability',
    badge: 'Transparent Rationale',
    tone: 'text-cyan-600',
    badgeTone: 'border-cyan-600/40 bg-cyan-600/10 text-cyan-700 dark:text-cyan-400',
    desc: 'Provides plain-language explanations, specific cited article snippets, and confidence scores so end-users can independently verify reasoning.',
  },
  {
    icon: Lock,
    title: 'Cryptographic Security',
    badge: 'Defense in Depth',
    tone: 'text-red-600',
    badgeTone: 'border-red-600/40 bg-red-600/10 text-red-700 dark:text-red-400',
    desc: 'Token-bucket rate limiting against DDoS and prompt injection sanitization protect backend reasoning infrastructure.',
  },
  {
    icon: UserRound,
    title: 'User Data Rights & Privacy',
    badge: 'Privacy Protected',
    tone: 'text-sky-600',
    badgeTone: 'border-sky-600/40 bg-sky-600/10 text-sky-700 dark:text-sky-400',
    desc: 'User queries are processed transiently and personal audit records are encrypted. We never sell or train public foundation models on private user submissions.',
  },
];

export default function ResponsibleAIPage() {
  return (
    <div className="mx-auto max-w-5xl flex flex-col gap-8 px-4 py-12">
      <header className="text-center">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-primary">
          Ethics & Governance
        </p>
        <h1 className="mt-2 flex flex-wrap items-center justify-center gap-2 font-heading text-3xl font-extrabold tracking-tight sm:text-4xl">
          <Bot className="size-8 text-primary" />
          Responsible AI, Ethics &amp; Governance
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-sm text-muted-foreground sm:text-base">
          ClaimShield AI is architected with Responsible AI principles at its foundation —
          guaranteeing fairness, explainability, safety, and verifiable evidence.
        </p>
      </header>

      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {PILLARS.map((pillar) => (
          <Card
            key={pillar.title}
            className="transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
          >
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className={cn('flex items-center gap-2 text-base font-bold', pillar.tone)}>
                  <pillar.icon className="size-4.5" />
                  {pillar.title}
                </CardTitle>
                <Badge variant="outline" className={cn('shrink-0 text-[0.65rem]', pillar.badgeTone)}>
                  {pillar.badge}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="text-sm leading-relaxed text-muted-foreground">
              {pillar.desc}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-emerald-600/40 bg-emerald-600/10 text-center shadow-sm">
        <CardContent className="flex flex-col gap-3 pt-6">
          <span className="mx-auto flex size-12 items-center justify-center rounded-full bg-emerald-600 text-white">
            <Globe className="size-6" />
          </span>
          <h2 className="font-heading text-xl font-bold text-emerald-800 dark:text-emerald-400">
            Global Responsible AI Commitment
          </h2>
          <p className="mx-auto max-w-3xl text-sm leading-relaxed text-emerald-700 dark:text-emerald-500">
            We commit to upholding open standards in computational truth verification. Every piece
            of retrieved evidence is cited with transparent scoring, multi-model consensus, and
            human-in-the-loop oversight.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
