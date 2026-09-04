"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import toast from "react-hot-toast";
import { auditApi, unwrapList } from "@/lib/api";
import { AuditLog } from "@/lib/types";
import DataTable, { Column } from "@/components/DataTable";
import Pagination from "@/components/Pagination";
import FilterBar from "@/components/FilterBar";
import ErrorState from "@/components/ErrorState";

export default function AuditPage() {
  const [items, setItems] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });
      const res = await auditApi.list(params);
      const data = unwrapList(res);
      setItems(data.data || []);
      setTotal(data.total || 0);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load audit log");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => { load(); }, [load]);

  const handleExport = async () => {
    try {
      const res = await auditApi.exportCsv(
        Object.entries(filters).reduce<Record<string, string>>((acc, [k, v]) => { if (v) acc[k] = v; return acc; }, {})
      );
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit-log-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success("Export downloaded");
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.message || "Export failed");
    }
  };

  const columns = useMemo<Column<AuditLog>[]>(
    () => [
      { key: "id", header: "ID", render: (a) => <span className="font-mono">#{a.id}</span> },
      { key: "action", header: "Action", render: (a) => <span className="font-medium text-slate-800">{a.action}</span> },
      { key: "entity_type", header: "Entity", render: (a) => `${a.entity_type} #${a.entity_id}` },
      { key: "actor_name", header: "Actor", render: (a) => a.actor_name || `#${a.actor_id}` },
      { key: "details", header: "Details", render: (a) => <span className="text-slate-500 line-clamp-1">{a.details ? JSON.stringify(a.details) : "-"}</span> },
      { key: "created_at", header: "Timestamp", render: (a) => new Date(a.created_at).toLocaleString() },
    ],
    []
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-800">Audit Trail</h2>
        <button className="btn-secondary" onClick={handleExport}>Export CSV</button>
      </div>

      <FilterBar
        filters={[
          { key: "action", label: "Action", type: "text", placeholder: "e.g. CREATE, UPDATE" },
          { key: "entity_type", label: "Entity Type", type: "text", placeholder: "e.g. PROJECT" },
          { key: "start_date", label: "Start Date", type: "text", placeholder: "YYYY-MM-DD" },
          { key: "end_date", label: "End Date", type: "text", placeholder: "YYYY-MM-DD" },
        ]}
        values={filters}
        onChange={(k, v) => { setFilters((f) => ({ ...f, [k]: v })); setPage(1); }}
        onClear={() => { setFilters({}); setPage(1); }}
      />

      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : (
        <>
          <DataTable columns={columns} data={items} loading={loading} emptyMessage="No audit records found" />
          <Pagination page={page} totalPages={Math.max(1, Math.ceil(total / pageSize))} total={total} pageSize={pageSize}
            onPageChange={setPage} onPageSizeChange={(s) => { setPageSize(s); setPage(1); }} />
        </>
      )}
    </div>
  );
}
