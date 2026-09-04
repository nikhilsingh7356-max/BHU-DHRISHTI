"use client";

import React from "react";

interface FilterBarProps {
  filters: {
    key: string;
    label: string;
    type: "select" | "text";
    options?: string[];
    placeholder?: string;
  }[];
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
  onClear?: () => void;
}

export default function FilterBar({ filters, values, onChange, onClear }: FilterBarProps) {
  return (
    <div className="card p-4 mb-4">
      <div className="flex flex-wrap items-end gap-3">
        {filters.map((f) => (
          <div key={f.key} className="min-w-[150px] flex-1">
            <label className="label-text">{f.label}</label>
            {f.type === "select" ? (
              <select
                className="select-field"
                value={values[f.key] || ""}
                onChange={(e) => onChange(f.key, e.target.value)}
              >
                <option value="">All</option>
                {f.options?.map((o) => (
                  <option key={o} value={o}>{o.replace(/_/g, " ")}</option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                className="input-field"
                placeholder={f.placeholder}
                value={values[f.key] || ""}
                onChange={(e) => onChange(f.key, e.target.value)}
              />
            )}
          </div>
        ))}
        {onClear && (
          <button className="btn-secondary" onClick={onClear}>
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
