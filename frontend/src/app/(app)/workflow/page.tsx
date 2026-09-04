"use client";

import React, { useEffect, useState, useCallback } from "react";
import toast from "react-hot-toast";
import { projectApi, workflowApi, unwrapList, unwrapResult } from "@/lib/api";
import { Project, WorkflowState } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";
import ErrorState from "@/components/ErrorState";
import ProjectTimeline from "@/components/ProjectTimeline";
import { useAuth } from "@/lib/auth";

export default function WorkflowPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<number | "">("");
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [transitioning, setTransitioning] = useState(false);
  const { user } = useAuth();

  const isOfficer = user?.role?.name !== "VIEWER" && user?.role?.name !== "AUDITOR";

  const loadProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page_size: 100 });
      setProjects(unwrapList(res).data || []);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const loadWorkflow = useCallback(async (pid: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await workflowApi.getProjectWorkflow(pid);
      setWorkflow(unwrapResult(res));
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load workflow");
      setWorkflow(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (projectId) loadWorkflow(Number(projectId));
    else {
      setWorkflow(null);
      setLoading(false);
    }
  }, [projectId, loadWorkflow]);

  const handleTransition = async (newStatus: string) => {
    if (!projectId) return;
    if (!comment.trim()) {
      toast.error("Please provide a comment");
      return;
    }
    setTransitioning(true);
    try {
      await workflowApi.transition(Number(projectId), newStatus, comment);
      toast.success("Status transitioned");
      setComment("");
      await loadWorkflow(Number(projectId));
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Transition failed");
    } finally {
      setTransitioning(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold text-slate-800 mb-4">Workflow</h2>

      <div className="card p-4 mb-4">
        <label className="label-text">Select Project</label>
        <select className="select-field" value={projectId} onChange={(e) => setProjectId(e.target.value ? Number(e.target.value) : "")}>
          <option value="">Select a project...</option>
          {projects.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.project_code})</option>)}
        </select>
      </div>

      {!projectId && <div className="card p-8 text-center text-slate-400">Select a project to manage its workflow</div>}

      {projectId && error && <ErrorState message={error} onRetry={() => projectId && loadWorkflow(Number(projectId))} />}

      {projectId && !error && loading && (
        <div className="card p-6"><div className="shimmer h-48 w-full" /></div>
      )}

      {projectId && !error && !loading && workflow && (
        <div className="grid lg:grid-cols-2 gap-4">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-800">Current Status</h3>
              <StatusBadge status={workflow.current_status} />
            </div>

            {isOfficer && (
              <div className="space-y-4 mb-4">
                <div>
                  <label className="label-text">Comment *</label>
                  <textarea
                    className="input-field"
                    rows={2}
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Required for transition"
                  />
                </div>
                <div>
                  <label className="label-text">Allowed Transitions</label>
                  {workflow.allowed_transitions?.length ? (
                    <div className="flex flex-wrap gap-2">
                      {workflow.allowed_transitions.map((t) => (
                        <button key={t} className="btn-primary" onClick={() => handleTransition(t)} disabled={transitioning}>
                          {t.replace(/_/g, " ")}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-slate-400">No transitions allowed</div>
                  )}
                </div>
              </div>
            )}

            <h4 className="font-semibold text-slate-800 mb-3">History</h4>
            {workflow.history?.length ? (
              <ProjectTimeline history={workflow.history.map((h) => ({ ...h, status: h.to_status }))} />
            ) : (
              <div className="text-sm text-slate-400">No history yet</div>
            )}
          </div>

          <div className="card p-6">
            <h3 className="font-semibold text-slate-800 mb-4">Tasks</h3>
            {workflow.tasks?.length ? (
              <div className="space-y-3">
                {workflow.tasks.map((t) => (
                  <div key={t.id} className="border border-slate-200 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm text-slate-800">{t.task_type}</span>
                      <StatusBadge status={t.status} />
                    </div>
                    <div className="text-xs text-slate-500 mt-1">{t.description}</div>
                    <div className="text-xs text-slate-400 mt-1">Assigned to: {t.assigned_to} | Due: {t.due_date ? new Date(t.due_date).toLocaleDateString() : "-"}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-slate-400">No tasks assigned</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
