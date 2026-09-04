"use client";

import React from "react";

const statusColors: Record<string, string> = {
  // Project statuses
  DRAFT: "bg-slate-100 text-slate-700 border-slate-200",
  SUBMITTED: "bg-blue-50 text-blue-700 border-blue-200",
  UNDER_REVIEW: "bg-amber-50 text-amber-700 border-amber-200",
  JURISDICTION_UNDER_REVIEW: "bg-purple-50 text-purple-700 border-purple-200",
  JURISDICTION_CONFIRMED: "bg-indigo-50 text-indigo-700 border-indigo-200",
  SURVEY_IN_PROGRESS: "bg-teal-50 text-teal-700 border-teal-200",
  GIS_PENDING: "bg-cyan-50 text-cyan-700 border-cyan-200",
  GIS_VERIFIED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  VERIFICATION_PENDING: "bg-orange-50 text-orange-700 border-orange-200",
  VERIFICATION_IN_PROGRESS: "bg-amber-50 text-amber-700 border-amber-200",
  VERIFICATION_COMPLETED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  APPROVED: "bg-green-50 text-green-700 border-green-200",
  ACTIVE: "bg-green-50 text-green-700 border-green-200",
  IN_PROGRESS: "bg-blue-50 text-blue-700 border-blue-200",
  COMPLETED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  REJECTED: "bg-red-50 text-red-700 border-red-200",
  CANCELLED: "bg-gray-100 text-gray-600 border-gray-200",
  PENDING: "bg-amber-50 text-amber-700 border-amber-200",
  ON_HOLD: "bg-yellow-50 text-yellow-700 border-yellow-200",
  COMPENSATION_PENDING: "bg-rose-50 text-rose-700 border-rose-200",
  COMPENSATION_IN_PROGRESS: "bg-pink-50 text-pink-700 border-pink-200",
  RR_PENDING: "bg-violet-50 text-violet-700 border-violet-200",
  RR_IN_PROGRESS: "bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200",
  CLOSED: "bg-slate-100 text-slate-600 border-slate-200",

  // Parcel statuses
  AVAILABLE: "bg-emerald-50 text-emerald-700 border-emerald-200",
  SURVEYED: "bg-blue-50 text-blue-700 border-blue-200",
  ACQUIRED: "bg-green-50 text-green-700 border-green-200",
  PENDING_: "bg-amber-50 text-amber-700 border-amber-200",

  // Document statuses
  UPLOADED: "bg-slate-100 text-slate-700 border-slate-200",
  VERIFIED: "bg-green-50 text-green-700 border-green-200",

  // Compensation statuses
  ASSESSED: "bg-blue-50 text-blue-700 border-blue-200",
  OFFERED: "bg-purple-50 text-purple-700 border-purple-200",
  ACCEPTED: "bg-green-50 text-green-700 border-green-200",
  PAID: "bg-emerald-50 text-emerald-700 border-emerald-200",
  DISPUTED: "bg-red-50 text-red-700 border-red-200",

  // RR statuses
  NOT_STARTED: "bg-slate-100 text-slate-700 border-slate-200",
  ONGOING: "bg-blue-50 text-blue-700 border-blue-200",
  COMPLETE: "bg-green-50 text-green-700 border-green-200",

  // GIS
  PASSED: "bg-green-50 text-green-700 border-green-200",
  FAILED: "bg-red-50 text-red-700 border-red-200",
  PENDING_VERIFICATION: "bg-orange-50 text-orange-700 border-orange-200",

  // Workflow
  IN_REVIEW: "bg-amber-50 text-amber-700 border-amber-200",
  ASSIGNED: "bg-indigo-50 text-indigo-700 border-indigo-200",
};

const fallbackMap: Record<string, string> = {
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  active: "bg-green-50 text-green-700 border-green-200",
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
  approved: "bg-green-50 text-green-700 border-green-200",
  verified: "bg-green-50 text-green-700 border-green-200",
  default: "bg-slate-100 text-slate-700 border-slate-200",
};

export default function StatusBadge({ status, className = "" }: { status?: string; className?: string }) {
  if (!status) return null;
  const key = status.toUpperCase();
  const color = statusColors[key] || fallbackMap[status.toLowerCase()] || fallbackMap.default;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${color} ${className}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
