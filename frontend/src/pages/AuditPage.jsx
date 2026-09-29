import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router';
import { ShieldCheck, Clock, Tag, Newspaper, RefreshCw, Loader2, ArrowRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from '@/components/ui/empty';
import { Skeleton } from '@/components/ui/skeleton';
import { verdictInfo } from '@/lib/verdicts';
import { useAuth } from '@/context/AuthContext';
import * as api from '@/services/api';

export default function AuditPage() {
  const { token } = useAuth();
  const [logs, setLogs] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setLogs(await api.getAuditLogs(token));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="flex flex-col gap-6">
      <Card className="shadow-sm">
        <CardContent className="flex flex-col gap-3 pt-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="flex items-center gap-2 text-xl font-bold text-emerald-800 dark:text-emerald-400">
                <ShieldCheck className="size-5" />
                Cryptographic Verification Ledger
              </h2>
              <p className="mt-1 max-w-2xl text-sm text-emerald-700 dark:text-emerald-500">
                Immutable audit trail. Every verified query, model reasoning trace, and citation is
                encrypted at rest using <strong>Fernet AES-128-CBC</strong>.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge
                variant="outline"
                className="border-emerald-600/40 bg-emerald-600/10 text-emerald-700 dark:text-emerald-400"
              >
                Fernet AES-128-CBC
              </Badge>
              <Badge
                variant="outline"
                className="border-primary/40 bg-primary/10 text-primary"
              >
                PBKDF2 Salted
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {loading && (
        <div className="flex flex-col gap-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="flex flex-col gap-2 rounded-lg border p-4">
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-3 w-2/3" />
            </div>
          ))}
        </div>
      )}

      {error && !loading && (
        <Alert variant="destructive">
          <AlertTitle>Failed to load audit logs</AlertTitle>
          <AlertDescription className="flex items-center justify-between gap-3">
            <span>{error}</span>
            <Button size="sm" variant="outline" onClick={load}>
              <RefreshCw data-icon="inline-start" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {!loading && !error && logs && logs.length === 0 && (
        <Empty className="min-h-[240px] border">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <ShieldCheck />
            </EmptyMedia>
            <EmptyTitle>No audit entries yet</EmptyTitle>
            <EmptyDescription>
              You haven&apos;t run any fact checks yet. Check a claim on the Verification Dashboard
              to populate this ledger.
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button asChild size="sm" variant="outline">
              <Link to="/dashboard">
                Open Verification Dashboard
                <ArrowRight data-icon="inline-end" />
              </Link>
            </Button>
          </EmptyContent>
        </Empty>
      )}

      {!loading && !error && logs && logs.length > 0 && (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-muted-foreground">
            {logs.length} encrypted audit entr{logs.length === 1 ? 'y' : 'ies'} on file.
          </p>
          {logs.map((log, idx) => {
            const info = verdictInfo(log.verdict);
            const details = log.details || {};
            const entities = (details.entities || []).filter((e) => e && typeof e === 'object');
            const articles = (details.articles_retrieved || []).filter(
              (a) => a && typeof a === 'object'
            );
            const confidence = Math.round((log.confidence || 0) * 100);

            return (
              <Collapsible key={log.id ?? idx}>
                <CollapsibleTrigger className="flex w-full items-center gap-3 rounded-2xl glass-card glass-card-interactive px-4 py-3.5 text-left transition-all duration-150">
                  <Clock className="size-4 shrink-0 text-muted-foreground" />
                  <span className="min-w-0 flex-1 truncate text-sm">
                    <span className="font-mono text-xs text-muted-foreground">
                      {log.timestamp}
                    </span>{' '}
                    — Claim: <span className="font-medium">“{log.claim}”</span>
                  </span>
                  <Badge variant="outline" className={`hidden shrink-0 sm:inline-flex ${info.badge}`}>
                    <info.icon className="size-3" />
                    {log.verdict}
                  </Badge>
                  <span className="shrink-0 text-xs font-bold tabular-nums">{confidence}%</span>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <div className="mt-2 flex flex-col gap-4 rounded-2xl glass-panel p-4.5">
                    <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-3">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={info.badge}>
                          <info.icon className="size-3" />
                          {log.verdict}
                        </Badge>
                        <span className="font-mono text-xs text-muted-foreground">
                          UTC: {log.timestamp}
                        </span>
                      </div>
                      <span className="text-xs">
                        <span className="font-semibold text-muted-foreground">Certainty:</span>{' '}
                        <strong>{confidence}%</strong>
                      </span>
                    </div>

                    <div className="rounded-xl glass-panel p-3.5">
                      <p className="mb-1 text-xs font-bold uppercase tracking-wider text-primary">
                        Audited Model Rationale
                      </p>
                      <p className="text-sm leading-relaxed">
                        {details.summary || 'No reasoning logged.'}
                      </p>
                    </div>

                    {entities.length > 0 && (
                      <div>
                        <p className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
                          <Tag className="size-3.5" /> Extracted Named Entities
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {entities.map((ent, i) => (
                            <Badge key={i} variant="secondary" className="font-mono text-xs">
                              {ent.text} <span className="opacity-70">({ent.label || 'MISC'})</span>
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {articles.length > 0 && (
                      <div>
                        <p className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
                          <Newspaper className="size-3.5" /> Referenced Source Articles (FAISS
                          Cosine Similarity)
                        </p>
                        <ul className="flex flex-col gap-1 text-sm text-muted-foreground">
                          {articles.map((a, i) => (
                            <li key={i} className="flex flex-wrap items-baseline gap-1.5">
                              <strong className="text-foreground">{a.source || 'Unknown'}</strong>
                              <span>: {a.title}</span>
                              <span className="font-mono text-xs">
                                (Score: {Number(a.score || 0).toFixed(4)})
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            );
          })}
        </div>
      )}
    </div>
  );
}
