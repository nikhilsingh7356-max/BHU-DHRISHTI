"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import toast from "react-hot-toast";
import { projectApi, intelligenceApi, analyticsApi, adminApi, unwrapList } from "@/lib/api";
import { Project, HealthScore, Escalation, Possession, ResourcePriority, StatePerf } from "@/lib/types";
import StatCard from "@/components/StatCard";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";

function healthColor(band?: string) {
  switch (band) {
    case "HEALTHY": return "text-emerald-700 bg-emerald-50";
    case "WATCH": return "text-amber-700 bg-amber-50";
    case "AT_RISK": return "text-orange-700 bg-orange-50";
    case "CRITICAL": return "text-red-700 bg-red-100";
    default: return "text-slate-700 bg-slate-100";
  }
}

function levelColor(level: number) {
  if (level >= 4) return "bg-red-100 text-red-700";
  if (level === 3) return "bg-orange-100 text-orange-700";
  if (level === 2) return "bg-amber-100 text-amber-700";
  return "bg-blue-100 text-blue-700";
}

export default function CommandCenterPage() {
  const [statePerf, setStatePerf] = useState<StatePerf[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [health, setHealth] = useState<HealthScore[]>([]);
  const [priorities, setPriorities] = useState<ResourcePriority[]>([]);
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [possessions, setPossessions] = useState<Possession[]>([]);
  const [stateMap, setStateMap] = useState<Record<string, string>>({});
  const [selectedState, setSelectedState] = useState<string>("");
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [parcelHealth, setParcelHealth] = useState<HealthScore[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [sp, pr, hl, pg, esc, pos, st] = await Promise.all([
        analyticsApi.statePerformance(),
        projectApi.list({ page_size: 100 }),
        intelligenceApi.projectHealth(),
        intelligenceApi.priorities(),
        intelligenceApi.escalations(),
        intelligenceApi.possessions(),
        adminApi.listStates(),
      ]);
      setStatePerf(unwrapList(sp).data || []);
      setProjects(unwrapList(pr).data || []);
      setHealth(unwrapList(hl).data || []);
      setPriorities(unwrapList(pg).data || []);
      setEscalations(unwrapList(esc).data || []);
      setPossessions(unwrapList(pos).data || []);
      const sm: Record<string, string> = {};
      (unwrapList(st).data || []).forEach((s) => { if (s.id != null && s.name) sm[String(s.id)] = s.name; });
      setStateMap(sm);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.message || "Failed to load command center");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const stateOf = (p: Project) => stateMap[String(p.state_id || "")] || "Unknown";

  const groupedStates = statePerf.map((s) => s.state);
  const stateNames = Array.from(new Set(projects.map(stateOf).filter((n) => n !== "Unknown")));
  const allStateNames = Array.from(new Set([...groupedStates, ...stateNames]));

  const stateProjects = selectedState
    ? projects.filter((p) => stateOf(p) === selectedState)
    : projects;

  const projectHealthMap: Record<string, HealthScore> = {};
  health.forEach((h) => { if (h.project_id) projectHealthMap[h.project_id] = h; });
  const priorityMap: Record<string, ResourcePriority> = {};
  priorities.forEach((r) => { if (r.project_id) priorityMap[r.project_id] = r; });

  const loadProjectParcels = async (pid: string) => {
    setSelectedProject(pid);
    try {
      const ph = await intelligenceApi.parcelHealth({ project_id: pid });
      setParcelHealth(unwrapList(ph).data || []);
    } catch {
      setParcelHealth([]);
    }
  };

  const openEscalations = escalations.filter((e) => e.status === "OPEN");

  if (loading && statePerf.length === 0) {
    return <div className="text-slate-400 text-sm py-10">Loading command center…</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-800">Command Center</h2>
        <button className="btn-secondary" onClick={loadAll}>Refresh</button>
      </div>
      <p className="text-sm text-slate-500 mb-4">DEMO / PROTOTYPE DATA — National overview: India → State → District → Project → Parcel.</p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard title="Total Projects" value={projects.length} color="bg-blue-600" />
        <StatCard title="States Tracked" value={allStateNames.length} color="bg-emerald-600" />
        <StatCard title="Open Escalations" value={openEscalations.length} color="bg-red-600" />
        <StatCard title="Possessions Pending" value={possessions.filter((p) => p.possession_status !== "COMPLETED").length} color="bg-amber-600" />
      </div>

      {/* State performance strip */}
      <div className="card p-5 mb-6">
        <h3 className="font-semibold text-slate-800 mb-3">State Performance (DEMO HISTORICAL DATA)</h3>
        <div className="flex flex-wrap gap-2">
          {statePerf.map((s) => (
            <button
              key={s.state}
              onClick={() => setSelectedState(selectedState === s.state ? "" : s.state)}
              className={`px-3 py-2 rounded-lg border text-sm ${selectedState === s.state ? "border-blue-500 bg-blue-50 text-blue-700" : "border-slate-200 hover:border-blue-300"}`}
            >
              <div className="font-medium">{s.state}</div>
              <div className={`font-bold ${s.avg_performance >= 80 ? "text-emerald-600" : s.avg_performance >= 60 ? "text-amber-600" : "text-red-600"}`}>{s.avg_performance}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Breakdown of India = sum of states */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card p-5">
          <h3 className="font-semibold text-slate-800 mb-3">
            {selectedState ? `Projects — ${selectedState}` : "Projects by State (India)"}
          </h3>
          {stateProjects.length === 0 ? (
            <EmptyState message="No projects for the selected state" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b border-slate-200">
                    <th className="py-2 pr-3 font-medium">Project</th>
                    <th className="py-2 pr-3 font-medium">Stage</th>
                    <th className="py-2 pr-3 font-medium">Health</th>
                    <th className="py-2 pr-3 font-medium">Priority</th>
                    <th className="py-2 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {stateProjects.map((p) => {
                    const h = projectHealthMap[p.id];
                    const prio = priorityMap[p.id];
                    return (
                      <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-2 pr-3">
                          <div className="font-medium text-slate-800">{p.name}</div>
                          <div className="text-xs text-slate-500">{p.project_code} · {stateOf(p)}</div>
                        </td>
                        <td className="py-2 pr-3"><StatusBadge status={p.status} /></td>
                        <td className="py-2 pr-3">
                          {h ? (
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${healthColor(h.band)}`}>
                              {h.score} · {h.band.replace("_", " ")}
                            </span>
                          ) : <span className="text-slate-300">—</span>}
                        </td>
                        <td className="py-2 pr-3">
                          {prio ? (
                            <span className="text-xs font-semibold text-slate-700">#{prio.priority_rank}</span>
                          ) : <span className="text-slate-300">—</span>}
                        </td>
                        <td className="py-2">
                          <button className="text-blue-600 text-xs font-medium hover:underline" onClick={() => loadProjectParcels(String(p.id))}>
                            View parcels
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Escalations panel */}
        <div className="card p-5">
          <h3 className="font-semibold text-slate-800 mb-3">Open Escalations (L1–L4)</h3>
          {openEscalations.length === 0 ? (
            <EmptyState message="No open escalations" />
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {openEscalations.map((e) => (
                <div key={e.id} className="border border-slate-200 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-700">{e.escalation_code}</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${levelColor(e.level)}`}>L{e.level}</span>
                  </div>
                  <div className="text-sm font-medium text-slate-800">{e.project_name || "Project"}</div>
                  <div className="text-xs text-slate-500">{e.stage} · {e.responsible_authority}</div>
                  <div className="text-xs text-slate-600 mt-1">{e.trigger_reason}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Project parcel health drilldown */}
      {selectedProject && (
        <div className="card p-5 mt-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-slate-800">Parcel Health — {projects.find((p) => String(p.id) === selectedProject)?.name}</h3>
            <Link href={`/projects/${selectedProject}`} className="text-blue-600 text-sm font-medium hover:underline">
              Open project →
            </Link>
          </div>
          {parcelHealth.length === 0 ? (
            <EmptyState message="No parcel health records for this project" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b border-slate-200">
                    <th className="py-2 pr-3 font-medium">Parcel</th>
                    <th className="py-2 pr-3 font-medium">Status</th>
                    <th className="py-2 pr-3 font-medium">Score</th>
                    <th className="py-2 font-medium">Band</th>
                  </tr>
                </thead>
                <tbody>
                  {parcelHealth.map((ph) => (
                    <tr key={ph.parcel_id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-2 pr-3 font-medium text-slate-800">{ph.parcel_code || ph.parcel_id}</td>
                      <td className="py-2 pr-3"><StatusBadge status={ph.parcel_status} /></td>
                      <td className="py-2 pr-3 font-semibold text-slate-700">{ph.score}</td>
                      <td className="py-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${healthColor(ph.band)}`}>
                          {ph.band.replace("_", " ")}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Possession panel */}
      <div className="card p-5 mt-6">
        <h3 className="font-semibold text-slate-800 mb-3">Possession Tracking (bottleneck focus)</h3>
        {possessions.length === 0 ? (
          <EmptyState message="No possession records" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="py-2 pr-3 font-medium">Project</th>
                  <th className="py-2 pr-3 font-medium">Parcel</th>
                  <th className="py-2 pr-3 font-medium">Status</th>
                  <th className="py-2 pr-3 font-medium">Reason</th>
                  <th className="py-2 font-medium">Authority</th>
                </tr>
              </thead>
              <tbody>
                {possessions.slice(0, 12).map((pos) => (
                  <tr key={pos.id} className="border-b border-slate-100">
                    <td className="py-2 pr-3 text-slate-800">{pos.project_code}</td>
                    <td className="py-2 pr-3 text-slate-600">{pos.parcel_code}</td>
                    <td className="py-2 pr-3"><StatusBadge status={pos.possession_status} /></td>
                    <td className="py-2 pr-3 text-xs text-slate-500">{pos.pending_reason || "—"}</td>
                    <td className="py-2 text-xs text-slate-600">{pos.responsible_authority || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
