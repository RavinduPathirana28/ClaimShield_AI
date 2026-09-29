import React from 'react';
import { useNavigate, useOutletContext, Link } from 'react-router';
import {
  Shield,
  ArrowRight,
  KeyRound,
  Coins,
  Zap,
  ClipboardList,
  Globe,
  Brain,
  Bot,
  Lock,
  Route,
  BarChart3,
  Dna,
  Search,
  Scale,
  Lightbulb,
  CircleCheck,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TypingAnimation } from '@/components/ui/typing-animation';
import PlanCards from '@/components/PlanCards';
import { useAuth } from '@/context/AuthContext';

const HERO_SUBTITLE =
  'ClaimShield AI is an agentic fact-verification platform using 5 AI agents, RAG, and multi-LLM consensus to deliver transparent, evidence-backed verdicts.';

const STATS = [
  { value: '5', label: 'Specialized Agents' },
  { value: '3', label: 'LLM Consensus Models' },
  { value: 'A2A', label: 'Messaging Protocol' },
  { value: 'FAISS', label: 'Vector Retrieval' },
];

const TRUST = [
  { icon: KeyRound, label: 'PBKDF2-SHA256 Hashing' },
  { icon: Coins, label: 'JWT Session Tokens' },
  { icon: Zap, label: 'Token-Bucket Rate Limiting' },
  { icon: ClipboardList, label: 'Encrypted Audit Trails' },
  { icon: Globe, label: 'LangGraph Stateful Workflow' },
];

const FEATURES = [
  {
    icon: Brain,
    title: 'Multi-Agent Orchestration',
    desc: 'Security, NLP, Retrieval, Verification, and Explainer agents collaborate via A2A/1.0 JSON protocol with full message tracing and live audit logs.',
    tone: 'text-blue-600 bg-blue-600/10',
  },
  {
    icon: Zap,
    title: 'Vector RAG & FAISS Index',
    desc: 'Semantic similarity retrieval over curated news repositories with cosine ranking, top-5 expansion, and direct inline source citations.',
    tone: 'text-sky-600 bg-sky-600/10',
  },
  {
    icon: Bot,
    title: 'Multi-LLM Consensus',
    desc: 'Three independent LLMs independently evaluate claims, then vote on a consensus verdict — eliminating single-model hallucination bias.',
    tone: 'text-cyan-600 bg-cyan-600/10',
  },
  {
    icon: Lock,
    title: 'Enterprise-Grade Security',
    desc: 'PBKDF2-SHA256 password hashing, signed JWT tokens, token-bucket rate limiting, and AES-encrypted audit trails at every layer.',
    tone: 'text-emerald-600 bg-emerald-600/10',
  },
  {
    icon: Route,
    title: 'LangGraph Stateful Workflow',
    desc: 'Optional LangGraph execution mode provides a stateful graph-based pipeline for complex multi-step reasoning with full state persistence.',
    tone: 'text-amber-600 bg-amber-600/10',
  },
  {
    icon: BarChart3,
    title: 'Explainability & Reports',
    desc: 'Every verdict comes with a cited evidence summary, confidence scores, source attribution, and downloadable PDF verification reports.',
    tone: 'text-red-600 bg-red-600/10',
  },
];

const PIPELINE = [
  { icon: KeyRound, label: 'Security\nAgent', tone: 'text-red-500 bg-red-500/15 border-red-500' },
  { icon: Dna, label: 'NLP\nAgent', tone: 'text-sky-400 bg-sky-400/15 border-sky-400' },
  { icon: Search, label: 'Retrieval\nAgent', tone: 'text-amber-500 bg-amber-500/15 border-amber-500' },
  { icon: Scale, label: 'Verification\nAgent', tone: 'text-blue-500 bg-blue-500/15 border-blue-500' },
  { icon: Lightbulb, label: 'Explainer\nAgent', tone: 'text-emerald-500 bg-emerald-500/15 border-emerald-500' },
  { icon: CircleCheck, label: 'Verdict\n& Report', tone: 'text-teal-500 bg-teal-500/15 border-teal-500' },
];

function SectionHead({ eyebrow, title, desc }) {
  return (
    <div className="mx-auto mb-10 max-w-2xl text-center">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-primary">{eyebrow}</p>
      <h2 className="mt-2 font-heading text-3xl font-extrabold tracking-tight">{title}</h2>
      <p className="mt-2 text-sm text-muted-foreground sm:text-base">{desc}</p>
    </div>
  );
}

