"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import toast from "react-hot-toast";
import { compensationApi, projectApi, parcelApi, unwrapList } from "@/lib/api";
import { Compensation, Project, Parcel } from "@/lib/types";
import DataTable, { Column } from "@/components/DataTable";
import Pagination from "@/components/Pagination";
import FilterBar from "@/components/FilterBar";
import StatusBadge from "@/components/StatusBadge";
import ErrorState from "@/components/ErrorState";

const STATUSES = ["ASSESSED", "OFFERED", "ACCEPTED", "PAID", "DISPUTED"];

export default function CompensationPage() {
  const searchParams = useSearchParams();
  const [items, setItems] = useState<Compensation[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Compensation | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [parcels, setParcels] = useState<Parcel[]>([]);
  const [payOpen, setPayOpen] = useState(false);

  useEffect(() => {
    const pid = searchParams?.get("project_id");
    if (pid) setFilters((f) => ({ ...f, project_id: pid }));
  }, [searchParams]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });
      const res = await compensationApi.list(params);
      const data = unwrapList(res);
      setItems(data.data || []);
      setTotal(data.total || 0);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load compensation cases");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    projectApi.list({ page_size: 100 }).then((r) => setProjects(unwrapList(r).data || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (filters.project_id) {
      parcelApi.list({ project_id: Number(filters.project_id), page_size: 500 }).then((r) => setParcels(unwrapList(r).data || [])).catch(() => {});
    }
  }, [filters.project_id]);

  const columns = useMemo<Column<Compensation>[]>(
    () => [
      { key: "id", header: "ID", render: (c) => <span className="font-mono text-blue-700">#{c.id}</span> },
      { key: "parcel", header: "Parcel", render: (c) => c.parcel?.survey_number || `#${c.parcel_id}` },
      { key: "landowner", header: "Landowner", render: (c) => c.landowner?.owner_name || `#${c.landowner_id}` },
      { key: "assessed_value", header: "Assessed Value", render: (c) => `₹${c.assessed_value.toLocaleString()}` },
      { key: "total_amount", header: "Total", render: (c) => <span className="font-medium">₹{c.total_amount.toLocaleString()}</span> },
      { key: "status", header: "Status", render: (c) => <StatusBadge status={c.status} /> },
    ],
    []
  );

  const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await compensationApi.create({
        parcel_id: Number(fd.get("parcel_id")),
        landowner_id: Number(fd.get("landowner_id")) || undefined,
        assessed_value: Number(fd.get("assessed_value")),
        land_area_sq_m: Number(fd.get("land_area_sq_m")),
        total_amount: Number(fd.get("total_amount")),
        compensation_components: {},
      });
      toast.success("Compensation case created");
      setCreateOpen(false);
      load();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Failed to create case");
    }
  };

  const handleApprove = async (id: number) => {
    try {
      await compensationApi.approve(id);
      toast.success("Compensation approved");
      load();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Approval failed");
    }
  };

  const handlePayment = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selected) return;
    const fd = new FormData(e.currentTarget);
    try {
      await compensationApi.addPayment(selected.id, {
        amount: Number(fd.get("amount")),
        payment_method: String(fd.get("payment_method")),
        payment_reference: String(fd.get("payment_reference")),
      });
      toast.success("Payment recorded");
      setPayOpen(false);
      load();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Payment failed");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-800">Compensation</h2>
        <button className="btn-primary" onClick={() => setCreateOpen(true)}>+ New Case</button>
      </div>

      <FilterBar
        filters={[
          { key: "project_id", label: "Project", type: "select", options: projects.map((p) => String(p.id)) },
          { key: "status", label: "Status", type: "select", options: STATUSES },
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
            data={items}
            loading={loading}
            emptyMessage="No compensation cases found"
            onRowClick={(row) => setSelected(row as unknown as Compensation)}
          />
          <Pagination page={page} totalPages={Math.max(1, Math.ceil(total / pageSize))} total={total} pageSize={pageSize}
            onPageChange={setPage} onPageSizeChange={(s) => { setPageSize(s); setPage(1); }} />
        </>
      )}

      {/* Detail */}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-800">Compensation #{selected.id}</h3>
                <button className="text-slate-400 hover:text-slate-600" onClick={() => setSelected(null)}>✕</button>
              </div>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between"><span className="text-slate-500">Parcel</span><span>{selected.parcel?.survey_number || `#${selected.parcel_id}`}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Landowner</span><span>{selected.landowner?.owner_name || `#${selected.landowner_id}`}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Assessed Value</span><span>₹{selected.assessed_value.toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Area</span><span>{(selected.land_area_sq_m || 0).toLocaleString()} sq m</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Total Amount</span><span className="font-semibold">₹{selected.total_amount.toLocaleString()}</span></div>
                <div className="flex justify-between items-center"><span className="text-slate-500">Status</span><StatusBadge status={selected.status} /></div>
              </div>
              <div className="flex gap-2 mt-5">
                {selected.status === "ASSESSED" && (
                  <button className="btn-success flex-1" onClick={() => handleApprove(selected.id)}>Approve</button>
                )}
                {selected.status === "ACCEPTED" && (
                  <button className="btn-primary flex-1" onClick={() => setPayOpen(true)}>Record Payment</button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payment */}
      {payOpen && selected && (
        <div className="modal-overlay" onClick={() => setPayOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Record Payment</h3>
              <form onSubmit={handlePayment} className="space-y-3">
                <div><label className="label-text">Amount *</label><input type="number" name="amount" className="input-field" required min={0} /></div>
                <div><label className="label-text">Payment Method *</label>
                  <select name="payment_method" className="select-field" required><option>BANK_TRANSFER</option><option>CHEQUE</option><option>UPI</option><option>CASH</option></select>
                </div>
                <div><label className="label-text">Reference *</label><input name="payment_reference" className="input-field" required /></div>
                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" className="btn-secondary" onClick={() => setPayOpen(false)}>Cancel</button>
                  <button type="submit" className="btn-primary">Record</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Create */}
      {createOpen && (
        <div className="modal-overlay" onClick={() => setCreateOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">New Compensation Case</h3>
              <form onSubmit={handleCreate} className="space-y-3">
                <div><label className="label-text">Parcel *</label>
                  <select name="parcel_id" className="select-field" required>
                    <option value="">Select parcel</option>
                    {parcels.map((p) => <option key={p.id} value={p.id}>{p.survey_number} ({p.village_name || "-"})</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="label-text">Assessed Value *</label><input type="number" name="assessed_value" className="input-field" required min={0} /></div>
                  <div><label className="label-text">Total Amount *</label><input type="number" name="total_amount" className="input-field" required min={0} /></div>
                </div>
                <div><label className="label-text">Land Area (sq m) *</label><input type="number" name="land_area_sq_m" className="input-field" required min={0} /></div>
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
