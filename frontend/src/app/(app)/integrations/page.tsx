"use client";

import React, { useEffect, useState, useCallback } from "react";
import { analyticsApi, unwrapList } from "@/lib/api";
import { IntegrationHealth, DataProvenance } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<IntegrationHealth[]>([]);
  const [provenance, setProvenance] = useState<DataProvenance[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [inres, prres] = await Promise.all([
        analyticsApi.integrations({}),
        analyticsApi.provenance({}),
      ]);
      setIntegrations(unwrapList(inres).data || []);
      setProvenance(unwrapList(prres).data || []);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load integrations");
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-800">System Integrations & Data Provenance</h2>
        <button className="btn-secondary" onClick={load}>Refresh</button>
      </div>
      <p className="text-sm text-slate-500 mb-4">DEMO / PROTOTYPE DATA — Status of external systems and lineage of land records.</p>
      {error && <div className="text-red-600 text-sm mb-4">{error}</div>}

      <div className="card p-5 mb-6">
        <h3 className="font-semibold text-slate-800 mb-3">Integration Health (DEMO)</h3>
        {integrations.length === 0 ? (
          <EmptyState message="No integrations configured" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="py-2 pr-3 font-medium">System</th>
                  <th className="py-2 pr-3 font-medium">Type</th>
                  <th className="py-2 pr-3 font-medium">Status</th>
                  <th className="py-2 pr-3 font-medium">Records</th>
                  <th className="py-2 pr-3 font-medium">Failed</th>
                  <th className="py-2 pr-3 font-medium">Conflicts</th>
                  <th className="py-2 pr-3 font-medium">Response</th>
                  <th className="py-2 font-medium">Last Sync</th>
                </tr>
              </thead>
              <tbody>
                {integrations.map((i) => (
                  <tr key={i.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-2 pr-3">
                      <div className="font-medium text-slate-800">{i.system_name}</div>
                      <div className="text-xs text-slate-500">{i.system_code}</div>
                    </td>
                    <td className="py-2 pr-3 text-slate-600">{i.integration_type || "—"}</td>
                    <td className="py-2 pr-3"><StatusBadge status={i.status} /></td>
                    <td className="py-2 pr-3">{i.records_synced}</td>
                    <td className="py-2 pr-3">{i.failed_records}</td>
                    <td className="py-2 pr-3">{i.conflicts}</td>
                    <td className="py-2 pr-3 text-xs">{i.api_response_time_ms != null ? `${i.api_response_time_ms} ms` : "—"}</td>
                    <td className="py-2 text-xs text-slate-500">{i.last_sync ? new Date(i.last_sync).toLocaleString() : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card p-5">
        <h3 className="font-semibold text-slate-800 mb-3">Data Provenance (DEMO)</h3>
        {provenance.length === 0 ? (
          <EmptyState message="No provenance records" />
        ) : (
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-white">
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="py-2 pr-3 font-medium">Entity</th>
                  <th className="py-2 pr-3 font-medium">Source System</th>
                  <th className="py-2 pr-3 font-medium">Created By</th>
                  <th className="py-2 pr-3 font-medium">Verification</th>
                  <th className="py-2 font-medium">Last Updated</th>
                </tr>
              </thead>
              <tbody>
                {provenance.map((p) => (
                  <tr key={p.id} className="border-b border-slate-100">
                    <td className="py-2 pr-3">
                      <div className="text-slate-800">{p.entity_type}</div>
                      <div className="text-xs text-slate-400">{p.entity_id}</div>
                    </td>
                    <td className="py-2 pr-3 text-slate-600">{p.source_system}</td>
                    <td className="py-2 pr-3 text-slate-600">{p.created_by_name || "—"}</td>
                    <td className="py-2 pr-3"><StatusBadge status={p.verification_status} /></td>
                    <td className="py-2 text-xs text-slate-500">{p.last_updated ? new Date(p.last_updated).toLocaleDateString() : "—"}</td>
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