export default function LandingPage() {
  const { openAuth } = useOutletContext();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const reducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const startVerifying = () =>
    isAuthenticated ? navigate('/dashboard') : openAuth('register');

  return (
    <div>
      {/* Hero */}
      <section className="px-4 pb-14 pt-14 text-center sm:pt-20">
        <span className="mx-auto mb-6 gap-2 px-3 py-1.5">
          
        </span>

        <h1 className="mx-auto max-w-4xl font-heading text-4xl font-black leading-[1.1] tracking-tight sm:text-5xl lg:text-6xl">
          Truth Verified.
          <br />
          <span className="bg-gradient-to-r from-primary to-sky-500 bg-clip-text text-transparent">
            In Real Time.
          </span>
        </h1>

        <div className="mx-auto mt-6 max-w-3xl">
          <TypingAnimation
            as="p"
            className="min-h-[5.75rem] text-balance text-base leading-relaxed text-muted-foreground sm:text-lg"
            typeSpeed={reducedMotion ? 1 : 25}
            delay={reducedMotion ? 0 : 100}
          >
            {HERO_SUBTITLE}
          </TypingAnimation>
        </div>

        <div className="mt-8">
          <Button size="lg" className="px-8 text-base shadow-lg shadow-primary/25" onClick={startVerifying}>
            <Shield data-icon="inline-start" />
            Start Verifying Claims
            <ArrowRight data-icon="inline-end" />
          </Button>
        </div>
      </section>

      {/* Stats */}
      <section className="mx-auto grid max-w-5xl grid-cols-2 gap-4 px-4 lg:grid-cols-4">
        {STATS.map((stat) => (
          <div
            key={stat.label}
            className="rounded-2xl glass-card p-5 text-center transition-all duration-200 hover:-translate-y-0.5"
          >
            <div className="font-heading text-3xl font-extrabold text-primary">{stat.value}</div>
            <div className="mt-1 text-xs font-semibold text-muted-foreground sm:text-sm">
              {stat.label}
            </div>
          </div>
        ))}
      </section>

      {/* Trust bar */}
      <section className="mx-auto mt-8 max-w-5xl px-4">
        <div className="flex flex-wrap items-center justify-center gap-3">
          {TRUST.map((item) => (
            <span
              key={item.label}
              className="inline-flex items-center gap-2 rounded-full glass-pill px-4 py-1.5 text-xs font-medium text-muted-foreground shadow-xs"
            >
              <item.icon className="size-3.5 text-primary" />
              {item.label}
            </span>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto mt-20 max-w-6xl px-4">
        <SectionHead
          eyebrow="Platform Capabilities"
          title="Everything you need to verify the truth"
          desc="Six pillars of our multi-agent verification engine, built for journalists, researchers & news organizations."
        />
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="group rounded-2xl glass-card p-6 transition-all duration-200 hover:-translate-y-1"
            >
              <span
                className={`mb-3.5 flex size-11 items-center justify-center rounded-xl ${feature.tone}`}
              >
                <feature.icon className="size-5" />
              </span>
              <h3 className="font-heading font-bold">{feature.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Pipeline */}
      <section className="mx-auto mt-24 max-w-6xl px-4">
        <SectionHead
          eyebrow="How it works"
          title="The 5-Agent Verification Pipeline"
          desc="Each claim flows through our sequential agent network — from authentication to final explanation."
        />
        <div className="rounded-3xl glass-card p-6 sm:p-8">
          <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4">
            {PIPELINE.map((node, idx) => (
              <React.Fragment key={node.label}>
                <div className="flex w-24 flex-col items-center gap-2 text-center sm:w-28">
                  <span
                    className={`flex size-14 items-center justify-center rounded-2xl border-2 backdrop-blur-xs ${node.tone}`}
                  >
                    <node.icon className="size-6" />
                  </span>
                  <span className="whitespace-pre-line text-xs font-bold leading-tight sm:text-sm">
                    {node.label}
                  </span>
                </div>
                {idx < PIPELINE.length - 1 && (
                  <ArrowRight className="size-5 shrink-0 text-border" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing preview */}
      <section className="mx-auto mt-24 max-w-5xl px-4 pb-8">
        <SectionHead
          eyebrow="Pricing"
          title="Simple, Transparent Plans"
          desc="Start with our Free plan or upgrade to Pro for expanded evidence depth."
        />
        <PlanCards onChoose={(planId) => openAuth('register', planId === 'pro' ? 'pro' : undefined)} />
        <p className="mt-6 text-center text-sm text-muted-foreground">
          <Link to="/plans" className="font-medium text-primary underline underline-offset-4">
            Compare all features in the full plan matrix
          </Link>
        </p>
      </section>
    </div>
  );
}
