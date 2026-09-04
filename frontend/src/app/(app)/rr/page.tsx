"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import toast from "react-hot-toast";
import { rrApi, projectApi, parcelApi, unwrapList } from "@/lib/api";
import { RRCase, Project, Parcel } from "@/lib/types";
import DataTable, { Column } from "@/components/DataTable";
import Pagination from "@/components/Pagination";
import FilterBar from "@/components/FilterBar";
import StatusBadge from "@/components/StatusBadge";
import ErrorState from "@/components/ErrorState";

const STATUSES = ["NOT_STARTED", "ONGOING", "COMPLETE"];

export default function RRPage() {
  const searchParams = useSearchParams();
  const [items, setItems] = useState<RRCase[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [parcels, setParcels] = useState<Parcel[]>([]);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    const pid = searchParams?.get("project_id");
    if (pid) setFilters((f) => ({ ...f, project_id: pid }));
  }, [searchParams]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });
      const res = await rrApi.list(params);
      const data = unwrapList(res);
      setItems(data.data || []);
      setTotal(data.total || 0);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load R&R cases");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    projectApi.list({ page_size: 100 }).then((r) => setProjects(unwrapList(r).data || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (filters.project_id) {
      parcelApi.list({ project_id: Number(filters.project_id), page_size: 500 })
        .then((r) => setParcels(unwrapList(r).data || [])).catch(() => {});
    }
  }, [filters.project_id]);

  const columns = useMemo<Column<RRCase>[]>(
    () => [
      { key: "id", header: "ID", render: (c) => <span className="font-mono text-blue-700">#{c.id}</span> },
      { key: "parcel", header: "Parcel", render: (c) => c.parcel?.survey_number || `#${c.parcel_id}` },
      { key: "case_type", header: "Case Type", render: (c) => c.case_type },
      { key: "status", header: "Status", render: (c) => <StatusBadge status={c.status} /> },
      { key: "description", header: "Description", render: (c) => <span className="text-slate-600 line-clamp-1">{c.description}</span> },
    ],
    []
  );

  const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await rrApi.create({
        project_id: Number(filters.project_id) || Number(fd.get("project_id")),
        parcel_id: Number(fd.get("parcel_id")),
        case_type: String(fd.get("case_type")),
        description: String(fd.get("description")),
        rehabilitation_plan: String(fd.get("rehabilitation_plan")),
      });
      toast.success("R&R case created");
      setCreateOpen(false);
      load();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Failed to create case");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-800">Rehabilitation & Resettlement</h2>
        <button className="btn-primary" onClick={() => setCreateOpen(true)}>+ New Case</button>
      </div>

      <FilterBar
        filters={[
          { key: "project_id", label: "Project", type: "select", options: projects.map((p) => String(p.id)) },
          { key: "status", label: "Status", type: "select", options: STATUSES },
        ]}
        values={filters}
        onChange={(k, v) => { setFilters((f) => ({ ...f, [k]: v })); setPage(1); }}
        onClear={() => { setFilters({}); setPage(1); }}
      />

      { error ? (
        <ErrorState message={error} onRetry={load} />
      ) : (
        <>
          <DataTable columns={columns} data={items} loading={loading}
            emptyMessage="No R&R cases found" />
          <Pagination page={page} totalPages={Math.max(1, Math.ceil(total / pageSize))} total={total} pageSize={pageSize}
            onPageChange={setPage} onPageSizeChange={(s) => { setPageSize(s); setPage(1); }} />
        </>
      )}

      {createOpen && (
        <div className="modal-overlay" onClick={() => setCreateOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">New R&R Case</h3>
              <form onSubmit={handleCreate} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="label-text">Project</label>
                    <select name="project_id" className="select-field" defaultValue={filters.project_id || ""} required>
                      <option value="">Select</option>
                      {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>
                  </div>
                  <div><label className="label-text">Parcel *</label>
                    <select name="parcel_id" className="select-field" required>
                      <option value="">Select</option>
                      {parcels.map((pv) => <option key={pv.id} value={pv.id}>{pv.survey_number}</option>)}
                    </select>
                  </div>
                </div>
                <div><label className="label-text">Case Type *</label>
                  <select name="case_type" className="select-field" required>
                    <option>CASH_COMPENSATION</option><option>JOB_OFFER</option><option>REHABILITATION</option>
                    <option>LAND_FOR_LAND</option><option>OTHER</option>
                  </select>
                </div>
                <div><label className="label-text">Description *</label><textarea name="description" className="input-field" rows={2} required /></div>
                <div><label className="label-text">Rehabilitation Plan</label><textarea name="rehabilitation_plan" className="input-field" rows={2} /></div>
                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" className="btn-secondary" onClick={() => setCreateOpen(false)}>Cancel</button>
                  <button type="submit" className="btn-primary">Create</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
