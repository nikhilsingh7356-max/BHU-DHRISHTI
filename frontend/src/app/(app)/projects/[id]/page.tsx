"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import toast from "react-hot-toast";
import {
  projectApi,
  parcelApi,
  documentApi,
  workflowApi,
  jurisdictionApi,
  gisApi,
  compensationApi,
  rrApi,
  objectionApi,
  unwrapResult,
  unwrapList,
} from "@/lib/api";
import {
  Project,
  Parcel,
  Document,
  WorkflowState,
  Compensation,
  RRCase,
  Objection,
  StatusHistory,
  GISVerification,
} from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";
import ErrorState from "@/components/ErrorState";
import EmptyState from "@/components/EmptyState";
import Skeleton from "@/components/Skeleton";
import MapView from "@/components/MapViewDynamic";
import ProjectTimeline from "@/components/ProjectTimeline";
import { useAuth } from "@/lib/auth";

type Tab =
  | "overview"
  | "parcels"
  | "gis"
  | "documents"
  | "verification"
  | "workflow"
  | "jurisdiction"
  | "compensation"
  | "rr"
  | "objections"
  | "activity";

const tabs: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "parcels", label: "Parcels" },
  { id: "gis", label: "GIS" },
  { id: "documents", label: "Documents" },
  { id: "verification", label: "Verification" },
  { id: "workflow", label: "Workflow" },
  { id: "jurisdiction", label: "Jurisdiction" },
  { id: "compensation", label: "Compensation" },
  { id: "rr", label: "R&R" },
  { id: "objections", label: "Objections" },
  { id: "activity", label: "Activity" },
];

