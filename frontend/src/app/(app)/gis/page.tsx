"use client";

import React, { useEffect, useState, useCallback } from "react";
import toast from "react-hot-toast";
import { projectApi, parcelApi, gisApi, unwrapList, unwrapResult } from "@/lib/api";
import { Project, Parcel, GISVerification } from "@/lib/types";
import MapView from "@/components/MapViewDynamic";
import StatusBadge from "@/components/StatusBadge";
import ErrorState from "@/components/ErrorState";

export default function GisPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [parcels, setParcels] = useState<Parcel[]>([]);
  const [verifications, setVerifications] = useState<GISVerification[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingParcels, setLoadingParcels] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedParcel, setSelectedParcel] = useState<Parcel | null>(null);

  const loadProjects = useCallback(async () => {
    setLoadingProjects(true);
    try {
      const res = await projectApi.list({ page_size: 50 });
      setProjects(unwrapList(res).data || []);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load projects");
    } finally {
      setLoadingProjects(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const loadParcelsFor = useCallback(async (project: Project) => {
    setSelectedProject(project);
    setLoadingParcels(true);
    setSelectedParcel(null);
    try {
      const res = await parcelApi.list({ project_id: project.id, page_size: 500 });
      setParcels(unwrapList(res).data || []);
      gisApi.getVerifications(project.id).then((r) => setVerifications(unwrapResult(r) || [])).catch(() => {});
    } catch {
      setParcels([]);
    } finally {
      setLoadingParcels(false);
    }
  }, []);

  const handleRunVerification = async (parcelId: number) => {
    if (!selectedProject) return;
    try {
      await gisApi.verify(selectedProject.id, parcelId);
      toast.success("GIS verification completed");
      gisApi.getVerifications(selectedProject.id).then((r) => setVerifications(unwrapResult(r) || [])).catch(() => {});
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Verification failed");
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold text-slate-800 mb-4">GIS / Map</h2>

      <div className="grid lg:grid-cols-4 gap-4">
        {/* Left: project list */}
        <div className="lg:col-span-1 space-y-3">
          <div className="card p-4">
            <h3 className="font-semibold text-slate-800 mb-3">Projects</h3>
            <div className="space-y-2 max-h-[70vh] overflow-y-auto">
              {loadingProjects ? (
                Array.from({ length: 5 }).map((_, i) => <div key={i} className="shimmer h-10 w-full" />)
              ) : (
                projects.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => loadParcelsFor(p)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedProject?.id === p.id
                        ? "border-blue-500 bg-blue-50"
                        : "border-slate-200 hover:border-blue-300 hover:bg-blue-50/50"
                    }`}
                  >
                    <div className="font-medium text-sm text-slate-800 truncate">{p.name}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{p.project_code}</div>
                    <div className="mt-1"><StatusBadge status={p.status} /></div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right: map */}
        <div className="lg:col-span-3">
          {error ? (
            <ErrorState message={error} onRetry={loadProjects} />
          ) : loadingParcels ? (
            <div className="card p-6"><div className="shimmer h-96 w-full" /></div>
          ) : (
            <div className="space-y-4">
              <div className="card p-4 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-800">
                    {selectedProject ? selectedProject.name : "Select a project"}
                  </h3>
                  <div className="text-sm text-slate-500">
                    {selectedProject
                      ? `${parcels.length} parcels | ${parcels.filter((p) => p.geometry).length} with geometry`
                      : "Choose a project from the list to view parcels"}
                  </div>
                </div>
              </div>

              <MapView parcels={parcels} height={520} onParcelClick={setSelectedParcel} />

              {/* Selected parcel info */}
              {selectedParcel && (
                <div className="card p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-slate-800">Parcel {selectedParcel.survey_number}</h4>
                    <StatusBadge status={selectedParcel.current_status} />
                  </div>
                  <div className="grid md:grid-cols-3 gap-3 text-sm">
                    <div><span className="text-slate-500">Khasra:</span> {selectedParcel.khasra_number}</div>
                    <div><span className="text-slate-500">Village:</span> {selectedParcel.village_name || "-"}</div>
                    <div><span className="text-slate-500">Area:</span> {(selectedParcel.area_sq_m || 0).toLocaleString()} sq m</div>
                  </div>
                  <div className="mt-3 flex gap-2">
                    <button className="btn-primary !py-1.5 text-xs" onClick={() => handleRunVerification(selectedParcel.id)}>
                      Run GIS Verification
                    </button>
                  </div>
                </div>
              )}

              {/* Verifications table */}
              <div className="card p-4">
                <h4 className="font-semibold text-slate-800 mb-3">Verification Records</h4>
                {verifications.length === 0 ? (
                  <div className="text-sm text-slate-400 text-center py-4">No verifications yet</div>
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
          )}
        </div>
      </div>
    </div>
  );
}
