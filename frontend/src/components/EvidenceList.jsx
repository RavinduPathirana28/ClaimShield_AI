import React, { useState } from 'react';
import { Lightbulb, Newspaper, ExternalLink, Lock, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

const PREVIEW_COUNT = 3;

export default function EvidenceList({ result, onUpgradeClick }) {
  const [showAll, setShowAll] = useState(false);

  if (!result) return null;

  const articles = result.display_articles || result.articles || [];
  const totalFound = result.total_resources_found ?? articles.length;
  const isPro = result.is_pro_plan;
  const citationsCount = (result.citations || []).length;

  if (articles.length === 0) {
    return (
      <Alert>
        <Lightbulb className="size-4" />
        <AlertTitle>General knowledge query</AlertTitle>
        <AlertDescription>
          No local database links were required. The answer was generated using internal facts
          {citationsCount > 0 ? ` with ${citationsCount} supporting citation(s).` : '.'}
        </AlertDescription>
      </Alert>
    );
  }

  const liveWeb = articles.filter((a) => (a.source || '').includes('Live Web'));
  const dbArticles = articles.filter((a) => !(a.source || '').includes('Live Web'));
  const dates = articles.map((a) => a.date).filter(Boolean);
  const newest = dates.length ? dates.reduce((a, b) => (a > b ? a : b)) : 'unknown';
  const visible = showAll ? articles : articles.slice(0, PREVIEW_COUNT);

  const hostOf = (url) => {
    try {
      return new URL(url).hostname.replace(/^www\./, '');
    } catch {
      return null;
    }
  };

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 text-base font-semibold">
              <Newspaper className="size-4 text-muted-foreground" />
              Sources
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              Showing {articles.length} of {totalFound} retrieved resources ·{' '}
              {dbArticles.length} local · {liveWeb.length} live web · newest {newest}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={isPro ? 'default' : 'secondary'}>{isPro ? 'Pro' : 'Free'}</Badge>
            {!isPro && totalFound > 2 && onUpgradeClick && (
              <Button size="sm" variant="outline" onClick={onUpgradeClick}>
                <Lock data-icon="inline-start" />
                View 3–5 resources
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-2">
        {visible.map((article, idx) => {
          const score =
            typeof article.score === 'number'
              ? (article.score * 100).toFixed(4).replace(/\.?0+$/, '')
              : null;
          const host = article.url && article.url !== '#' ? hostOf(article.url) : null;
          return (
            <div
              key={idx}
              className="flex flex-col gap-1.5 rounded-xl glass-panel p-3.5 transition-all duration-150 hover:border-[var(--glass-primary-border)]"
            >
              <div className="flex items-start justify-between gap-3">
                <h4 className="line-clamp-2 text-sm font-semibold leading-snug">
                  {idx + 1}. {article.title || `Evidence Source #${idx + 1}`}
                </h4>
                <div className="flex shrink-0 items-center gap-2">
                  {score !== null && (
                    <Badge variant="secondary" className="font-mono">
                      {score}
                    </Badge>
                  )}
                  {host && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 whitespace-nowrap text-xs font-medium text-primary hover:underline"
                    >
                      {host}
                      <ExternalLink className="size-3" />
                    </a>
                  )}
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                {article.source}
                {article.date && ` · ${article.date}`}
              </p>
              <p className="line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                {article.content}
              </p>
            </div>
          );
        })}

        {articles.length > PREVIEW_COUNT && (
          <Button
            variant="ghost"
            size="sm"
            className="mx-auto text-muted-foreground"
            onClick={() => setShowAll((v) => !v)}
          >
            {showAll ? (
              <>
                Show fewer sources <ChevronUp data-icon="inline-end" />
              </>
            ) : (
              <>
                Show all {articles.length} sources <ChevronDown data-icon="inline-end" />
              </>
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
