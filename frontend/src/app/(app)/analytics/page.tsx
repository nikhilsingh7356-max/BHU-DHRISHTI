"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  analyticsApi, intelligenceApi, projectApi, unwrapList,
} from "@/lib/api";
import {
  StatePerf, Bottleneck, ResourcePriority, HistoricalAnalytic, WhatIfScenario, Project, DependencyRecord,
} from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, AreaChart, Area,
} from "recharts";

export default function AnalyticsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [statePerf, setStatePerf] = useState<StatePerf[]>([]);
  const [bottlenecks, setBottlenecks] = useState<Bottleneck[]>([]);
  const [priorities, setPriorities] = useState<ResourcePriority[]>([]);
  const [historical, setHistorical] = useState<HistoricalAnalytic[]>([]);
  const [whatif, setWhatif] = useState<WhatIfScenario[]>([]);
  const [deps, setDeps] = useState<DependencyRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [pr, sp, bn, pg, hs, wf, dp] = await Promise.all([
        projectApi.list({ page_size: 100 }),
        analyticsApi.statePerformance(),
        analyticsApi.bottlenecks(),
        intelligenceApi.priorities(),
        analyticsApi.historical({}),
        analyticsApi.whatif({}),
        intelligenceApi.dependencies({}),
      ]);
      setProjects(unwrapList(pr).data || []);
      setStatePerf(unwrapList(sp).data || []);
      setBottlenecks(unwrapList(bn).data || []);
      setPriorities(unwrapList(pg).data || []);
      setHistorical(unwrapList(hs).data || []);
      setWhatif(unwrapList(wf).data || []);
      setDeps(unwrapList(dp).data || []);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load analytics");
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const stateData = statePerf.map((s) => ({ name: s.state, value: s.avg_performance }));
  const bottleneckData = bottlenecks.map((b) => ({ name: b.district, value: b.bottleneck_count }));

  const projectName: Record<string, string> = {};
  projects.forEach((p) => { projectName[String(p.id)] = p.name; });
  const priorityRows = priorities
    .map((r) => ({ ...r, project_name: r.project_name || projectName[r.project_id] || "—" }))
    .sort((a, b) => a.priority_rank - b.priority_rank);

  const monthlyData = [
    "JAN 2025", "FEB 2025", "MAR 2025", "APR 2025", "MAY 2025", "JUN 2025",
    "JUL 2025", "AUG 2025", "SEP 2025", "OCT 2025", "NOV 2025", "DEC 2025",
    "JAN 2026",
  ].map((period) => {
    const kpis = historical.filter((h) => h.period === period);
    const get = (m: string) => {
      const avg = kpis.filter((h) => h.metric_name === m);
      if (!avg.length) return undefined;
      return Math.round((avg.reduce((s, h) => s + h.metric_value, 0) / avg.length) * 10) / 10;
    };
    return { name: period, efficiency: get("EFFICIENCY"), overrun: get("COST_OVERRUN"), sla: get("SLA_COMPLIANCE") };
  }).filter((d) => d.efficiency !== undefined || d.overrun !== undefined || d.sla !== undefined);

  const dependencyTypes = deps.map((d) => ({ name: d.dependency_type, satisfied: d.is_satisfied ? 1 : 0, value: 1 }));

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-800">Analytics & Intelligence</h2>
        <button className="btn-secondary" onClick={load}>Refresh</button>
      </div>
      <p className="text-sm text-slate-500 mb-4">DEMO / PROTOTYPE DATA — Predictive & bottleneck analytics, priority queue, trends, what-if.</p>

      <div className="grid lg:grid-cols-2 gap-4">
        {/* State comparison */}
        <div className="card p-5">
          <h3 className="font-semibold text-slate-800 mb-3">State Performance Comparison</h3>
          {stateData.length === 0 ? <EmptyState /> : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stateData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#2563eb" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Bottlenecks */}
        <div className="card p-5">
          <h3 className="font-semibold text-slate-800 mb-3">District Bottleneck Frequency</h3>
          {bottleneckData.length === 0 ? <EmptyState /> : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={bottleneckData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#d97706" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Historical trends */}
      <div className="card p-5 mt-4">
        <h3 className="font-semibold text-slate-800 mb-3">Historical KPIs (DEMO TREND)</h3>
        {monthlyData.length === 0 ? <EmptyState message="No historical KPI data" /> : (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="efficiency" stroke="#059669" name="Efficiency" />
                <Line type="monotone" dataKey="overrun" stroke="#dc2626" name="Cost Overrun" />
                <Line type="monotone" dataKey="sla" stroke="#2563eb" name="SLA Compliance" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Priority queue */}
      <div className="card p-5 mt-4">
        <h3 className="font-semibold text-slate-800 mb-3">Priority Queue (DEMO)</h3>
        {priorityRows.length === 0 ? (
          <EmptyState message="No prioritized projects" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="py-2 pr-3 font-medium">Rank</th>
                  <th className="py-2 pr-3 font-medium">Project</th>
                  <th className="py-2 pr-3 font-medium">Score</th>
                  <th className="py-2 pr-3 font-medium">Stage</th>
                  <th className="py-2 font-medium">Reasoning</th>
                </tr>
              </thead>
              <tbody>
                {priorityRows.map((r) => (
                  <tr key={r.id} className="border-b border-slate-100">
                    <td className="py-2 pr-3 font-bold text-slate-700">#{r.priority_rank}</td>
                    <td className="py-2 pr-3">
                      <Link href={`/projects/${r.project_id}`} className="text-slate-800 font-medium hover:text-blue-600 hover:underline">
                        {r.project_name}
                      </Link>
                    </td>
                    <td className="py-2 pr-3 font-semibold">{r.priority_score}</td>
                    <td className="py-2 pr-3"><StatusBadge status={r.project_status} /></td>
                    <td className="py-2 text-xs text-slate-500">{r.reasoning || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* What-if scenarios */}
      <div className="card p-5 mt-4">
        <h3 className="font-semibold text-slate-800 mb-3">What-If Scenarios (DEMO)</h3>
        {whatif.length === 0 ? (
          <EmptyState message="No what-if scenarios" />
        ) : (
          <div className="grid md:grid-cols-2 gap-3">
            {whatif.map((w) => (
              <div key={w.id} className="border border-slate-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-slate-500">{w.scenario_code}</span>
                  <span className="text-xs font-semibold text-emerald-600">−{w.estimated_time_saved_days ?? 0} days</span>
                </div>
                <div className="font-medium text-slate-800">{w.title}</div>
                <div className="text-xs text-slate-500 mb-2">{w.project_name}</div>
                <div className="text-sm text-slate-600">{w.description}</div>
                <div className="mt-2 text-xs bg-slate-50 rounded p-2 text-slate-600">
                  <span className="text-slate-400">From:</span> {w.current_completion_label} → <span className="text-emerald-600">{w.simulated_completion_label}</span>
                </div>
                <div className="mt-2 text-xs text-slate-500"><span className="font-medium text-slate-600">Intervention:</span> {w.intervention}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Dependencies */}
      <div className="card p-5 mt-4">
        <h3 className="font-semibold text-slate-800 mb-3">Stage Dependencies (DEMO)</h3>
        {deps.length === 0 ? (
          <EmptyState message="No dependencies recorded" />
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dependencyTypes}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="value" stroke="#7c3aed" fill="#7c3aed44" name="Occurrences" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {error && <div className="text-red-600 text-sm mt-4">{error}</div>}
    </div>
  );
}
