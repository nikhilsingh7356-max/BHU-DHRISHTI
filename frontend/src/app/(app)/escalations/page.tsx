"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { intelligenceApi, unwrapList } from "@/lib/api";
import { Escalation } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";

function levelColor(level: number) {
  if (level >= 4) return "bg-red-100 text-red-700";
  if (level === 3) return "bg-orange-100 text-orange-700";
  if (level === 2) return "bg-amber-100 text-amber-700";
  return "bg-blue-100 text-blue-700";
}

const LEVEL_LABEL: Record<number, string> = {
  1: "District Collector",
  2: "State Revenue / Commissioner",
  3: "State Government / Ministry",
  4: "Central / PMO Oversight",
};

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [levelFilter, setLevelFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (levelFilter !== "ALL") params.level = levelFilter;
      if (statusFilter !== "ALL") params.status = statusFilter;
      const res = await intelligenceApi.escalations(params);
      setEscalations(unwrapList(res).data || []);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load escalations");
    }
  }, [levelFilter, statusFilter]);

  useEffect(() => { load(); }, [load]);

  const open = escalations.filter((e) => e.status === "OPEN");
  const highLevel = escalations.filter((e) => e.level >= 3 && e.status === "OPEN");

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-800">Escalations (L1–L4) — DEMO</h2>
        <button className="btn-secondary" onClick={load}>Refresh</button>
      </div>
      <p className="text-sm text-slate-500 mb-4">SLA breaches and stalled stages escalated through four levels of authority.</p>
      {error && <div className="text-red-600 text-sm mb-4">{error}</div>}

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-slate-800">{escalations.length}</div>
          <div className="text-sm text-slate-500">Total</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-amber-600">{open.length}</div>
          <div className="text-sm text-slate-500">Open</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-red-600">{highLevel.length}</div>
          <div className="text-sm text-slate-500">High-Level Open (L3+)</div>
        </div>
      </div>

      <div className="flex gap-3 mb-4">
        <select className="select-field" value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)}>
          <option value="ALL">All levels</option>
          <option value="1">L1 — District</option>
          <option value="2">L2 — State Revenue</option>
          <option value="3">L3 — State Govt</option>
          <option value="4">L4 — Central</option>
        </select>
        <select className="select-field" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="ALL">All statuses</option>
          <option value="OPEN">Open</option>
          <option value="RESOLVED">Resolved</option>
        </select>
      </div>

      <div className="card p-5">
        {escalations.length === 0 ? (
          <EmptyState message="No escalations match the filters" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="py-2 pr-3 font-medium">Code</th>
                  <th className="py-2 pr-3 font-medium">Level</th>
                  <th className="py-2 pr-3 font-medium">Project</th>
                  <th className="py-2 pr-3 font-medium">Stage</th>
                  <th className="py-2 pr-3 font-medium">Status</th>
                  <th className="py-2 pr-3 font-medium">Authority</th>
                  <th className="py-2 font-medium">Trigger</th>
                </tr>
              </thead>
              <tbody>
                {escalations.map((e) => (
                  <tr key={e.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-2 pr-3 font-medium text-slate-700">{e.escalation_code}</td>
                    <td className="py-2 pr-3">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${levelColor(e.level)}`}>L{e.level}</span>
                    </td>
                    <td className="py-2 pr-3">
                      <Link href={`/projects/${e.project_id}`} className="text-slate-800 hover:text-blue-600 hover:underline">
                        {e.project_name || e.project_code}
                      </Link>
                    </td>
                    <td className="py-2 pr-3 text-slate-600">{e.stage}</td>
                    <td className="py-2 pr-3"><StatusBadge status={e.status} /></td>
                    <td className="py-2 pr-3 text-xs text-slate-600">{LEVEL_LABEL[e.level] || e.responsible_authority}</td>
                    <td className="py-2 text-xs text-slate-500">{e.trigger_reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
