import React from 'react';
import { Link } from 'react-router';
import { Radio, ArrowRight, Inbox, Send, ClipboardList } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from '@/components/ui/empty';
import { useRuns } from '@/context/RunContext';

const SPEC_ROWS = [
  ['Protocol', 'A2A/1.0 — Agent-to-Agent messaging over in-process Python function calls'],
  ['Serialization', 'JSON — validated via dumps/loads round-trip for strict compliance'],
  ['Message ID', 'UUID4 — unique identifier for every message for end-to-end traceability'],
  ['Timestamp', 'Unix epoch float — precise timing for performance profiling'],
  ['Transport', 'In-process function invocation — zero-latency delivery via BaseAgent.send_message()'],
];

function JsonPane({ title, icon: Icon, data, tone }) {
  let text;
  try {
    text = JSON.stringify(data ?? {}, null, 2);
  } catch {
    text = String(data);
  }
  return (
    <div className="min-w-0">
      <p className={`mb-1.5 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider ${tone}`}>
        <Icon className="size-3.5" />
        {title}
      </p>
      <pre className="max-h-72 overflow-auto rounded-xl border border-border/50 bg-background/60 p-3.5 font-mono text-xs leading-relaxed shadow-inner backdrop-blur-xs dark:border-white/10 dark:bg-card/50">
        {text}
      </pre>
    </div>
  );
}

export default function A2AMonitorPage() {
  const { agentLogs, lastRunAt } = useRuns();

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h2 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
          <Radio className="size-6 text-primary" />
          Multi-Agent A2A/1.0 Protocol Message Tracing
        </h2>
        <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
          Inspect the JSON communications occurring between subagents using the{' '}
          <strong>A2A/1.0 (Agent-to-Agent)</strong> protocol. Each message includes a protocol
          version, unique message ID, Unix timestamp, sender/recipient identifiers, action verb,
          and structured data payload.
        </p>
      </header>

      <Card className="shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-primary">
            <ClipboardList className="size-4" />
            A2A/1.0 Protocol Specification
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-xl border border-border/50 bg-background/30 backdrop-blur-xs">
            <Table>
              <TableBody>
                {SPEC_ROWS.map(([key, value]) => (
                  <TableRow key={key}>
                    <TableCell className="w-1/4 align-top font-semibold text-primary">
                      {key}
                    </TableCell>
                    <TableCell className="align-top text-muted-foreground">{value}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {agentLogs.length === 0 ? (
        <Empty className="min-h-[220px] rounded-2xl border border-border/50 bg-card/45 backdrop-blur-xl dark:border-white/10 dark:bg-card/40">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <Inbox />
            </EmptyMedia>
            <EmptyTitle>Trace buffer is empty</EmptyTitle>
            <EmptyDescription>
              No query logs in buffer. Run a claim check from the Verification Dashboard to monitor
              agent communication flows.
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button asChild size="sm" variant="outline">
              <Link to="/dashboard">
                Run a claim check
                <ArrowRight data-icon="inline-end" />
              </Link>
            </Button>
          </EmptyContent>
        </Empty>
      ) : (
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-muted-foreground">
              {agentLogs.length} envelope{agentLogs.length === 1 ? '' : 's'} from the most recent
              verification run
              {lastRunAt ? ` · captured ${new Date(lastRunAt).toLocaleTimeString()}` : ''}.
            </p>
            <Badge variant="secondary" className="font-mono">
              A2A/1.0
            </Badge>
          </div>

          {agentLogs.map((log, idx) => (
            <Collapsible key={idx}>
              <CollapsibleTrigger className="flex w-full items-center gap-3 rounded-2xl border border-border/60 bg-card/75 px-4 py-3.5 text-left shadow-xs backdrop-blur-xl transition-all duration-150 hover:-translate-y-0.5 hover:border-primary/40 hover:bg-card/90 dark:border-white/10 dark:bg-card/65">
                <Radio className="size-4 shrink-0 text-primary" />
                <span className="min-w-0 flex-1 truncate text-sm">
                  Trace #{idx + 1}{' '}
                  <span className="font-mono text-xs text-muted-foreground">
                    [{log.timestamp}]
                  </span>
                  : <strong className="text-primary">{log.from}</strong>
                  <span className="text-muted-foreground"> → </span>
                  <strong className="text-emerald-600">{log.to}</strong>
                </span>
                <Badge variant="outline" className="hidden shrink-0 font-mono sm:inline-flex">
                  {log.action}
                </Badge>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="mt-2 grid gap-4 rounded-2xl border border-border/50 bg-muted/30 p-4.5 backdrop-blur-md lg:grid-cols-2">
                  <JsonPane
                    title="Outgoing A2A/1.0 Message"
                    icon={Send}
                    tone="text-primary"
                    data={{
                      protocol: 'A2A/1.0',
                      sender: log.from,
                      recipient: log.to,
                      action: log.action,
                      data: log.data_sent,
                    }}
                  />
                  <JsonPane
                    title="Received Response Payload"
                    icon={Inbox}
                    tone="text-emerald-600"
                    data={log.response_received}
                  />
                </div>
              </CollapsibleContent>
            </Collapsible>
          ))}
        </div>
      )}
    </div>
  );
}
