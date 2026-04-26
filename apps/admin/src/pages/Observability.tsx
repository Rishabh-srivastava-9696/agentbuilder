import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowPathIcon,
  BoltIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  FunnelIcon,
  ServerStackIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import { observabilityApi, ObservabilityAgent } from '../api/client';

const countFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
const decimalFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });
const percentFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0, style: 'percent' });

const RANGE_OPTIONS = [
  { label: 'Last 1h', value: 1 },
  { label: 'Last 24h', value: 24 },
  { label: 'Last 7d', value: 168 },
  { label: 'Last 30d', value: 720 },
];

function formatCount(value: number): string {
  return countFormatter.format(value || 0);
}

function formatMs(value: number): string {
  if (!value) {
    return 'No data';
  }
  return `${decimalFormatter.format(value)} ms`;
}

function formatPercent(value: number): string {
  return percentFormatter.format(value || 0);
}

function statusPillTone(value: string): string {
  const normalized = value.toLowerCase();
  if (normalized.includes('success') || normalized.includes('healthy') || normalized.includes('grounded')) {
    return 'bg-emerald-50 text-emerald-700 ring-emerald-600/20';
  }
  if (normalized.includes('error') || normalized.includes('fallback') || normalized.includes('blocked')) {
    return 'bg-rose-50 text-rose-700 ring-rose-600/20';
  }
  return 'bg-slate-100 text-slate-700 ring-slate-600/20';
}