const fmtMoney = (n: number) => `₹${(n / 10000000).toFixed(2)} Cr`;

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const projectId = Number(params?.id);
  const { user } = useAuth();

  const [project, setProject] = useState<Project | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // tab sub-states
  const [parcels, setParcels] = useState<Parcel[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [timeline, setTimeline] = useState<StatusHistory[]>([]);
  const [compensations, setCompensations] = useState<Compensation[]>([]);
  const [rrCases, setRrCases] = useState<RRCase[]>([]);
  const [objections, setObjections] = useState<Objection[]>([]);
  const [verifications, setVerifications] = useState<GISVerification[]>([]);
  const [activity, setActivity] = useState<Record<string, unknown>[]>([]);

  const [transitionComment, setTransitionComment] = useState("");
  const [transitionLoading, setTransitionLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const isOfficer =
    user?.role?.name !== "VIEWER" &&
    user?.role?.name !== "AUDITOR";

  const loadProject = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await projectApi.get(projectId);
      const p = unwrapResult(res);
      setProject(p);
      if (p.parcels) setParcels(p.parcels);
      if (p.documents) setDocuments(p.documents);
      if (p.compensation) setCompensations(p.compensation);
      if (p.rr_cases) setRrCases(p.rr_cases);
      if (p.objections) setObjections(p.objections);
      if (p.gis_verifications) setVerifications(p.gis_verifications);

      // Fetch tab-specific data in parallel for robustness
      const [activityRes, workflowRes, timelineRes] = await Promise.all([
        projectApi.activity(projectId).catch(() => null),
        workflowApi.getProjectWorkflow(projectId).catch(() => null),
        projectApi.timeline(projectId).catch(() => null),
      ]);
      if (activityRes) setActivity(unwrapResult(activityRes)?.activities || []);
      if (workflowRes) setWorkflow(unwrapResult(workflowRes));
      if (timelineRes) setTimeline(unwrapResult(timelineRes)?.history || []);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load project");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) loadProject();
  }, [projectId, loadProject]);

  const loadParcels = async () => {
    try {
      const res = await parcelApi.list({ project_id: projectId, page_size: 100 });
      const data = unwrapList(res);
      setParcels(data.data || []);
    } catch {
      // keep existing
    }
  };

  const loadDocs = async () => {
    try {
      const res = await documentApi.listByProject(projectId);
      setDocuments(unwrapResult(res) || []);
    } catch {
      // keep
    }
  };

  const loadWorkflow = async () => {
    try {
      const res = await workflowApi.getProjectWorkflow(projectId);
      setWorkflow(unwrapResult(res));
    } catch {
      // keep
    }
  };

  const loadSections = async () => {
    await Promise.all([
      loadParcels(),
      loadDocs(),
      loadWorkflow(),
      compensationApi.list({ project_id: projectId, page_size: 100 }).then((r) => setCompensations(unwrapList(r).data || [])).catch(() => {}),
      rrApi.list({ project_id: projectId, page_size: 100 }).then((r) => setRrCases(unwrapList(r).data || [])).catch(() => {}),
      objectionApi.listByProject(projectId).then((r) => setObjections(unwrapResult(r) || [])).catch(() => {}),
      gisApi.getVerifications(projectId).then((r) => setVerifications(unwrapResult(r) || [])).catch(() => {}),
    ]);
  };

  useEffect(() => {
    if (!loading && project) loadSections();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  if (loading) {
    return (
      <div>
        <div className="mb-4"><Skeleton lines={1} /></div>
        <div className="card p-6"><Skeleton lines={8} /></div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div>
        <div className="mb-4 flex items-center gap-3">
          <Link href="/projects" className="text-blue-600 hover:text-blue-800">← Back</Link>
        </div>
        <ErrorState message={error || "Project not found"} onRetry={loadProject} />
      </div>
    );
  }

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await projectApi.submit(projectId);
      toast.success("Project submitted for review");
      await loadProject();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Submit failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleTransition = async (newStatus: string) => {
    if (!transitionComment.trim()) {
      toast.error("Please provide a comment");
      return;
    }
    setTransitionLoading(true);
    try {
      await workflowApi.transition(projectId, newStatus, transitionComment);
      toast.success("Status updated");
      setTransitionComment("");
      await loadProject();
      await loadWorkflow();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Transition failed");
    } finally {
      setTransitionLoading(false);
    }
  };

  const handleJurisdictionSuggest = async () => {
    try {
      await jurisdictionApi.suggest(projectId);
      toast.success("Jurisdiction suggestion generated");
      await loadProject();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Suggestion failed");
    }
  };

  const handleJurisdictionConfirm = async () => {
    try {
      await jurisdictionApi.confirm(project.jurisdiction?.id || 0, "Confirmed by officer");
      toast.success("Jurisdiction confirmed");
      await loadProject();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Confirmation failed");
    }
  };

  const handleGisVerify = async (parcelId: number) => {
    try {
      await gisApi.verify(projectId, parcelId);
      toast.success("GIS verification completed");
      await loadParcels();
      gisApi.getVerifications(projectId).then((r) => setVerifications(unwrapResult(r) || [])).catch(() => {});
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "GIS verification failed");
    }
  };

  const handleDocumentUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    formData.append("project_id", String(projectId));
    try {
      await documentApi.upload(formData);
      toast.success("Document uploaded");
      e.currentTarget.reset();
      await loadDocs();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Upload failed");
    }
  };

  const renderTab = () => {
    switch (tab) {
      case "overview":
        return (
          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="card p-6">
                <h4 className="font-semibold text-slate-800 mb-4">Project Details</h4>
                <div className="space-y-3 text-sm">
                  <div><span className="text-slate-500 font-medium">Code:</span> <span className="font-mono text-blue-700">{project.project_code}</span></div>
                  <div><span className="text-slate-500 font-medium">Type:</span> {project.project_type}</div>
                  <div><span className="text-slate-500 font-medium">Purpose:</span> {project.purpose}</div>
                  <div><span className="text-slate-500 font-medium">Public Category:</span> {project.public_category}</div>
                  <div><span className="text-slate-500 font-medium">State:</span> {project.state_name || project.state_id}</div>
                  <div><span className="text-slate-500 font-medium">District:</span> {project.district_name || project.district_id}</div>
                  <div><span className="text-slate-500 font-medium">Sponsor:</span> {project.sponsor_name || "-"}</div>
                  <div><span className="text-slate-500 font-medium">Priority:</span> <StatusBadge status={project.priority} /></div>
                  <div><span className="text-slate-500 font-medium">Area:</span> {(project.proposed_area_sq_m ?? 0).toLocaleString()} sq m</div>
                  <div><span className="text-slate-500 font-medium">Est. Cost:</span> {fmtMoney(project.estimated_cost || 0)}</div>
                  <div><span className="text-slate-500 font-medium">Start:</span> {project.start_date}</div>
                  <div><span className="text-slate-500 font-medium">Target Completion:</span> {project.target_completion_date}</div>
                  <div><span className="text-slate-500 font-medium">Funding Source:</span> {project.funding_source || "-"}</div>
                  <div><span className="text-slate-500 font-medium">Status:</span> <StatusBadge status={project.status} /></div>
                </div>
              </div>
              <div className="card p-6">
                <h4 className="font-semibold text-slate-800 mb-4">Description</h4>
                <p className="text-sm text-slate-600 whitespace-pre-wrap">{project.description || "No description provided."}</p>
              </div>
            </div>
            {project.status === "DRAFT" && isOfficer && (
              <div className="card p-6 flex items-center justify-between">
                <div>
                  <div className="font-medium text-slate-800">Ready to submit?</div>
                  <div className="text-sm text-slate-500">Submit this project for review and workflow initiation.</div>
                </div>
                <button className="btn-primary" onClick={handleSubmit} disabled={submitting}>
                  {submitting ? "Submitting..." : "Submit Project"}
                </button>
              </div>
            )}

            <div className="card p-6">
              <h4 className="font-semibold text-slate-800 mb-4">Status Timeline</h4>
              <ProjectTimeline history={timeline} />
            </div>
          </div>
        );

      case "parcels":
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-slate-800">Linked Parcels ({parcels.length})</h4>
              <Link href={`/parcels?project_id=${projectId}`} className="btn-secondary">Manage Parcels</Link>
            </div>
            {parcels.length === 0 ? (
              <EmptyState message="No parcels linked to this project yet" />
            ) : (
              <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="table-header">
                      <tr>
                        {["Survey #", "Khasra", "Village", "Area (sq m)", "Status", "Owners"].map((h) => (
                          <th key={h} className="px-4 py-3 font-semibold">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-100">
                      {parcels.map((p) => (
                        <tr key={p.id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 text-sm">{p.survey_number}</td>
                          <td className="px-4 py-3 text-sm">{p.khasra_number}</td>
                          <td className="px-4 py-3 text-sm">{p.village_name || "-"}</td>
                          <td className="px-4 py-3 text-sm">{(p.area_sq_m || 0).toLocaleString()}</td>
                          <td className="px-4 py-3"><StatusBadge status={p.current_status} /></td>
                          <td className="px-4 py-3 text-sm">{p.owners?.length || 0}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        );

      case "gis":
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-slate-800">GIS Map</h4>
              {isOfficer && parcels.length > 0 && (
                <button className="btn-primary" onClick={() => handleGisVerify(parcels[0]?.id)}>
                  Run GIS Verification
                </button>
              )}
            </div>
            {parcels.length === 0 ? (
              <EmptyState message="No parcels with geometry to display" />
            ) : (
              <MapView parcels={parcels} height={500} />
            )}
            <div className="card p-6">
              <h5 className="font-semibold text-slate-800 mb-3">Verifications</h5>
              {verifications.length === 0 ? (
                <EmptyState message="No GIS verifications recorded" />
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="table-header">
                      <tr>
                        {["Parcel", "Status", "Verified Area", "Discrepancy", "Date"].map((h) => (
                          <th key={h} className="px-4 py-3 font-semibold">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-100">
                      {verifications.map((v) => (
                        <tr key={v.id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 text-sm">#{v.parcel_id}</td>
                          <td className="px-4 py-3"><StatusBadge status={v.status} /></td>
                          <td className="px-4 py-3 text-sm">{v.verified_area_sq_m.toLocaleString()}</td>
                          <td className="px-4 py-3 text-sm">{v.discrepancy?.toFixed(2) ?? "-"}</td>
                          <td className="px-4 py-3 text-sm">{new Date(v.verified_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        );

      case "documents":
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-slate-800">Documents</h4>
            </div>
            {isOfficer && (
              <div className="card p-6">
                <h5 className="font-semibold text-slate-800 mb-3">Upload Document</h5>
                <form onSubmit={handleDocumentUpload} className="flex flex-wrap items-end gap-3">
                  <div className="flex-1 min-w-[150px]">
                    <label className="label-text">Title *</label>
                    <input name="title" className="input-field" required placeholder="Document title" />
                  </div>
                  <div className="flex-1 min-w-[150px]">
                    <label className="label-text">Type *</label>
                    <select name="document_type" className="select-field" required>
                      <option value="">Select</option>
                      <option value="LAND_RECORD">Land Record</option>
                      <option value="SURVEY_REPORT">Survey Report</option>
                      <option value="GIS_REPORT">GIS Report</option>
                      <option value="LEGAL_NOTICE">Legal Notice</option>
                      <option value="COMPENSATION">Compensation</option>
                      <option value="APPROVAL">Approval</option>
                      <option value="OTHER">Other</option>
                    </select>
                  </div>
                  <div className="flex-1 min-w-[200px]">
                    <label className="label-text">File *</label>
                    <input type="file" name="file" className="input-field" required />
                  </div>
                  <button type="submit" className="btn-primary">Upload</button>
                </form>
              </div>
            )}
            {documents.length === 0 ? (
              <EmptyState message="No documents uploaded" />
            ) : (
              <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="table-header">
                      <tr>
                        {["Title", "Type", "Status", "Uploaded", "Actions"].map((h) => (
                          <th key={h} className="px-4 py-3 font-semibold">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-100">
                      {documents.map((d) => (
                        <tr key={d.id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 text-sm font-medium text-slate-800">{d.title}</td>
                          <td className="px-4 py-3 text-sm">{d.document_type}</td>
                          <td className="px-4 py-3"><StatusBadge status={d.verification_status} /></td>
                          <td className="px-4 py-3 text-sm">{new Date(d.created_at).toLocaleDateString()}</td>
                          <td className="px-4 py-3">
                            <div className="flex gap-2">
                              <a href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${d.file_path}`} target="_blank" className="text-blue-600 text-sm hover:underline" rel="noreferrer">
                                View
                              </a>
                              {isOfficer && d.verification_status === "UPLOADED" && (
                                <>
                                  <button
                                    className="text-emerald-600 text-sm hover:underline"
                                    onClick={async () => {
                                      try {
                                        await documentApi.verify(d.id, "APPROVED", "Approved by officer");
                                        toast.success("Document approved");
                                        await loadDocs();
                                      } catch (err: unknown) {
                                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                        toast.error((err as any)?.response?.data?.message || "Verification failed");
                                      }
                                    }}
                                  >
                                    Approve
                                  </button>
                                  <button
                                    className="text-red-600 text-sm hover:underline"
                                    onClick={async () => {
                                      try {
                                        await documentApi.verify(d.id, "REJECTED", "Rejected by officer");
                                        toast.success("Document rejected");
                                        await loadDocs();
                                      } catch (err: unknown) {
                                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                        toast.error((err as any)?.response?.data?.message || "Verification failed");
                                      }
                                    }}
                                  >
                                    Reject
                                  </button>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        );

      case "verification":
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-slate-800">Verification Records</h4>
            </div>
            {verifications.length === 0 ? (
              <EmptyState message="No verification records for this project" />
            ) : (
              <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="table-header">
                      <tr>
                        {["Parcel", "Status", "Verified Area", "Discrepancy", "Date"].map((h) => (
                          <th key={h} className="px-4 py-3 font-semibold">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-100">
                      {verifications.map((v) => (
                        <tr key={v.id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 text-sm">#{v.parcel_id}</td>
                          <td className="px-4 py-3"><StatusBadge status={v.status} /></td>
                          <td className="px-4 py-3 text-sm">{v.verified_area_sq_m.toLocaleString()}</td>
                          <td className="px-4 py-3 text-sm">{v.discrepancy?.toFixed(2) ?? "-"}</td>
                          <td className="px-4 py-3 text-sm">{new Date(v.verified_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        );

      case "workflow":
        return (
          <div className="grid lg:grid-cols-2 gap-4">
            <div className="card p-6">
              <h4 className="font-semibold text-slate-800 mb-4">Workflow</h4>
              {workflow ? (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-sm text-slate-500">Current Status:</span>
                    <StatusBadge status={workflow.current_status} />
                  </div>
                  {isOfficer && (
                    <div className="space-y-3">
                      <div>
                        <label className="label-text">Allowed Transitions</label>
                        <div className="flex flex-wrap gap-2">
                          {workflow.allowed_transitions?.length ? (
                            workflow.allowed_transitions.map((t) => (
                              <button key={t} className="btn-secondary" onClick={() => handleTransition(t)} disabled={transitionLoading}>
                                {t.replace(/_/g, " ")}
                              </button>
                            ))
                          ) : (
                            <span className="text-sm text-slate-400">No transitions allowed</span>
                          )}
                        </div>
                      </div>
                      <div>
                        <label className="label-text">Comment *</label>
                        <textarea
                          className="input-field"
                          rows={2}
                          value={transitionComment}
                          onChange={(e) => setTransitionComment(e.target.value)}
                          placeholder="Required for status transition"
                        />
                      </div>
                    </div>
                  )}
                  {workflow.history?.length ? (
                    <div className="mt-4">
                      <h5 className="text-sm font-semibold text-slate-600 mb-2">History</h5>
                      <ProjectTimeline history={workflow.history.map((h) => ({ ...h, status: h.to_status }))} />
                    </div>
                  ) : (
                    <div className="text-sm text-slate-400 mt-2">No history yet</div>
                  )}
                </div>
              ) : (
                <EmptyState message="Workflow not available" />
              )}
            </div>
            <div className="card p-6">
              <h4 className="font-semibold text-slate-800 mb-4">Tasks</h4>
              {workflow?.tasks?.length ? (
                <div className="space-y-3">
                  {workflow.tasks.map((t) => (
                    <div key={t.id} className="border border-slate-200 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm text-slate-800">{t.task_type}</span>
                        <StatusBadge status={t.status} />
                      </div>
                      <div className="text-xs text-slate-500 mt-1">{t.description}</div>
                      <div className="text-xs text-slate-400 mt-1">Assigned to: {t.assigned_to} | Due: {t.due_date}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState message="No tasks assigned" />
              )}
            </div>
          </div>
        );

      case "jurisdiction":
        return (
          <div className="card p-6">
            <h4 className="font-semibold text-slate-800 mb-4">Jurisdiction</h4>
            {project.jurisdiction ? (
              <div className="space-y-3">
                <div className="text-sm"><span className="text-slate-500 font-medium">Suggestion:</span> {project.jurisdiction.suggested_jurisdiction}</div>
                <div className="text-sm"><span className="text-slate-500 font-medium">Status:</span> <StatusBadge status={project.jurisdiction.status} /></div>
                <div className="text-sm"><span className="text-slate-500 font-medium">Comment:</span> {project.jurisdiction.comment || "-"}</div>
                {isOfficer && project.jurisdiction.status === "PENDING" && (
                  <button className="btn-success" onClick={handleJurisdictionConfirm}>Confirm Jurisdiction</button>
                )}
              </div>
            ) : (
              <div className="text-center py-6">
                <div className="text-slate-500 mb-3">No jurisdiction suggestion generated yet</div>
                {isOfficer && (
                  <button className="btn-primary" onClick={handleJurisdictionSuggest}>
                    Generate Jurisdiction Suggestion
                  </button>
                )}
              </div>
            )}
          </div>
        );

      case "compensation":
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-slate-800">Compensation Cases ({compensations.length})</h4>
              <Link href={`/compensation?project_id=${projectId}`} className="btn-secondary">Manage Compensation</Link>
            </div>
            {compensations.length === 0 ? (
              <EmptyState message="No compensation cases for this project" />
            ) : (
              <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="table-header">
                      <tr>
                        {["Parcel", "Landowner", "Assessed Value", "Total", "Status"].map((h) => (
                          <th key={h} className="px-4 py-3 font-semibold">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-100">
                      {compensations.map((c) => (
                        <tr key={c.id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 text-sm">#{c.parcel_id}</td>
                          <td className="px-4 py-3 text-sm">{c.landowner?.owner_name || `#${c.landowner_id}`}</td>
                          <td className="px-4 py-3 text-sm">₹{c.assessed_value.toLocaleString()}</td>
                          <td className="px-4 py-3 text-sm font-medium">₹{c.total_amount.toLocaleString()}</td>
                          <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        );

      case "rr":
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-slate-800">R&R Cases ({rrCases.length})</h4>
              <Link href={`/rr?project_id=${projectId}`} className="btn-secondary">Manage R&R</Link>
            </div>
            {rrCases.length === 0 ? (
              <EmptyState message="No R&R cases for this project" />
            ) : (
              <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="table-header">
                      <tr>
                        {["Parcel", "Type", "Status", "Description"].map((h) => (
                          <th key={h} className="px-4 py-3 font-semibold">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-100">
                      {rrCases.map((r) => (
                        <tr key={r.id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 text-sm">#{r.parcel_id}</td>
                          <td className="px-4 py-3 text-sm">{r.case_type}</td>
                          <td className="px-4 py-3"><StatusBadge status={r.status} /></td>
                          <td className="px-4 py-3 text-sm">{r.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        );

      case "objections":
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-slate-800">Objections ({objections.length})</h4>
              <Link href={`/objections?project_id=${projectId}`} className="btn-secondary">Manage Objections</Link>
            </div>
            {objections.length === 0 ? (
              <EmptyState message="No objections filed" />
            ) : (
              <div className="space-y-3">
                {objections.map((o) => (
                  <div key={o.id} className="card p-4">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-slate-800">{o.category}</span>
                      <StatusBadge status={o.status} />
                    </div>
                    <div className="text-sm text-slate-600">{o.description}</div>
                    <div className="text-xs text-slate-400 mt-1">Parcel #{o.parcel_id} | {new Date(o.created_at).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      case "activity":
        return (
          <div className="card p-6">
            <h4 className="font-semibold text-slate-800 mb-4">Activity Feed</h4>
            {activity.length === 0 ? (
              <EmptyState message="No activity recorded" />
            ) : (
              <ul className="space-y-3">
                {activity.map((a, i) => (
                  <li key={i} className="border-l-2 border-blue-200 pl-4 py-1">
                    <div className="text-sm text-slate-700">{String(a.action || a.message || "")}</div>
                    <div className="text-xs text-slate-400">{String(a.created_at ? new Date(String(a.created_at)).toLocaleString() : "")}</div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <Link href="/projects" className="text-blue-600 hover:text-blue-800">← Back</Link>
        <h2 className="text-xl font-semibold text-slate-800 truncate">{project.name}</h2>
        <StatusBadge status={project.status} />
      </div>

      <div className="flex overflow-x-auto gap-1 mb-4 pb-1 border-b border-slate-200">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              tab === t.id
                ? "border-blue-600 text-blue-700"
                : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="mt-4">{renderTab()}</div>
    </div>
  );
}
