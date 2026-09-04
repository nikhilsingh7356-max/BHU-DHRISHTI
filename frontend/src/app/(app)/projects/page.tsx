"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { projectApi, adminApi, unwrapList, unwrapResult } from "@/lib/api";
import { Project, State, District } from "@/lib/types";
import DataTable, { Column } from "@/components/DataTable";
import Pagination from "@/components/Pagination";
import FilterBar from "@/components/FilterBar";
import StatusBadge from "@/components/StatusBadge";
import ProjectForm from "@/components/ProjectForm";
import ErrorState from "@/components/ErrorState";

const PROJECT_STATUSES = [
  "DRAFT",
  "SUBMITTED",
  "UNDER_REVIEW",
  "JURISDICTION_UNDER_REVIEW",
  "JURISDICTION_CONFIRMED",
  "SURVEY_IN_PROGRESS",
  "GIS_PENDING",
  "GIS_VERIFIED",
  "VERIFICATION_PENDING",
  "VERIFICATION_IN_PROGRESS",
  "VERIFICATION_COMPLETED",
  "APPROVED",
  "ACTIVE",
  "COMPLETED",
  "REJECTED",
  "CANCELLED",
  "ON_HOLD",
];

const PRIORITIES = ["HIGH", "MEDIUM", "LOW"];

const fmtMoney = (n: number) => `₹${(n / 10000000).toFixed(2)} Cr`;
const fmtDate = (d?: string) => (d ? new Date(d).toLocaleDateString() : "-");

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [states, setStates] = useState<State[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: pageSize,
      };
      if (filters.status) params.status = filters.status;
      if (filters.priority) params.priority = filters.priority;
      if (filters.state_id) params.state_id = Number(filters.state_id);
      if (filters.district_id) params.district_id = Number(filters.district_id);
      if (filters.search) params.search = filters.search;
      const res = await projectApi.list(params);
      const data = unwrapList(res);
      setProjects(data.data || []);
      setTotal(data.total || 0);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    adminApi
      .listStates()
      .then((res) => setStates(unwrapResult(res)))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (filters.state_id) {
      adminApi
        .listDistricts(Number(filters.state_id))
        .then((res) => setDistricts(unwrapResult(res)))
        .catch(() => {});
    }
  }, [filters.state_id]);

  const columns = useMemo<Column<Project>[]>(
    () => [
      { key: "project_code", header: "Project Code", render: (p) => <span className="font-mono text-xs font-medium text-blue-700">{p.project_code}</span> },
      { key: "name", header: "Name", render: (p) => <span className="font-medium text-slate-800">{p.name}</span> },
      { key: "district_name", header: "State / District", render: (p) => `${p.state_name || "-"} / ${p.district_name || "-"}` },
      { key: "status", header: "Status", render: (p) => <StatusBadge status={p.status} /> },
      { key: "priority", header: "Priority", render: (p) => <span className={p.priority === "HIGH" ? "text-red-600 font-semibold" : p.priority === "MEDIUM" ? "text-amber-600" : "text-slate-600"}>{p.priority}</span> },
      { key: "proposed_area_sq_m", header: "Area (sq m)", render: (p) => (p.proposed_area_sq_m ?? 0).toLocaleString() },
      { key: "estimated_cost", header: "Est. Cost", render: (p) => fmtMoney(p.estimated_cost || 0) },
      { key: "created_at", header: "Created", render: (p) => fmtDate(p.created_at) },
    ],
    []
  );

  const handleFilterChange = (key: string, value: string) => {
    setFilters((f) => ({ ...f, [key]: value }));
    setPage(1);
  };

  const onSaved = () => {
    load();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-800">Projects</h2>
        <button className="btn-primary" onClick={() => setFormOpen(true)}>
          + New Project
        </button>
      </div>

      <FilterBar
        filters={[
          { key: "search", label: "Search", type: "text", placeholder: "Name or code..." },
          { key: "status", label: "Status", type: "select", options: PROJECT_STATUSES },
          { key: "priority", label: "Priority", type: "select", options: PRIORITIES },
          { key: "state_id", label: "State", type: "select", options: states.map((s) => String(s.id)) },
          { key: "district_id", label: "District", type: "select", options: districts.map((d) => String(d.id)) },
        ]}
        values={filters}
        onChange={handleFilterChange}
        onClear={() => { setFilters({}); setPage(1); }}
      />

      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : (
        <>
          <DataTable
            columns={columns}
            data={projects}
            loading={loading}
            emptyMessage="No projects found"
            onRowClick={(row) => router.push(`/projects/${(row as unknown as Project).id}`)}
          />
          <Pagination
            page={page}
            totalPages={Math.max(1, Math.ceil(total / pageSize))}
            total={total}
            pageSize={pageSize}
            onPageChange={setPage}
            onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
          />
        </>
      )}

      <ProjectForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSaved={onSaved}
        states={states}
        districts={districts}
      />
    </div>
  );
}
