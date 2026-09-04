"use client";

import React from "react";

export default function StatCard({
  title,
  value,
  icon,
  color = "bg-blue-600",
}: {
  title: string;
  value: number | string;
  icon?: React.ReactNode;
  color?: string;
}) {
  return (
    <div className="card p-4 flex items-start space-x-4 hover:shadow-md transition-shadow">
      {icon && (
        <div className={`${color} text-white p-3 rounded-lg shrink-0`}>{icon}</div>
      )}
      <div>
        <div className="text-2xl font-bold text-slate-900">{value ?? 0}</div>
        <div className="text-sm text-slate-500 font-medium mt-0.5">{title}</div>
      </div>
    </div>
  );
}
