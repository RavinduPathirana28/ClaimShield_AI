import React, { useState } from 'react';
import { toast } from 'sonner';
import { FileDown, Loader2, CircleCheck, TriangleAlert } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import { verdictInfo } from '@/lib/verdicts';
import * as api from '@/services/api';
import AudioVerdictPlayer from '@/components/AudioVerdictPlayer';

export default function VerdictCard({ result, elapsed, agreementScore = null, modelCount = 0 }) {
  const [exporting, setExporting] = useState(false);
  if (!result) return null;

  const info = verdictInfo(result.verdict);
  const Icon = info.icon;
  const conf = Math.round((result.confidence || 0) * 100);
  const agreePct = agreementScore != null ? Math.round(agreementScore * 100) : null;
  const converged = agreePct != null && agreementScore >= 0.7;
  const straight =
    result.straight_answer ||
    (result.summary ? `${result.summary.split('. ')[0]}.` : info.label);

  const downloadPdf = async () => {
    setExporting(true);
    try {
      const blob = await api.exportPdf(result);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `claimshield_report_${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Verification report downloaded');
    } catch (err) {
      toast.error(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <Badge variant="outline" className={cn('gap-2 px-3.5 py-1.5 text-base font-bold', info.badge)}>
            <Icon className="size-5" />
            {info.label}
          </Badge>
          <div className="flex flex-col items-end gap-1.5">
            <span className="text-xs font-medium text-muted-foreground">
              Confidence{' '}
              <span className={cn('ml-1 text-2xl font-extrabold tracking-tight', info.accent)}>
                {conf}%
              </span>
            </span>
            <Progress value={conf} className={cn('h-1.5 w-40')} />
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <p className="text-xl font-bold leading-snug">{straight}</p>
          <p className="text-sm leading-relaxed text-muted-foreground">{result.summary}</p>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-3">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
            <p className="text-xs text-muted-foreground">
              <strong className="font-semibold text-foreground">{result.engine || 'Unknown'}</strong>
              {elapsed != null && <> · {elapsed.toFixed(2)}s</>}
            </p>
            {agreePct != null && modelCount > 0 && (
              <span
                className={cn(
                  'inline-flex items-center gap-1.5 text-xs font-medium',
                  converged ? 'text-emerald-600' : 'text-amber-600'
                )}
              >
                {converged ? (
                  <CircleCheck className="size-3.5" />
                ) : (
                  <TriangleAlert className="size-3.5" />
                )}
                {modelCount} model{modelCount === 1 ? '' : 's'} · {agreePct}% agreement
              </span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <AudioVerdictPlayer
              verdict={info.label}
              straight={straight}
              summary={result.summary}
            />
            <Button variant="outline" size="sm" onClick={downloadPdf} disabled={exporting}>
              {exporting ? (
                <Loader2 data-icon="inline-start" className="animate-spin" />
              ) : (
                <FileDown data-icon="inline-start" />
              )}
              {exporting ? 'Generating PDF…' : 'Download report (PDF)'}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
