"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { reportsApi, unwrapResult } from "@/lib/api";
import { DashboardStats } from "@/lib/types";
import StatCard from "@/components/StatCard";
import ErrorState from "@/components/ErrorState";
import Skeleton from "@/components/Skeleton";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";

const COLORS = ["#2563eb", "#059669", "#d97706", "#dc2626", "#7c3aed", "#0891b2", "#db2777", "#64748b"];

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await reportsApi.dashboardStats();
      setStats(unwrapResult(res));
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading && !stats) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold text-slate-800">Dashboard</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="card p-4"><Skeleton lines={2} /></div>
          ))}
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="card p-6"><Skeleton lines={6} /></div>
          <div className="card p-6"><Skeleton lines={6} /></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">Dashboard</h2>
        <ErrorState message={error} onRetry={load} />
      </div>
    );
  }

  const totals: Partial<DashboardStats["totals"]> = stats?.totals || {};
  const charts: Partial<DashboardStats["charts"]> = stats?.charts || {};

  const statCards = [
    { title: "Total Projects", value: totals.projects ?? 0, icon: "📁", color: "bg-blue-600" },
    { title: "Active Acquisitions", value: totals.active ?? 0, icon: "🏗️", color: "bg-emerald-600" },
    { title: "Pending Verification", value: totals.pending_verification ?? 0, icon: "🔍", color: "bg-amber-500" },
    { title: "GIS Pending", value: totals.gis_pending ?? 0, icon: "📍", color: "bg-cyan-600" },
    { title: "SLA Breaches", value: totals.sla_breaches ?? 0, icon: "⚠️", color: "bg-red-600" },
    { title: "Compensation Pending", value: totals.compensation_pending ?? 0, icon: "💰", color: "bg-rose-600" },
    { title: "R&R Pending", value: totals.rr_pending ?? 0, icon: "🏠", color: "bg-violet-600" },
    { title: "Completed", value: totals.completed ?? 0, icon: "✅", color: "bg-green-600" },
    { title: "Rejected", value: totals.rejected ?? 0, icon: "❌", color: "bg-slate-600" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-slate-800">Dashboard</h2>
        <Link href="/projects" className="text-sm text-blue-600 hover:text-blue-800 font-medium">
          View all projects →
        </Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {statCards.map((s) => (
          <StatCard key={s.title} title={s.title} value={s.value} icon={<span className="text-lg">{s.icon}</span>} color={s.color} />
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Projects by Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={charts.by_status || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" angle={-35} textAnchor="end" interval={0} height={60} tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" name="Projects" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Projects by State</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={charts.by_state || []} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={110} label>
                {(charts.by_state || []).map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Monthly Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={charts.monthly || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" name="Projects" stroke="#2563eb" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">SLA Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={charts.sla || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" name="SLA%" fill="#059669" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
