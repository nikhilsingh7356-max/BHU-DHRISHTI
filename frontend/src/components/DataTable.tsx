"use client";

import React from "react";

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  sortable?: boolean;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (row: T) => void;
  loading?: boolean;
  emptyMessage?: string;
}

export default function DataTable<T>({
  columns,
  data,
  onRowClick,
  loading,
  emptyMessage = "No records found",
}: DataTableProps<T>) {
  if (loading) {
    return (
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="table-header">
              <tr>
                {columns.map((c) => (
                  <th key={c.key} className="px-4 py-3 font-semibold">
                    {c.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-100">
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {columns.map((c) => (
                    <td key={c.key} className="px-4 py-3">
                      <div className="shimmer h-4 w-24"></div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="card p-8 text-center">
        <div className="text-slate-400 mb-2">
          <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
        </div>
        <div className="text-slate-500">{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="table-header">
            <tr>
              {columns.map((c) => (
                <th key={c.key} className="px-4 py-3 font-semibold whitespace-nowrap">
                  {c.header}
                  {c.sortable && (
                    <span className="ml-1 text-slate-400">↕</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-100">
            {data.map((row, idx) => (
              <tr
                key={idx}
                onClick={() => onRowClick?.(row)}
                className={onRowClick ? "cursor-pointer hover:bg-slate-50 transition-colors" : "hover:bg-slate-50"}
              >
                {columns.map((c) => (
                  <td key={c.key} className="px-4 py-3 text-sm text-slate-700 whitespace-nowrap">
                    {c.render ? c.render(row) : (row as Record<string, unknown>)[c.key] as React.ReactNode}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
