"use client";

import React from "react";

interface PaginationProps {
  page: number;
  totalPages: number;
  total: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
}

export default function Pagination({
  page,
  totalPages,
  total,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: PaginationProps) {
  const pages: (number | "...")[] = [];
  const maxVisible = 7;
  let start = Math.max(1, page - 3);
  const end = Math.min(totalPages, start + maxVisible - 1);
  start = Math.max(1, end - maxVisible + 1);

  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-slate-200 rounded-b-xl">
      <div className="flex items-center gap-2">
        <select
          className="select-field !w-20"
          value={pageSize}
          onChange={(e) => onPageSizeChange?.(Number(e.target.value))}
        >
          {[10, 25, 50, 100].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <span className="text-sm text-slate-500">
          Showing {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, total)} of {total}
        </span>
      </div>
      <div className="flex items-center gap-1">
        <button
          className="px-2 py-1 text-sm text-slate-600 hover:bg-slate-100 rounded disabled:opacity-40"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          ‹
        </button>
        {start > 1 && (
          <>
            <button className="px-3 py-1 text-sm text-slate-600 hover:bg-slate-100 rounded" onClick={() => onPageChange(1)}>1</button>
            {start > 2 && <span className="px-1 text-slate-400">…</span>}
          </>
        )}
        {pages.map((p, i) =>
          p === "..." ? (
            <span key={`dots-${i}`} className="px-1 text-slate-400">…</span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={`px-3 py-1 text-sm rounded ${
                p === page
                  ? "bg-blue-600 text-white font-semibold"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {p}
            </button>
          )
        )}
        {end < totalPages && (
          <>
            {end < totalPages - 1 && <span className="px-1 text-slate-400">…</span>}
            <button className="px-3 py-1 text-sm text-slate-600 hover:bg-slate-100 rounded" onClick={() => onPageChange(totalPages)}>
              {totalPages}
            </button>
          </>
        )}
        <button
          className="px-2 py-1 text-sm text-slate-600 hover:bg-slate-100 rounded disabled:opacity-40"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          ›
        </button>
      </div>
    </div>
  );
}
