import React, { useState } from 'react';
import { Link } from 'react-router';
import {
  Search,
  Shield,
  ShieldAlert,
  Loader2,
  Bot,
  Smartphone,
  MoonStar,
  Coffee,
  Cpu,
  ArrowRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from '@/components/ui/empty';

import PipelineLoader from '@/components/PipelineLoader';
import VerdictCard from '@/components/VerdictCard';
import ConsensusCard from '@/components/ConsensusCard';
import DebateCard from '@/components/DebateCard';
import EvidenceList from '@/components/EvidenceList';
import Recommendations from '@/components/Recommendations';
import PaymentDialog from '@/components/PaymentDialog';
import VoiceClaimInput from '@/components/VoiceClaimInput';

import { useAuth } from '@/context/AuthContext';
import { useRuns } from '@/context/RunContext';
import * as api from '@/services/api';

const SAMPLES = [
  { label: 'What is AI?', query: 'What is Artificial Intelligence?', icon: Bot },
  { label: 'iPhone 18 in 2026?', query: 'Apple will launch the iPhone 18 in July 2026.', icon: Smartphone },
  { label: 'Why is sky blue?', query: 'Why is the sky blue?', icon: MoonStar },
  { label: 'Is coffee healthy?', query: 'Is drinking coffee good for heart health?', icon: Coffee },
];

const ENGINE_MODES = [
  'Standard A2A Protocol',
  'LangGraph Stateful Workflow',
  'AutoGen Agent Debate',
];

function DetailHeading({ children }) {
  return <h4 className="text-sm font-semibold tracking-tight">{children}</h4>;
}

export default function DashboardPage() {
  const { token, refreshProfile, isPro } = useAuth();
  const { recordRun, agentLogs } = useRuns();

  const [claim, setClaim] = useState('');
  const [engineMode, setEngineMode] = useState(ENGINE_MODES[0]);
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState([]);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [elapsed, setElapsed] = useState(null);
  const [checkoutOpen, setCheckoutOpen] = useState(false);

  const run = async (override = null) => {
    const query = (override ?? claim).trim();
    if (!query) {
      setError({ message: 'Please type a question or statement first.', status: 0 });
      return;
    }
    if (override !== null) setClaim(override);

    setError(null);
    setResult(null);
    setSteps([]);
    setElapsed(null);
    setLoading(true);
    const started = Date.now();

    try {
      const { result: finalResult, agent_logs } = await api.streamVerify(
        token,
        query,
        engineMode,
        (event) => setSteps((prev) => [...prev, event])
      );
      setResult(finalResult);
      setElapsed((Date.now() - started) / 1000);
      recordRun(agent_logs);
      await refreshProfile();
    } catch (err) {
      setError({ message: err.message, status: err.status });
    } finally {
      setLoading(false);
    }
  };

  const entities = (result?.entities || []).filter((e) => e && typeof e === 'object');
  const citations = (result?.citations || []).filter((c) => c && typeof c === 'object');
  const ml = result?.ml_classification;
  const evidenceSummary = result?.evidence_summary;
  const debate = result?.autogen_debate;
  const hasDebate = !!debate && (!!debate.consensus || !!debate.message || (debate.debate_log || []).length > 0);

  const overviewSections = [
    evidenceSummary && (
      <section key="highlights" className="flex flex-col gap-2">
        <DetailHeading>Evidence highlights</DetailHeading>
        <p className="leading-relaxed text-foreground/90">{evidenceSummary}</p>
      </section>
    ),
    citations.length > 0 && (
      <section key="quotes" className="flex flex-col gap-2.5">
        <DetailHeading>Key quotes &amp; citations · {citations.length}</DetailHeading>
        <div className="flex flex-col gap-2.5">
          {citations.map((cit, idx) => (
            <div key={idx} className="rounded-lg border bg-muted/40 p-3">
              <p className="text-xs font-semibold text-muted-foreground">
                {cit.article_id ? `Article #${cit.article_id}` : 'General evidence'}
              </p>
              <p className="my-1 text-sm italic">“{cit.quote || 'No quote provided.'}”</p>
              {cit.explanation && (
                <p className="text-xs text-muted-foreground">
                  <strong>Insight:</strong> {cit.explanation}
                </p>
              )}
            </div>
          ))}
        </div>
      </section>
    ),
    entities.length > 0 && (
      <section key="entities" className="flex flex-col gap-2">
        <DetailHeading>Extracted concepts · {entities.length}</DetailHeading>
        <div className="flex flex-wrap gap-1.5">
          {entities.map((ent, idx) => (
            <Badge key={idx} variant="secondary">
              <strong>{ent.text || 'Unknown'}</strong>&nbsp;({ent.label || 'MISC'})
            </Badge>
          ))}
        </div>
      </section>
    ),
  ].filter(Boolean);

  const modelSections = [
    <ConsensusCard
      key="consensus"
      agreementScore={result?.agreement_score}
      modelResults={result?.model_results || []}
    />,
    ml && (
      <section key="ml" className="flex flex-col gap-2">
        <DetailHeading>ML credibility check</DetailHeading>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-sm">
          <span>
            Prediction: <strong>{ml.label || 'N/A'}</strong>
          </span>
          <span>
            Confidence: <strong>{Math.round((ml.confidence || 0) * 100)}%</strong>
          </span>
          <span className="text-xs text-muted-foreground">
            Engine: {ml.engine || 'TF-IDF Vectorizer'}
          </span>
        </div>
      </section>
    ),
    hasDebate && (
      <section key="debate" className="flex flex-col gap-2">
        <DetailHeading>Multi-agent debate</DetailHeading>
        <DebateCard debate={debate} />
      </section>
    ),
  ].filter(Boolean);

  const technicalSections =
    agentLogs.length > 0
      ? [
          <section key="a2a" className="flex flex-col gap-2">
            <DetailHeading>A2A/1.0 agent messages · {agentLogs.length}</DetailHeading>
            <div className="flex flex-col gap-2">
              {agentLogs.slice(0, 4).map((log, idx) => (
                <div
                  key={idx}
                  className="flex flex-wrap items-center gap-2 rounded-xl glass-panel px-3.5 py-2 text-xs"
                >
                  <strong className="text-primary">{log.from}</strong>
                  <span className="text-muted-foreground">→</span>
                  <strong className="text-emerald-600">{log.to}</strong>
                  <span className="text-muted-foreground">({log.action})</span>
                  <span className="ml-auto font-mono text-muted-foreground">{log.timestamp}</span>
                </div>
              ))}
              <div className="flex flex-wrap items-center justify-between gap-2">
                {agentLogs.length > 4 && (
                  <p className="text-xs text-muted-foreground">
                    + {agentLogs.length - 4} more envelopes
                  </p>
                )}
                <Button asChild variant="outline" size="sm" className="ml-auto no-underline">
                  <Link to="/a2a">
                    Open A2A Protocol Monitor
                    <ArrowRight data-icon="inline-end" />
                  </Link>
                </Button>
              </div>
            </div>
          </section>,
        ]
      : [];

  const detailTabs = [
    overviewSections.length > 0 && {
      value: 'overview',
      label: 'Overview',
      node: overviewSections,
    },
    modelSections.length > 0 && {
      value: 'models',
      label: 'Model analysis',
      node: modelSections,
    },
    technicalSections.length > 0 && {
      value: 'technical',
      label: 'A2A messages',
      node: technicalSections,
    },
  ].filter(Boolean);

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h2 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
          <Search className="size-6 text-primary" />
          Ask a Question or Verify a Claim
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Type any general question or factual statement below. Our multi-agent AI system will
          evaluate it and provide a realistic, easy-to-understand explanation.
        </p>
      </header>

      <section>
        <p className="mb-2 text-xs font-bold uppercase tracking-wider text-muted-foreground">
          Sample Questions &amp; Claims:
        </p>
        <div className="flex flex-wrap gap-2">
          {SAMPLES.map((sample) => (
            <Button
              key={sample.label}
              variant="outline"
              size="sm"
              className="rounded-full glass-button hover:bg-[var(--glass-button-hover-bg)]"
              onClick={() => setClaim(sample.query)}
            >
              <sample.icon data-icon="inline-start" />
              {sample.label}
            </Button>
          ))}
        </div>
      </section>

      <section className="rounded-2xl glass-card p-5">
        <div className="mb-2.5 flex flex-wrap items-center justify-between gap-2">
          <label htmlFor="claim-input" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Claim or Query Input
          </label>
          <VoiceClaimInput
            onTranscript={(transcribed) => {
              setClaim((prev) => (prev.trim() ? `${prev.trim()} ${transcribed}` : transcribed));
            }}
            disabled={loading}
            token={token}
          />
        </div>
        <Textarea
          id="claim-input"
          name="claim"
          rows={3}
          value={claim}
          onChange={(e) => setClaim(e.target.value)}
          placeholder="e.g. 'What is quantum computing?', 'Why is the sky blue?', or 'Apple will launch iPhone 18 in July 2026'"
          className="resize-y text-sm"
        />
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <Select value={engineMode} onValueChange={setEngineMode}>
            <SelectTrigger className="w-[260px]" aria-label="Engine protocol">
              <Cpu data-icon="inline-start" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ENGINE_MODES.map((mode) => (
                <SelectItem key={mode} value={mode}>
                  {mode}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-muted-foreground md:inline">
              Supports general knowledge questions as well as factual news verification.
            </span>
            <Button onClick={() => run()} disabled={loading} className="shadow-sm shadow-primary/25">
              {loading ? (
                <Loader2 data-icon="inline-start" className="animate-spin" />
              ) : (
                <Shield data-icon="inline-start" />
              )}
              {loading ? 'Verifying…' : 'Run ClaimShield AI'}
            </Button>
          </div>
        </div>
      </section>

      {error && (
        <Alert variant="destructive">
          <ShieldAlert className="size-4" />
          <AlertTitle>
            {error.status === 429
              ? 'Rate limit exceeded'
              : 'Fact checking pipeline failed'}
          </AlertTitle>
          <AlertDescription>
            {error.message}
            {error.status === 429 &&
              ' Please wait a moment, or upgrade to the Pro Plan on the Account page to bypass token limits.'}
          </AlertDescription>
        </Alert>
      )}

      {loading && <PipelineLoader events={steps} />}

      {!loading && !result && !error && (
        <Empty className="min-h-[260px] rounded-2xl glass-card">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <Search />
            </EmptyMedia>
            <EmptyTitle>No verification yet</EmptyTitle>
            <EmptyDescription>
              Type a claim or question above and run the multi-agent pipeline to see the full
              analysis report — verdict, model consensus, evidence and citations.
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button variant="outline" size="sm" onClick={() => run(SAMPLES[0].query)}>
              Try “{SAMPLES[0].label}”
              <ArrowRight data-icon="inline-end" />
            </Button>
          </EmptyContent>
        </Empty>
      )}

      {!loading && result && (
        <div className="flex flex-col gap-5">
          <VerdictCard
            result={result}
            elapsed={elapsed}
            agreementScore={result.agreement_score}
            modelCount={(result.model_results || []).length}
          />

          <EvidenceList
            result={result}
            onUpgradeClick={isPro ? undefined : () => setCheckoutOpen(true)}
          />

          {detailTabs.length > 0 && (
            <Card className="shadow-sm">
              <Tabs defaultValue={detailTabs[0].value} className="w-full">
                <div className="px-6 pt-5">
                  <TabsList>
                    {detailTabs.map((tab) => (
                      <TabsTrigger key={tab.value} value={tab.value}>
                        {tab.label}
                      </TabsTrigger>
                    ))}
                  </TabsList>
                </div>
                <CardContent className="flex flex-col gap-5 pt-5">
                  {detailTabs.map((tab) => (
                    <TabsContent
                      key={tab.value}
                      value={tab.value}
                      className="flex flex-col gap-5"
                    >
                      {tab.node}
                    </TabsContent>
                  ))}
                </CardContent>
              </Tabs>
            </Card>
          )}

          <Recommendations
            recommendations={result.recommendations}
            onSelectClaim={(c) => run(c)}
          />
        </div>
      )}

      <PaymentDialog open={checkoutOpen} onOpenChange={setCheckoutOpen} planId="pro" />
    </div>
  );
}
