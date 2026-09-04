"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import toast from "react-hot-toast";
import { parcelApi, adminApi, unwrapList, unwrapResult } from "@/lib/api";
import { Parcel, State, District } from "@/lib/types";
import DataTable, { Column } from "@/components/DataTable";
import Pagination from "@/components/Pagination";
import FilterBar from "@/components/FilterBar";
import StatusBadge from "@/components/StatusBadge";
import ErrorState from "@/components/ErrorState";

const LAND_TYPES = ["AGRICULTURAL", "RESIDENTIAL", "COMMERCIAL", "INDUSTRIAL", "WASTELAND", "FOREST", "OTHER"];
const OWNERSHIP = ["PRIVATE", "GOVERNMENT", "COMMUNITY", "TRUST", "MUTUAL"];
const STATUSES = ["AVAILABLE", "SURVEYED", "COMPENSATION_PENDING", "COMPENSATION_IN_PROGRESS", "ACQUIRED", "REJECTED"];

export default function ParcelsPage() {
  const searchParams = useSearchParams();
  const [parcels, setParcels] = useState<Parcel[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [states, setStates] = useState<State[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);
  const [selected, setSelected] = useState<Parcel | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [ownerOpen, setOwnerOpen] = useState(false);
  const [filters, setFilters] = useState<Record<string, string>>({});

  useEffect(() => {
    const projectId = searchParams?.get("project_id");
    if (projectId) setFilters((f) => ({ ...f, project_id: projectId }));
  }, [searchParams]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      Object.entries(filters).forEach(([k, v]) => {
        if (v) params[k] = v;
      });
      const res = await parcelApi.list(params);
      const data = unwrapList(res);
      setParcels(data.data || []);
      setTotal(data.total || 0);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load parcels");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    adminApi.listStates().then((r) => setStates(unwrapResult(r))).catch(() => {});
  }, []);

  useEffect(() => {
    if (filters.state_id) {
      adminApi.listDistricts(Number(filters.state_id)).then((r) => setDistricts(unwrapResult(r))).catch(() => {});
    }
  }, [filters.state_id]);

  const columns = useMemo<Column<Parcel>[]>(
    () => [
      { key: "survey_number", header: "Survey #", render: (p) => <span className="font-mono text-blue-700">{p.survey_number}</span> },
      { key: "khasra_number", header: "Khasra", render: (p) => <span className="font-mono">{p.khasra_number}</span> },
      { key: "village_name", header: "Village", render: (p) => p.village_name || "-" },
      { key: "district_name", header: "District", render: (p) => p.district_name || "-" },
      { key: "land_type", header: "Land Type", render: (p) => <span className="text-slate-600">{p.land_type}</span> },
      { key: "area_sq_m", header: "Area (sq m)", render: (p) => (p.area_sq_m || 0).toLocaleString() },
      { key: "current_status", header: "Status", render: (p) => <StatusBadge status={p.current_status} /> },
    ],
    []
  );

  const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const data: Partial<Parcel> = {
      survey_number: String(fd.get("survey_number")),
      khasra_number: String(fd.get("khasra_number")),
      land_type: String(fd.get("land_type")),
      ownership_type: String(fd.get("ownership_type")),
      area_sq_m: Number(fd.get("area_sq_m")),
      state_id: Number(fd.get("state_id")) || undefined,
      district_id: Number(fd.get("district_id")) || undefined,
    };
    try {
      await parcelApi.create(data);
      toast.success("Parcel created");
      setCreateOpen(false);
      load();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Failed to create parcel");
    }
  };

  const handleAddOwner = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selected) return;
    const fd = new FormData(e.currentTarget);
    try {
      await parcelApi.addOwner(selected.id, {
        owner_name: String(fd.get("owner_name")),
        father_husband_name: String(fd.get("father_husband_name")),
        gender: String(fd.get("gender")),
        age: Number(fd.get("age")),
        is_primary: fd.get("is_primary") === "on",
        contact_phone: String(fd.get("contact_phone")),
        address: String(fd.get("address")),
      });
      toast.success("Owner added");
      setOwnerOpen(false);
      const detail = await parcelApi.get(selected.id);
      setSelected(unwrapResult(detail));
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Failed to add owner");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-800">Parcels</h2>
        <button className="btn-primary" onClick={() => setCreateOpen(true)}>+ New Parcel</button>
      </div>

      <FilterBar
        filters={[
          { key: "search", label: "Search", type: "text", placeholder: "Survey / khasra..." },
          { key: "current_status", label: "Status", type: "select", options: STATUSES },
          { key: "state_id", label: "State", type: "select", options: states.map((s) => String(s.id)) },
          { key: "district_id", label: "District", type: "select", options: districts.map((d) => String(d.id)) },
        ]}
        values={filters}
        onChange={(k, v) => { setFilters((f) => ({ ...f, [k]: v })); setPage(1); }}
        onClear={() => { setFilters({}); setPage(1); }}
      />

      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : (
        <>
          <DataTable
            columns={columns}
            data={parcels}
            loading={loading}
            emptyMessage="No parcels found"
            onRowClick={(row) => setSelected(row as unknown as Parcel)}
          />
          <Pagination
            page={page} totalPages={Math.max(1, Math.ceil(total / pageSize))}
            total={total} pageSize={pageSize}
            onPageChange={setPage} onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
          />
        </>
      )}

      {/* Detail drawer */}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-800">
                  Parcel {selected.survey_number}
                </h3>
                <button className="text-slate-400 hover:text-slate-600" onClick={() => setSelected(null)}>✕</button>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm mb-4">
                <div className="text-slate-500">Khasra:</div><div>{selected.khasra_number}</div>
                <div className="text-slate-500">Village:</div><div>{selected.village_name || "-"}</div>
                <div className="text-slate-500">District:</div><div>{selected.district_name || "-"}</div>
                <div className="text-slate-500">Land Type:</div><div>{selected.land_type}</div>
                <div className="text-slate-500">Ownership:</div><div>{selected.ownership_type}</div>
                <div className="text-slate-500">Area:</div><div>{(selected.area_sq_m || 0).toLocaleString()} sq m</div>
                <div className="text-slate-500">Status:</div><div><StatusBadge status={selected.current_status} /></div>
              </div>

              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-slate-800">Owners</h4>
                <button className="btn-secondary !py-1 !px-2 text-xs" onClick={() => setOwnerOpen(true)}>+ Add Owner</button>
              </div>
              {selected.owners?.length ? (
                <div className="space-y-2 mb-4">
                  {selected.owners.map((o) => (
                    <div key={o.id} className="border border-slate-200 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{o.owner_name} {o.is_primary && <span className="text-xs text-blue-600">(Primary)</span>}</span>
                        <span className="text-xs text-slate-400">{o.gender}, {o.age}</span>
                      </div>
                      <div className="text-xs text-slate-500">Father/Husband: {o.father_husband_name}</div>
                      {o.contact_phone && <div className="text-xs text-slate-500">Phone: {o.contact_phone}</div>}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-slate-400 mb-4">No owners recorded</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Owner modal */}
      {ownerOpen && (
        <div className="modal-overlay" onClick={() => setOwnerOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Add Owner</h3>
              <form onSubmit={handleAddOwner} className="space-y-3">
                <div><label className="label-text">Owner Name *</label><input name="owner_name" className="input-field" required /></div>
                <div><label className="label-text">Father/Husband Name</label><input name="father_husband_name" className="input-field" /></div>
                <div className="grid grid-cols-3 gap-3">
                  <div><label className="label-text">Gender</label><select name="gender" className="select-field"><option>MALE</option><option>FEMALE</option><option>OTHER</option></select></div>
                  <div className="col-span-2"><label className="label-text">Age</label><input type="number" name="age" className="input-field" min={0} /></div>
                </div>
                <div><label className="label-text">Contact Phone</label><input name="contact_phone" className="input-field" /></div>
                <div><label className="label-text">Address</label><textarea name="address" className="input-field" rows={2} /></div>
                <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="is_primary" className="rounded" /> Is Primary Owner</label>
                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" className="btn-secondary" onClick={() => setOwnerOpen(false)}>Cancel</button>
                  <button type="submit" className="btn-primary">Add Owner</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Create modal */}
      {createOpen && (
        <div className="modal-overlay" onClick={() => setCreateOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">New Parcel</h3>
              <form onSubmit={handleCreate} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="label-text">Survey Number *</label><input name="survey_number" className="input-field" required /></div>
                  <div><label className="label-text">Khasra Number *</label><input name="khasra_number" className="input-field" required /></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="label-text">State</label>
                    <select name="state_id" className="select-field">{states.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
                  </div>
                  <div><label className="label-text">District</label>
                    <select name="district_id" className="select-field">{districts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="label-text">Land Type</label>
                    <select name="land_type" className="select-field">{LAND_TYPES.map((t) => <option key={t}>{t}</option>)}</select>
                  </div>
                  <div><label className="label-text">Ownership</label>
                    <select name="ownership_type" className="select-field">{OWNERSHIP.map((o) => <option key={o}>{o}</option>)}</select>
                  </div>
                </div>
                <div><label className="label-text">Area (sq m) *</label><input type="number" name="area_sq_m" className="input-field" required min={0} /></div>
                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" className="btn-secondary" onClick={() => setCreateOpen(false)}>Cancel</button>
                  <button type="submit" className="btn-primary">Create</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