function responsibleStatus(totals: {
  messages: number;
  grounded_rate: number;
  guardrails: number;
  fallbacks: number;
  strapi_errors: number;
}) {
  if (totals.strapi_errors > 0) {
    return { label: 'Needs attention', tone: 'text-rose-700', bg: 'bg-rose-50', border: 'border-rose-200' };
  }
  if (totals.messages > 0 && totals.grounded_rate < 0.5) {
    return { label: 'Grounding watch', tone: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200' };
  }
  return { label: 'Healthy', tone: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200' };
}

function HeroMetric({
  label,
  value,
  help,
  icon: Icon,
}: {
  label: string;
  value: string;
  help: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-3 font-mono text-3xl font-semibold tracking-tight text-slate-950">{value}</p>
          <p className="mt-2 text-sm leading-5 text-slate-500">{help}</p>
        </div>
        <div className="rounded-lg bg-slate-950 p-2 text-white">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}

function StoryCard({
  title,
  value,
  description,
  tone,
}: {
  title: string;
  value: string;
  description: string;
  tone: 'emerald' | 'blue' | 'amber' | 'rose' | 'slate';
}) {
  const toneClasses = {
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-900',
    blue: 'border-sky-200 bg-sky-50 text-sky-900',
    amber: 'border-amber-200 bg-amber-50 text-amber-900',
    rose: 'border-rose-200 bg-rose-50 text-rose-900',
    slate: 'border-slate-200 bg-slate-50 text-slate-900',
  };

  return (
    <div className={`rounded-lg border p-4 ${toneClasses[tone]}`}>
      <p className="text-sm font-semibold">{title}</p>
      <p className="mt-3 font-mono text-2xl font-semibold">{value}</p>
      <p className="mt-2 text-sm leading-5 opacity-80">{description}</p>
    </div>
  );
}

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-950">{title}</h2>
        <p className="mt-1 text-sm leading-5 text-slate-500">{description}</p>
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center">
      <p className="text-sm font-medium text-slate-700">{label}</p>
      <p className="mt-1 text-xs text-slate-500">New agent traffic will populate this view.</p>
    </div>
  );
}

function AgentRows({ agents }: { agents: ObservabilityAgent[] }) {
  if (agents.length === 0) {
    return <EmptyState label="No agents match this filter" />;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead>
          <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <th className="py-2 pr-4">Agent</th>
            <th className="py-2 pr-4">Grounded</th>
            <th className="py-2 pr-4">Safety</th>
            <th className="py-2 pr-4">Fallbacks</th>
            <th className="py-2 pr-4">Latency</th>
            <th className="py-2">Sync Issues</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {agents.map((agent) => (
            <tr key={agent.agent_id}>
              <td className="py-3 pr-4">
                <p className="font-semibold text-slate-950">{agent.agent_name}</p>
                <p className="text-xs text-slate-500">{agent.brand_name}</p>
              </td>
              <td className="py-3 pr-4 font-mono text-slate-800">
                {agent.messages ? formatPercent(agent.grounded_rate) : 'No data'}
              </td>
              <td className="py-3 pr-4 font-mono text-slate-800">
                {formatCount(agent.guardrails)} caught
              </td>
              <td className="py-3 pr-4 font-mono text-slate-800">
                {formatCount(agent.fallbacks)}
              </td>
              <td className="py-3 pr-4 font-mono text-slate-800">
                {formatMs(agent.avg_latency_ms)}
              </td>
              <td className="py-3">
                <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ring-1 ring-inset ${agent.strapi_errors ? 'bg-rose-50 text-rose-700 ring-rose-600/20' : 'bg-emerald-50 text-emerald-700 ring-emerald-600/20'}`}>
                  {agent.strapi_errors ? `${formatCount(agent.strapi_errors)} issues` : 'Healthy'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Observability() {
  const [brandSlug, setBrandSlug] = React.useState('');
  const [agentId, setAgentId] = React.useState('');
  const [rangeHours, setRangeHours] = React.useState(24);

  const summaryQuery = useQuery({
    queryKey: ['observability', 'summary', brandSlug, agentId, rangeHours],
    queryFn: () => observabilityApi.getSummary({
      brand_slug: brandSlug || undefined,
      agent_id: agentId || undefined,
      range_hours: rangeHours,
    }).then((response) => response.data),
    refetchInterval: 10000,
  });

  const summary = summaryQuery.data;
  const totals = summary?.totals || {
    messages: 0,
    grounded: 0,
    grounded_rate: 0,
    low_confidence_prevented: 0,
    guardrails: 0,
    fallbacks: 0,
    rate_limit_blocks: 0,
    strapi_errors: 0,
    avg_latency_ms: 0,
    avg_confidence: 0,
  };
  const health = responsibleStatus(totals);
  const agents = summary?.agents || [];
  const availableAgents = brandSlug
    ? agents.filter((agent) => agent.brand_slug === brandSlug)
    : agents;
  const hallucination = summary?.sections.hallucination;

  React.useEffect(() => {
    if (agentId && !availableAgents.some((agent) => agent.agent_id === agentId)) {
      setAgentId('');
    }
  }, [agentId, availableAgents]);

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${health.bg} ${health.border} ${health.tone}`}>
            <ShieldCheckIcon className="h-4 w-4" aria-hidden="true" />
            Responsible AI: {health.label}
          </div>
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-slate-950">Observability</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Per-agent visibility into safety, grounding, hallucination prevention, fallbacks, sync health, and response speed.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void summaryQuery.refetch()}
          className="inline-flex items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50 active:translate-y-px"
        >
          <ArrowPathIcon className={`h-4 w-4 ${summaryQuery.isFetching ? 'animate-spin' : ''}`} aria-hidden="true" />
          Refresh
        </button>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900">
          <FunnelIcon className="h-4 w-4 text-slate-500" aria-hidden="true" />
          Filters
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Brand</span>
            <select
              value={brandSlug}
              onChange={(event) => {
                setBrandSlug(event.target.value);
                setAgentId('');
              }}
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm"
            >
              <option value="">All brands</option>
              {(summary?.brands || []).map((brand) => (
                <option key={brand.slug} value={brand.slug}>{brand.name}</option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Agent</span>
            <select
              value={agentId}
              onChange={(event) => setAgentId(event.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm"
            >
              <option value="">All agents</option>
              {availableAgents.map((agent) => (
                <option key={agent.agent_id} value={agent.agent_id}>{agent.agent_name}</option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Time range</span>
            <select
              value={rangeHours}
              onChange={(event) => setRangeHours(Number(event.target.value))}
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm"
            >
              {RANGE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {summaryQuery.isLoading && (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-36 animate-pulse rounded-lg border border-slate-200 bg-slate-100" />
          ))}
        </div>
      )}

      {summaryQuery.isError && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-5">
          <div className="flex gap-3">
            <ExclamationTriangleIcon className="h-5 w-5 flex-none text-rose-600" aria-hidden="true" />
            <div>
              <p className="text-sm font-semibold text-rose-900">Could not load observability data</p>
              <p className="mt-1 text-sm text-rose-700">Confirm the AgentBuilder API is running and your dashboard session is still valid.</p>
            </div>
          </div>
        </div>
      )}

      {!summaryQuery.isLoading && !summaryQuery.isError && (
        <>
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-5">
            <HeroMetric
              label="Grounded Answers"
              value={totals.messages ? formatPercent(totals.grounded_rate) : 'No data'}
              help={`${formatCount(totals.grounded)} of ${formatCount(totals.messages)} responses used KB evidence`}
              icon={CheckCircleIcon}
            />
            <HeroMetric
              label="Safety Catches"
              value={formatCount(totals.guardrails)}
              help="Sensitive data, prompt attacks, and escalation triggers caught"
              icon={ShieldCheckIcon}
            />
            <HeroMetric
              label="Low Confidence Prevented"
              value={formatCount(totals.low_confidence_prevented)}
              help="Answers softened instead of guessing"
              icon={ExclamationTriangleIcon}
            />
            <HeroMetric
              label="Safe Fallbacks"
              value={formatCount(totals.fallbacks)}
              help="Agent recovered when the ideal path was unavailable"
              icon={BoltIcon}
            />
            <HeroMetric
              label="Response Speed"
              value={formatMs(totals.avg_latency_ms)}
              help="Average message processing latency"
              icon={ClockIcon}
            />
          </div>

          <Section
            title="Hallucination Management"
            description="How the system avoids unsupported answers and keeps responses anchored in the knowledge base."
          >
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <StoryCard
                title="Responses Checked"
                value={formatCount(hallucination?.responses_checked || 0)}
                description="Every completed message records validation and grounding signals."
                tone="slate"
              />
              <StoryCard
                title="Grounded in KB"
                value={formatCount(hallucination?.grounded || 0)}
                description="Answers connected to retrieved documents, products, dealers, or citations."
                tone="emerald"
              />
              <StoryCard
                title="Unsupported Answers"
                value={formatCount(hallucination?.ungrounded || 0)}
                description="Responses with no recorded retrieval evidence in this time range."
                tone={(hallucination?.ungrounded || 0) > 0 ? 'amber' : 'emerald'}
              />
              <StoryCard
                title="Prevented Guessing"
                value={formatCount(hallucination?.low_confidence_prevented || 0)}
                description="Low-confidence answers replaced with a safe clarification response."
                tone="blue"
              />
            </div>
          </Section>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <Section
              title="Agents"
              description="Compare responsible-AI behavior across agents. Brand filters narrow this list."
            >
              <AgentRows agents={agents} />
            </Section>

            <Section
              title="Strapi Sync Health"
              description="Whether conversations and messages are reaching the Strapi dashboard."
            >
              {(summary?.sections.strapi_sync || []).length === 0 ? (
                <EmptyState label="No Strapi sync events yet" />
              ) : (
                <div className="space-y-3">
                  {(summary?.sections.strapi_sync || []).map((row) => (
                    <div key={`${row.operation}-${row.status}`} className="flex items-center justify-between gap-4 border-b border-slate-100 pb-3 last:border-b-0 last:pb-0">
                      <div>
                        <p className="font-mono text-sm font-semibold text-slate-950">{row.operation}</p>
                        <span className={`mt-1 inline-flex rounded-full px-2 py-1 text-xs font-semibold ring-1 ring-inset ${statusPillTone(row.status)}`}>
                          {row.status}
                        </span>
                      </div>
                      <ServerStackIcon className="h-4 w-4 text-slate-400" aria-hidden="true" />
                      <p className="font-mono text-lg font-semibold text-slate-950">{formatCount(row.count)}</p>
                    </div>
                  ))}
                </div>
              )}
            </Section>
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <Section
              title="Traffic Protection"
              description="Rate limits that protect public widgets and admin APIs from bursts or abuse."
            >
              {(summary?.sections.rate_limits || []).length === 0 ? (
                <EmptyState label="No rate-limit blocks yet" />
              ) : (
                <div className="space-y-3">
                  {(summary?.sections.rate_limits || []).map((row) => (
                    <div key={`${row.policy}-${row.outcome}`} className="flex items-center justify-between gap-4 border-b border-slate-100 pb-3 last:border-b-0 last:pb-0">
                      <div>
                        <p className="font-mono text-sm font-semibold text-slate-950">{row.policy}</p>
                        <p className="text-xs text-slate-500">{row.outcome}</p>
                      </div>
                      <p className="font-mono text-lg font-semibold text-slate-950">{formatCount(row.count)}</p>
                    </div>
                  ))}
                </div>
              )}
            </Section>

            <Section
              title="Safety Guardrails"
              description="Inputs or outputs that needed intervention."
            >
              {(summary?.sections.guardrails || []).length === 0 ? (
                <EmptyState label="No guardrail events yet" />
              ) : (
                <div className="space-y-3">
                  {(summary?.sections.guardrails || []).map((row) => (
                    <div key={`${row.action}-${row.reason}`} className="flex items-center justify-between gap-4 border-b border-slate-100 pb-3 last:border-b-0 last:pb-0">
                      <div>
                        <p className="text-sm font-semibold text-slate-950">{row.action}</p>
                        <p className="text-xs text-slate-500">{row.reason}</p>
                      </div>
                      <p className="font-mono text-lg font-semibold text-slate-950">{formatCount(row.count)}</p>
                    </div>
                  ))}
                </div>
              )}
            </Section>

            <Section
              title="Fallbacks & Latency"
              description="Graceful recovery behavior and how long responses took."
            >
              <div className="space-y-4">
                {(summary?.sections.fallbacks || []).length === 0 ? (
                  <EmptyState label="No fallback events yet" />
                ) : (
                  (summary?.sections.fallbacks || []).map((row) => (
                    <div key={`${row.stage}-${row.reason}`} className="flex items-center justify-between gap-4">
                      <div>
                        <p className="font-mono text-sm font-semibold text-slate-950">{row.stage}</p>
                        <p className="text-xs text-slate-500">{row.reason}</p>
                      </div>
                      <p className="font-mono text-lg font-semibold text-slate-950">{formatCount(row.count)}</p>
                    </div>
                  ))
                )}
                <div className="border-t border-slate-200 pt-4">
                  {(summary?.sections.latency || []).map((row) => (
                    <div key={`${row.mode}-${row.status}`} className="mt-2 flex items-center justify-between gap-4 first:mt-0">
                      <div>
                        <p className="font-mono text-sm text-slate-950">{row.mode}</p>
                        <p className="text-xs text-slate-500">{row.status} · {formatCount(row.count)} samples</p>
                      </div>
                      <p className="font-mono text-sm font-semibold text-slate-950">{formatMs(row.average_ms)}</p>
                    </div>
                  ))}
                </div>
              </div>
            </Section>
          </div>
        </>
      )}
    </div>
  );
}
