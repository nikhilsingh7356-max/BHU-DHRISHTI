"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { reportsApi, projectApi, unwrapList, unwrapResult } from "@/lib/api";
import { Project } from "@/lib/types";
import ErrorState from "@/components/ErrorState";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";

const COLORS = ["#2563eb", "#059669", "#d97706", "#dc2626", "#7c3aed", "#0891b2"];

export default function ReportsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [projectSummary, setProjectSummary] = useState<Record<string, unknown> | null>(null);
  const [compSummary, setCompSummary] = useState<Record<string, unknown> | null>(null);
  const [slaSummary, setSlaSummary] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadSummaries = useCallback(async () => {
    setError(null);
    try {
      const [comp, sla] = await Promise.all([
        reportsApi.compensationSummary(),
        reportsApi.slaSummary(),
      ]);
      setCompSummary(unwrapResult(comp));
      setSlaSummary(unwrapResult(sla));
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load reports");
    }
  }, []);

  useEffect(() => {
    loadSummaries();
    projectApi.list({ page_size: 100 }).then((r) => setProjects(unwrapList(r).data || [])).catch(() => {});
  }, [loadSummaries]);

  const loadProjectSummary = async (pid: number) => {
    try {
      const res = await reportsApi.projectSummary(pid);
      setProjectSummary(unwrapResult(res));
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.message || "Failed to load project summary");
    }
  };

  const projectCharts = projectSummary?.charts as Record<string, { name: string; value: number }[]> | undefined;
  const compCharts = compSummary?.charts as Record<string, { name: string; value: number }[]> | undefined;
  const slaData = Array.isArray(slaSummary?.data) ? (slaSummary.data as { name?: string; value?: number }[]) : [];

  return (
    <div>
      <h2 className="text-2xl font-semibold text-slate-800 mb-4">Reports</h2>

      {error && <ErrorState message={error} onRetry={loadSummaries} />}

      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-6">
          <h3 className="font-semibold text-slate-800 mb-3">Project Summary Report</h3>
          <p className="text-sm text-slate-500 mb-4">Generate a detailed summary report for a selected project.</p>
          <div className="flex gap-3">
            <select className="select-field flex-1" value={selectedProjectId} onChange={(e) => setSelectedProjectId(e.target.value)}>
              <option value="">Select project...</option>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
            <button
              className="btn-secondary"
              disabled={!selectedProjectId}
              onClick={() => selectedProjectId && loadProjectSummary(Number(selectedProjectId))}
            >
              Generate
            </button>
          </div>
          {projectSummary && (
            <div className="mt-4 text-sm space-y-1">
              {Object.entries(projectSummary).filter(([k]) => k !== "charts").map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="text-slate-500">{k.replace(/_/g, " ")}</span>
                  <span className="font-medium">{String(v)}</span>
                </div>
              ))}
            </div>
          )}
          {projectCharts && (
            <div className="mt-4 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={projectCharts.by_status || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#2563eb" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="card p-6">
          <h3 className="font-semibold text-slate-800 mb-3">Compensation Summary</h3>
          <p className="text-sm text-slate-500 mb-4">Overview of compensation across all projects.</p>
          <button className="btn-secondary" onClick={loadSummaries}>Refresh</button>
          {compSummary && (
            <div className="mt-4">
              <div className="grid grid-cols-3 gap-3 mb-4">
                {Object.entries(compSummary).filter(([k]) => k !== "charts" && k !== "data").map(([k, v]) => (
                  <div key={k} className="border border-slate-200 rounded-lg p-3 text-center">
                    <div className="text-lg font-bold text-slate-800">{String(v)}</div>
                    <div className="text-xs text-slate-500">{k.replace(/_/g, " ")}</div>
                  </div>
                ))}
              </div>
              {compCharts && (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={compCharts.by_status || []} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                        {(compCharts.by_status || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="card p-6 mt-4">
        <h3 className="font-semibold text-slate-800 mb-3">SLA Summary</h3>
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">Service Level Agreement performance indicators.</p>
          <button className="btn-secondary" onClick={loadSummaries}>Refresh</button>
        </div>
        {slaData.length > 0 ? (
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={slaData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#059669" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="text-sm text-slate-400 mt-4">No SLA data available</div>
        )}
      </div>

      <button className="btn-secondary mt-6" onClick={() => router.push("/dashboard")}>← Back to Dashboard</button>
    </div>
  );
}
