"use client";

import React, { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { projectApi, adminApi, unwrapResult } from "@/lib/api";
import { Project, State, District } from "@/lib/types";

interface ProjectFormProps {
  open: boolean;
  onClose: () => void;
  onSaved: (project: Project) => void;
  initial?: Project | null;
  states?: State[];
  districts?: District[];
}

const projectTypes = ["ROAD", "RAILWAY", "IRRIGATION", "POWER", "INDUSTRIAL", "URBAN", "DEFENSE", "OTHER"];
const categories = ["PUBLIC_PURPOSE", "INFRASTRUCTURE", "EDUCATIONAL", "HEALTHCARE", "URBAN_DEVELOPMENT", "INDUSTRIAL_CORRIDOR", "OTHER"];
const priorities = ["HIGH", "MEDIUM", "LOW"];
const fundingSources = ["CENTRAL_BUDGET", "STATE_BUDGET", "PPP", "BILATERAL", "MULTILATERAL", "OTHER"];

export default function ProjectForm({
  open,
  onClose,
  onSaved,
  initial,
  states: providedStates,
  districts: providedDistricts,
}: ProjectFormProps) {
  const [form, setForm] = useState<Partial<Project>>({});
  const [states, setStates] = useState<State[]>(providedStates || []);
  const [districts, setDistricts] = useState<District[]>(providedDistricts || []);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!providedStates) {
      adminApi
        .listStates()
        .then((res) => setStates(unwrapResult(res)))
        .catch(() => {});
    }
  }, [providedStates]);

  useEffect(() => {
    if (initial) setForm({ ...initial });
    else setForm({});
  }, [initial, open]);

  useEffect(() => {
    if (form.state_id && !providedDistricts) {
      adminApi
        .listDistricts(Number(form.state_id))
        .then((res) => setDistricts(unwrapResult(res)))
        .catch(() => {});
    }
  }, [form.state_id, providedDistricts]);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (initial) {
        const res = await projectApi.update(initial.id, form);
        toast.success("Project updated");
        onSaved(unwrapResult(res));
      } else {
        const res = await projectApi.create(form);
        toast.success("Project created");
        onSaved(unwrapResult(res));
      }
      onClose();
    } catch (err: unknown) {
      const msg =
        typeof err === "object" && err && "response" in err
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          ? (err as any).response?.data?.message
          : "Failed to save project";
      toast.error(msg as string);
    } finally {
      setLoading(false);
    }
  };

  const set = (key: string, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            {initial ? "Edit Project" : "New Project"}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label-text">Project Name *</label>
              <input className="input-field" required value={form.name || ""} onChange={(e) => set("name", e.target.value)} />
            </div>
            <div>
              <label className="label-text">Description</label>
              <textarea className="input-field" rows={3} value={form.description || ""} onChange={(e) => set("description", e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label-text">Project Type *</label>
                <select className="select-field" value={form.project_type || ""} onChange={(e) => set("project_type", e.target.value)}>
                  <option value="">Select</option>
                  {projectTypes.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="label-text">Public Category</label>
                <select className="select-field" value={form.public_category || ""} onChange={(e) => set("public_category", e.target.value)}>
                  <option value="">Select</option>
                  {categories.map((c) => <option key={c} value={c}>{c.replace(/_/g, " ")}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="label-text">Purpose</label>
              <input className="input-field" value={form.purpose || ""} onChange={(e) => set("purpose", e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label-text">State *</label>
                <select className="select-field" value={form.state_id || ""} onChange={(e) => { set("state_id", Number(e.target.value) || undefined); set("district_id", undefined); }}>
                  <option value="">Select</option>
                  {states.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div>
                <label className="label-text">District *</label>
                <select className="select-field" value={form.district_id || ""} onChange={(e) => set("district_id", Number(e.target.value) || undefined)}>
                  <option value="">Select</option>
                  {districts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="label-text">Priority</label>
                <select className="select-field" value={form.priority || "MEDIUM"} onChange={(e) => set("priority", e.target.value)}>
                  {priorities.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div>
                <label className="label-text">Area (sq m) *</label>
                <input type="number" className="input-field" required min={0} value={form.proposed_area_sq_m || ""} onChange={(e) => set("proposed_area_sq_m", Number(e.target.value))} />
              </div>
              <div>
                <label className="label-text">Est. Cost (₹) *</label>
                <input type="number" className="input-field" required min={0} value={form.estimated_cost || ""} onChange={(e) => set("estimated_cost", Number(e.target.value))} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label-text">Start Date *</label>
                <input type="date" className="input-field" required value={form.start_date || ""} onChange={(e) => set("start_date", e.target.value)} />
              </div>
              <div>
                <label className="label-text">Target Completion *</label>
                <input type="date" className="input-field" required value={form.target_completion_date || ""} onChange={(e) => set("target_completion_date", e.target.value)} />
              </div>
            </div>
            <div>
              <label className="label-text">Funding Source</label>
              <select className="select-field" value={form.funding_source || ""} onChange={(e) => set("funding_source", e.target.value)}>
                <option value="">Select</option>
                {fundingSources.map((f) => <option key={f} value={f}>{f.replace(/_/g, " ")}</option>)}
              </select>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? "Saving..." : initial ? "Update" : "Create"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
