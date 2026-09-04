"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import toast from "react-hot-toast";
import { objectionApi, hearingApi, projectApi, unwrapList, unwrapResult } from "@/lib/api";
import { Objection, Project, Hearing } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";
import ErrorState from "@/components/ErrorState";

export default function ObjectionsPage() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<number | "">(() => {
    const pid = searchParams?.get("project_id");
    return pid ? Number(pid) : "";
  });
  const [objections, setObjections] = useState<Objection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [selected, setSelected] = useState<Objection | null>(null);
  const [hearings, setHearings] = useState<Hearing[]>([]);
  const [hearingOpen, setHearingOpen] = useState(false);

  const loadProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page_size: 100 });
      setProjects(unwrapList(res).data || []);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => { loadProjects(); }, [loadProjects]);

  const loadObjections = useCallback(async (pid: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await objectionApi.listByProject(pid);
      setObjections(unwrapResult(res) || []);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load objections");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (projectId) loadObjections(Number(projectId));
    else {
      setObjections([]);
      setLoading(false);
    }
  }, [projectId, loadObjections]);

  const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await objectionApi.create({
        project_id: projectId ? Number(projectId) : Number(fd.get("project_id")),
        parcel_id: Number(fd.get("parcel_id")) || undefined,
        category: String(fd.get("category")),
        description: String(fd.get("description")),
      });
      toast.success("Objection filed");
      setCreateOpen(false);
      if (projectId) loadObjections(Number(projectId));
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Failed to file objection");
    }
  };

  const openDetail = async (o: Objection) => {
    setSelected(o);
    try {
      const res = await hearingApi.listByObjection(o.id);
      setHearings(unwrapResult(res) || []);
    } catch {
      setHearings([]);
    }
  };

  const handleHearing = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selected) return;
    const fd = new FormData(e.currentTarget);
    try {
      await hearingApi.create({
        objection_id: selected.id,
        hearing_date: String(fd.get("hearing_date")),
        location: String(fd.get("location")),
      });
      toast.success("Hearing scheduled");
      setHearingOpen(false);
      openDetail(selected);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Failed to schedule hearing");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-800">Objections</h2>
        <button className="btn-primary" onClick={() => setCreateOpen(true)}>+ File Objection</button>
      </div>

      <div className="card p-4 mb-4">
        <label className="label-text">Select Project</label>
        <select className="select-field" value={projectId} onChange={(e) => setProjectId(e.target.value ? Number(e.target.value) : "")}>
          <option value="">All projects (select required)</option>
          {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>

      {error ? (
        <ErrorState message={error} onRetry={() => projectId && loadObjections(Number(projectId))} />
      ) : loading ? (
        <div className="card p-6"><div className="shimmer h-40 w-full" /></div>
      ) : !projectId ? (
        <div className="card p-8 text-center text-slate-400">Select a project to view objections</div>
      ) : objections.length === 0 ? (
        <div className="card p-8 text-center text-slate-400">No objections filed for this project</div>
      ) : (
        <div className="space-y-3">
          {objections.map((o) => (
            <button key={o.id} onClick={() => openDetail(o)} className="card w-full text-left p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-slate-800">{o.category}</span>
                <StatusBadge status={o.status} />
              </div>
              <div className="text-sm text-slate-600">{o.description}</div>
              <div className="text-xs text-slate-400 mt-1">Parcel #{o.parcel_id || "-"} | {new Date(o.created_at).toLocaleString()}</div>
            </button>
          ))}
        </div>
      )}

      {/* Detail */}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-800">{selected.category}</h3>
                <button className="text-slate-400 hover:text-slate-600" onClick={() => setSelected(null)}>✕</button>
              </div>
              <div className="text-sm text-slate-600 mb-2">{selected.description}</div>
              <div className="text-xs text-slate-400 mb-4">Status: <StatusBadge status={selected.status} /></div>

              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-slate-800">Hearings</h4>
                <button className="btn-secondary !py-1 !px-2 text-xs" onClick={() => setHearingOpen(true)}>+ Schedule</button>
              </div>
              {hearings.length ? (
                <div className="space-y-2">
                  {hearings.map((h) => (
                    <div key={h.id} className="border border-slate-200 rounded-lg p-3">
                      <div className="flex justify-between items-center">
                        <span className="font-medium text-sm">{new Date(h.hearing_date).toLocaleString()}</span>
                        <StatusBadge status={h.status} />
                      </div>
                      <div className="text-xs text-slate-500 mt-1">{h.location}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-slate-400">No hearings scheduled</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Hearing modal */}
      {hearingOpen && selected && (
        <div className="modal-overlay" onClick={() => setHearingOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Schedule Hearing</h3>
              <form onSubmit={handleHearing} className="space-y-3">
                <div><label className="label-text">Hearing Date *</label><input type="datetime-local" name="hearing_date" className="input-field" required /></div>
                <div><label className="label-text">Location *</label><input name="location" className="input-field" required /></div>
                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" className="btn-secondary" onClick={() => setHearingOpen(false)}>Cancel</button>
                  <button type="submit" className="btn-primary">Schedule</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Create objection */}
      {createOpen && (
        <div className="modal-overlay" onClick={() => setCreateOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">File Objection</h3>
              <form onSubmit={handleCreate} className="space-y-3">
                <div><label className="label-text">Project *</label>
                  <select name="project_id" className="select-field" required defaultValue={projectId || ""}>
                    <option value="">Select</option>
                    {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>
                <div><label className="label-text">Category *</label>
                  <select name="category" className="select-field" required>
                    <option>MARKET_VALUE</option><option>TITLE_DISPUTE</option><option>ACQUISITION_PROCESS</option>
                    <option>COMPENSATION_AMOUNT</option><option>BOUNDARY_DISPUTE</option><option>OTHER</option>
                  </select>
                </div>
                <div><label className="label-text">Parcel ID</label><input type="number" name="parcel_id" className="input-field" min={0} /></div>
                <div><label className="label-text">Description *</label><textarea name="description" className="input-field" rows={3} required /></div>
                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" className="btn-secondary" onClick={() => setCreateOpen(false)}>Cancel</button>
                  <button type="submit" className="btn-primary">File</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
