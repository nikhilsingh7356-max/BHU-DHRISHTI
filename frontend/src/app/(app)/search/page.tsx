"use client";

import React, { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { searchApi, unwrapList } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import Pagination from "@/components/Pagination";
import ErrorState from "@/components/ErrorState";

export default function SearchPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [type, setType] = useState("");
  const [results, setResults] = useState<Record<string, unknown>[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const doSearch = useCallback(
    async (q: string, t: string, p: number) => {
      if (!q.trim()) return;
      setLoading(true);
      setError(null);
      try {
        const res = await searchApi.search({ q: q.trim(), type: t || undefined, page: p, page_size: pageSize });
        const data = unwrapList(res);
        setResults(data.data || []);
        setTotal(data.total || 0);
        setSearched(true);
      } catch (err: unknown) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        setError((err as any)?.message || "Search failed");
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [pageSize]
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    doSearch(query, type, 1);
  };

  const navigate = (item: Record<string, unknown>) => {
    const entity = String(item.entity_type || item.type || "").toLowerCase();
    const id = item.id;
    if (entity === "project") router.push(`/projects/${id}`);
    else if (entity === "parcel") router.push(`/parcels?search=${item.survey_number || ""}`);
    else if (entity === "document") router.push(`/documents`);
    else if (entity === "user") router.push(`/admin`);
    else toastFallback();
  };

  const toastFallback = () => {
    import("react-hot-toast").then(({ toast }) => toast("No dedicated page for this entity"));
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold text-slate-800 mb-4">Global Search</h2>

      <form onSubmit={handleSubmit} className="card p-4 mb-4">
        <div className="flex flex-wrap gap-3">
          <input
            className="input-field flex-1 min-w-[200px]"
            placeholder="Search projects, parcels, documents, users..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <select className="select-field !w-44" value={type} onChange={(e) => setType(e.target.value)}>
            <option value="">All Types</option>
            <option value="project">Projects</option>
            <option value="parcel">Parcels</option>
            <option value="document">Documents</option>
            <option value="user">Users</option>
          </select>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
      </form>

      {error && <ErrorState message={error} onRetry={() => doSearch(query, type, page)} />}

      {searched && !error && results.length === 0 && (
        <div className="card p-8 text-center text-slate-400">No results found for &quot;{query}&quot;</div>
      )}

      {!searched && !error && (
        <div className="card p-8 text-center text-slate-400">
          Enter a search term to find land records across the system
        </div>
      )}

      {searched && results.length > 0 && !error && (
        <>
          <div className="space-y-3">
            {results.map((r, i) => {
              const entity = String(r.entity_type || r.type || "record");
              const title = String(r.name || r.title || r.survey_number || `${entity} #${r.id}`);
              return (
                <button key={i} onClick={() => navigate(r)} className="card w-full text-left p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-slate-800">{title}</div>
                    <span className="text-xs text-slate-400 uppercase">{entity}</span>
                  </div>
                  {Boolean(r.status) && <div className="mt-1"><StatusBadge status={String(r.status)} /></div>}
                  {Boolean(r.description || r.message) && (
                    <div className="text-sm text-slate-600 mt-1 line-clamp-2">{String(r.description || r.message)}</div>
                  )}
                </button>
              );
            })}
          </div>
          <Pagination page={page} totalPages={Math.max(1, Math.ceil(total / pageSize))} total={total} pageSize={pageSize}
            onPageChange={(p) => { setPage(p); doSearch(query, type, p); }} />
        </>
      )}
    </div>
  );
}
