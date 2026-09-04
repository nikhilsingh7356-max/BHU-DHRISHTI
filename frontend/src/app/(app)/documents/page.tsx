"use client";

import React, { useEffect, useState, useCallback } from "react";
import toast from "react-hot-toast";
import { projectApi, documentApi, unwrapList, unwrapResult } from "@/lib/api";
import { Project, Document } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";
import ErrorState from "@/components/ErrorState";
import { useAuth } from "@/lib/auth";

export default function DocumentsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<number | "">("");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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

  const loadDocs = useCallback(async (pid: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await documentApi.listByProject(pid);
      setDocuments(unwrapResult(res) || []);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (projectId) loadDocs(Number(projectId));
    else {
      setDocuments([]);
      setLoading(false);
    }
  }, [projectId, loadDocs]);

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    fd.append("project_id", String(projectId));
    try {
      await documentApi.upload(fd);
      toast.success("Document uploaded");
      e.currentTarget.reset();
      if (projectId) loadDocs(Number(projectId));
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Upload failed");
    }
  };

  const verify = async (docId: number, status: string) => {
    try {
      await documentApi.verify(docId, status, `Document ${status === "APPROVED" ? "approved" : "rejected"} by officer`);
      toast.success(`Document ${status === "APPROVED" ? "approved" : "rejected"}`);
      if (projectId) loadDocs(Number(projectId));
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Verification failed");
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold text-slate-800 mb-4">Documents</h2>

      <div className="card p-4 mb-4">
        <label className="label-text">Select Project</label>
        <select className="select-field" value={projectId} onChange={(e) => setProjectId(e.target.value ? Number(e.target.value) : "")}>
          <option value="">Select a project...</option>
          {projects.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.project_code})</option>)}
        </select>
      </div>

      {!projectId && (
        <div className="card p-8 text-center text-slate-400">Select a project to view and manage its documents</div>
      )}

      {projectId && isOfficer && (
        <div className="card p-6 mb-4">
          <h3 className="font-semibold text-slate-800 mb-3">Upload Document</h3>
          <form onSubmit={handleUpload} className="flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[150px]">
              <label className="label-text">Title *</label>
              <input name="title" className="input-field" required placeholder="Document title" />
            </div>
            <div className="flex-1 min-w-[150px]">
              <label className="label-text">Type *</label>
              <select name="document_type" className="select-field" required>
                <option value="">Select</option>
                <option>LAND_RECORD</option><option>SURVEY_REPORT</option><option>GIS_REPORT</option>
                <option>LEGAL_NOTICE</option><option>COMPENSATION</option><option>APPROVAL</option><option>OTHER</option>
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

      {projectId && (
        error ? (
          <ErrorState message={error} onRetry={() => projectId && loadDocs(Number(projectId))} />
        ) : loading ? (
          <div className="card p-6"><div className="shimmer h-40 w-full" /></div>
        ) : documents.length === 0 ? (
          <div className="card p-8 text-center text-slate-400">No documents for this project</div>
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
                          <a href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${d.file_path}`} target="_blank" className="text-blue-600 text-sm hover:underline" rel="noreferrer">View</a>
                          {isOfficer && d.verification_status === "UPLOADED" && (
                            <>
                              <button className="text-emerald-600 text-sm hover:underline" onClick={() => verify(d.id, "APPROVED")}>Approve</button>
                              <button className="text-red-600 text-sm hover:underline" onClick={() => verify(d.id, "REJECTED")}>Reject</button>
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
        )
      )}
    </div>
  );
}
