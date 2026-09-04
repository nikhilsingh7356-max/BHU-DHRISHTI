"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { intelligenceApi, unwrapList } from "@/lib/api";
import { DataConflict } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";

function severityColor(sev?: string) {
  switch (sev) {
    case "CRITICAL": return "bg-red-100 text-red-700";
    case "HIGH": return "bg-orange-100 text-orange-700";
    case "MEDIUM": return "bg-amber-100 text-amber-700";
    case "LOW": return "bg-blue-100 text-blue-700";
    default: return "bg-slate-100 text-slate-600";
  }
}

export default function ConflictsPage() {
  const [conflicts, setConflicts] = useState<DataConflict[]>([]);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (statusFilter !== "ALL") params.status = statusFilter;
      if (severityFilter !== "ALL") params.severity = severityFilter;
      const res = await intelligenceApi.conflicts(params);
      setConflicts(unwrapList(res).data || []);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load conflicts");
    }
  }, [statusFilter, severityFilter]);

  useEffect(() => { load(); }, [load]);

  const resolved = conflicts.filter((c) => c.status === "RESOLVED").length;
  const open = conflicts.length - resolved;
  const critical = conflicts.filter((c) => c.severity === "CRITICAL" && c.status !== "RESOLVED").length;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-800">Data Conflicts (DEMO)</h2>
        <button className="btn-secondary" onClick={load}>Refresh</button>
      </div>
      <p className="text-sm text-slate-500 mb-4">Cross-source record discrepancies (e.g., revenue ≠ GIS area).</p>
      {error && <div className="text-red-600 text-sm mb-4">{error}</div>}

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-slate-800">{conflicts.length}</div>
          <div className="text-sm text-slate-500">Total Conflicts</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-amber-600">{open}</div>
          <div className="text-sm text-slate-500">Open</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-red-600">{critical}</div>
          <div className="text-sm text-slate-500">Critical Open</div>
        </div>
      </div>

      <div className="flex gap-3 mb-4">
        <select className="select-field" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="ALL">All statuses</option>
          <option value="OPEN">Open</option>
          <option value="RESOLVED">Resolved</option>
        </select>
        <select className="select-field" value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
          <option value="ALL">All severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      <div className="card p-5">
        {conflicts.length === 0 ? (
          <EmptyState message="No conflicts match the filters" />
        ) : (
          <div className="space-y-3">
            {conflicts.map((c) => (
              <div key={c.id} className="border border-slate-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-700">{c.conflict_code}</span>
                    <StatusBadge status={c.status} />
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${severityColor(c.severity)}`}>{c.severity}</span>
                  </div>
                  <Link href={`/projects/${c.project_id}`} className="text-blue-600 text-xs hover:underline">Project →</Link>
                </div>
                <div className="text-sm text-slate-700 font-medium">{c.field_name}</div>
                <div className="mt-2 grid md:grid-cols-2 gap-3 text-sm">
                  <div className="bg-red-50 border border-red-100 rounded p-2">
                    <div className="text-xs font-semibold text-red-500 mb-1">{c.source_a} (SOURCE A)</div>
                    <pre className="text-xs text-slate-700 whitespace-pre-wrap">{JSON.stringify(c.new_value)}</pre>
                  </div>
                  <div className="bg-emerald-50 border border-emerald-100 rounded p-2">
                    <div className="text-xs font-semibold text-emerald-600 mb-1">{c.source_b} (SOURCE B)</div>
                    <pre className="text-xs text-slate-700 whitespace-pre-wrap">{JSON.stringify(c.old_value)}</pre>
                  </div>
                </div>
                {c.resolution_reason && (
                  <div className="mt-2 text-xs text-slate-500"><span className="font-medium">Resolution:</span> {c.resolution_reason}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
