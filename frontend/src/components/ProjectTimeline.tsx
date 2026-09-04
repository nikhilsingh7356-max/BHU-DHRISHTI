"use client";

import React from "react";
import { StatusHistory } from "@/lib/types";
import StatusBadge from "./StatusBadge";

export default function ProjectTimeline({ history }: { history: StatusHistory[] }) {
  if (!history || history.length === 0) {
    return <div className="text-sm text-slate-400 py-4 text-center">No status history yet</div>;
  }

  const sorted = [...history].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  return (
    <ol className="relative border-l border-slate-200 ml-3 space-y-6">
      {sorted.map((h, idx) => (
        <li key={idx} className="ml-6">
          <span className="absolute -left-[9px] mt-1 flex h-4 w-4 items-center justify-center rounded-full bg-blue-100 ring-4 ring-white">
            <span className="h-2 w-2 rounded-full bg-blue-600"></span>
          </span>
          <div className="flex items-center gap-2 mb-1">
            <StatusBadge status={h.status} />
            <span className="text-xs text-slate-400">
              {new Date(h.created_at).toLocaleString()}
            </span>
          </div>
          {h.comment && <div className="text-sm text-slate-600">{h.comment}</div>}
          {h.actor_name && (
            <div className="text-xs text-slate-400 mt-0.5">By {h.actor_name}</div>
          )}
        </li>
      ))}
    </ol>
  );
}
