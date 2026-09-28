import React from 'react';
import { MessagesSquare, Search, Scale, Target } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { verdictInfo } from '@/lib/verdicts';

const AGENT_STAGES = {
  FactCheckerAgent: {
    label: 'Fact Checker',
    icon: Search,
    chip: 'border-sky-600/40 bg-sky-600/10 text-sky-600',
  },
  CriticAgent: {
    label: 'Critic',
    icon: Scale,
    chip: 'border-amber-600/40 bg-amber-600/10 text-amber-600',
  },
  ConsensusAgent: {
    label: 'Consensus',
    icon: Target,
    chip: 'border-emerald-600/40 bg-emerald-600/10 text-emerald-600',
  },
};

const DEFAULT_STAGE = {
  label: 'Agent',
  icon: MessagesSquare,
  chip: 'border-border bg-muted text-muted-foreground',
};

export default function DebateCard({ debate }) {
  if (!debate) return null;

  const turns = debate.debate_log || [];
  const consensus = debate.consensus || debate.message || '';

  return (
    <div className="flex flex-col gap-3">
      {turns.map((turn, idx) => {
        const stage = AGENT_STAGES[turn.agent] || { ...DEFAULT_STAGE, label: turn.agent || 'Agent' };
        const StageIcon = stage.icon;
        const vInfo = turn.verdict ? verdictInfo(turn.verdict) : null;

        return (
          <div key={idx} className="flex flex-col gap-2 rounded-lg border bg-muted/30 p-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className={cn('gap-1', stage.chip)}>
                <StageIcon className="size-3" />
                {stage.label}
              </Badge>
              {turn.model && <Badge variant="secondary">{turn.model}</Badge>}
              {vInfo && (
                <Badge variant="outline" className={cn('gap-1', vInfo.badge)}>
                  <vInfo.icon className="size-3" />
                  {turn.verdict}
                </Badge>
              )}
              {turn.confidence != null && (
                <span className="text-xs font-semibold text-muted-foreground">
                  {Math.round(turn.confidence)}% confidence
                </span>
              )}
            </div>
            <p className="text-sm leading-relaxed text-foreground/90">{turn.message}</p>
          </div>
        );
      })}

      {consensus && (
        <div className="rounded-lg border border-emerald-600/40 bg-emerald-600/10 p-3">
          <p className="mb-1 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-600">
            <Target className="size-3.5" />
            Final Consensus
          </p>
          <p className="text-sm leading-relaxed text-foreground/90">{consensus}</p>
        </div>
      )}
    </div>
  );
}
