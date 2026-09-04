"use client";

import React, { useEffect, useState, useCallback } from "react";
import toast from "react-hot-toast";
import { adminApi, unwrapResult } from "@/lib/api";
import { User, Role, Permission, Department, State, District, SLARule, JurisdictionRule } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";
import ErrorState from "@/components/ErrorState";
import Pagination from "@/components/Pagination";

type Tab = "users" | "roles" | "departments" | "geo" | "sla" | "jurisdiction";

const tabs: { id: Tab; label: string }[] = [
  { id: "users", label: "Users" },
  { id: "roles", label: "Roles" },
  { id: "departments", label: "Departments" },
  { id: "geo", label: "States/Districts" },
  { id: "sla", label: "SLA Rules" },
  { id: "jurisdiction", label: "Jurisdiction Rules" },
];

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("users");

  return (
    <div>
      <h2 className="text-2xl font-semibold text-slate-800 mb-4">Administration</h2>
      <div className="flex overflow-x-auto gap-1 mb-4 pb-1 border-b border-slate-200">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              tab === t.id ? "border-blue-600 text-blue-700" : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "users" && <UsersTab />}
      {tab === "roles" && <RolesTab />}
      {tab === "departments" && <DepartmentsTab />}
      {tab === "geo" && <GeoTab />}
      {tab === "sla" && <SlaTab />}
      {tab === "jurisdiction" && <JurisdictionTab />}
    </div>
  );
}

function UsersTab() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (search) params.search = search;
      const res = await adminApi.listUsers(params);
      const data = unwrapResult(res);
      const list = Array.isArray(data) ? data : (data as { data: User[]; total: number });
      setUsers(Array.isArray(list) ? list : (list.data || []));
      setTotal(Array.isArray(list) ? list.length : (list.total || 0));
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    adminApi.listRoles().then((r) => setRoles(unwrapResult(r) || [])).catch(() => {});
  }, []);

  const toggleActive = async (user: User) => {
    try {
      await adminApi.updateUser(user.id, { is_active: !user.is_active });
      toast.success(`User ${user.is_active ? "deactivated" : "activated"}`);
      load();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Update failed");
    }
  };

  const changeRole = async (user: User, roleId: number) => {
    try {
      await adminApi.updateUser(user.id, { role_id: roleId } as Partial<User>);
      toast.success("Role updated");
      load();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Role update failed");
    }
  };

  const createUser = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await adminApi.createUser({
        email: String(fd.get("email")),
        password: String(fd.get("password")),
        full_name: String(fd.get("full_name")),
        role_id: Number(fd.get("role_id")),
      });
      toast.success("User created");
      setCreateOpen(false);
      load();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Failed to create user");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <input className="input-field !w-64" placeholder="Search users..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        </div>
        <button className="btn-primary" onClick={() => setCreateOpen(true)}>+ New User</button>
      </div>

      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : loading ? (
        <div className="card p-6"><div className="shimmer h-48 w-full" /></div>
      ) : (
        <>
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="table-header">
                  <tr>
                    {["User", "Email", "Role", "Status", "Actions"].map((h) => (
                      <th key={h} className="px-4 py-3 font-semibold">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-100">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-800">{u.full_name}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">{u.email}</td>
                      <td className="px-4 py-3">
                        <select
                          className="select-field !w-44 !py-1 !text-xs"
                          value={u.role?.id || ""}
                          onChange={(e) => changeRole(u, Number(e.target.value))}
                        >
                          {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={u.is_active ? "ACTIVE" : "INACTIVE"} />
                      </td>
                      <td className="px-4 py-3">
                        <button
                          className={`text-sm ${u.is_active ? "text-red-600 hover:underline" : "text-emerald-600 hover:underline"}`}
                          onClick={() => toggleActive(u)}
                        >
                          {u.is_active ? "Deactivate" : "Activate"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <Pagination page={page} totalPages={Math.max(1, Math.ceil(total / pageSize))} total={total} pageSize={pageSize}
            onPageChange={setPage} onPageSizeChange={(s) => { setPageSize(s); setPage(1); }} />
        </>
      )}

      {createOpen && (
        <div className="modal-overlay" onClick={() => setCreateOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">New User</h3>
              <form onSubmit={createUser} className="space-y-3">
                <div><label className="label-text">Full Name *</label><input name="full_name" className="input-field" required /></div>
                <div><label className="label-text">Email *</label><input type="email" name="email" className="input-field" required /></div>
                <div><label className="label-text">Password *</label><input type="password" name="password" className="input-field" required minLength={8} /></div>
                <div><label className="label-text">Role *</label>
                  <select name="role_id" className="select-field" required>
                    <option value="">Select</option>
                    {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
                  </select>
                </div>
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

function RolesTab() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([adminApi.listRoles(), adminApi.listPermissions()])
      .then(([r, p]) => {
        setRoles(unwrapResult(r) || []);
        setPermissions(unwrapResult(p) || []);
      })
      .catch((err: unknown) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        setError((err as any)?.message || "Failed to load roles");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="card p-6"><div className="shimmer h-48 w-full" /></div>;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="grid lg:grid-cols-2 gap-4">
      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 mb-3">Roles</h3>
        <div className="space-y-3">
          {roles.map((r) => (
            <div key={r.id} className="border border-slate-200 rounded-lg p-4">
              <div className="font-medium text-slate-800">{r.name}</div>
              {r.description && <div className="text-xs text-slate-500 mt-0.5">{r.description}</div>}
              <div className="text-xs text-slate-400 mt-2">
                {r.permissions ? `${r.permissions.length} permissions` : "Defaults"}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 mb-3">Permissions</h3>
        <div className="max-h-[60vh] overflow-y-auto space-y-2">
          {permissions.length === 0 ? (
            <div className="text-sm text-slate-400">No permissions listed</div>
          ) : (
            permissions.map((p) => (
              <div key={p.id} className="flex items-center justify-between border border-slate-100 rounded px-3 py-2">
                <div>
                  <span className="text-sm font-medium text-slate-700">{p.name}</span>
                  <span className="text-xs text-slate-400 ml-2">{p.resource}.{p.action}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function DepartmentsTab() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    adminApi.listDepartments()
      .then((r) => setDepartments(unwrapResult(r) || []))
      .catch((err: unknown) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        setError((err as any)?.message || "Failed to load departments");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const createDept = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await adminApi.createDepartment({ name: String(fd.get("name")), description: String(fd.get("description")) });
      toast.success("Department created");
      load();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Failed to create department");
    }
  };

  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="grid lg:grid-cols-2 gap-4">
      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 mb-3">Departments</h3>
        {loading ? (
          <div className="shimmer h-32 w-full" />
        ) : departments.length === 0 ? (
          <div className="text-sm text-slate-400">No departments</div>
        ) : (
          <div className="space-y-2">
            {departments.map((d) => (
              <div key={d.id} className="border border-slate-200 rounded-lg p-3">
                <div className="font-medium text-slate-800 text-sm">{d.name}</div>
                {d.description && <div className="text-xs text-slate-500 mt-0.5">{d.description}</div>}
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 mb-3">New Department</h3>
        <form onSubmit={createDept} className="space-y-3">
          <div><label className="label-text">Name *</label><input name="name" className="input-field" required /></div>
          <div><label className="label-text">Description</label><textarea name="description" className="input-field" rows={3} /></div>
          <button type="submit" className="btn-primary">Create</button>
        </form>
      </div>
    </div>
  );
}

function GeoTab() {
  const [states, setStates] = useState<State[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);
  const [selectedState, setSelectedState] = useState<number | "">("");

  const loadStates = useCallback(() => {
    adminApi.listStates().then((r) => setStates(unwrapResult(r) || [])).catch(() => {});
  }, []);

  useEffect(() => {
    loadStates();
  }, [loadStates]);

  useEffect(() => {
    if (selectedState) {
      adminApi.listDistricts(Number(selectedState)).then((r) => setDistricts(unwrapResult(r) || [])).catch(() => {});
    }
  }, [selectedState]);

  return (
    <div className="grid lg:grid-cols-2 gap-4">
      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 mb-3">States</h3>
        <div className="grid grid-cols-2 gap-2">
          {states.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedState(s.id)}
              className={`text-left p-3 rounded-lg border text-sm ${selectedState === s.id ? "border-blue-500 bg-blue-50" : "border-slate-200 hover:border-blue-300"}`}
            >
              <div className="font-medium text-slate-800">{s.name}</div>
              <div className="text-xs text-slate-400">{s.code}</div>
            </button>
          ))}
        </div>
      </div>
      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 mb-3">Districts {selectedState ? `- ${states.find((s) => s.id === selectedState)?.name}` : ""}</h3>
        {!selectedState ? (
          <div className="text-sm text-slate-400">Select a state to view districts</div>
        ) : districts.length === 0 ? (
          <div className="text-sm text-slate-400">No districts</div>
        ) : (
          <div className="grid grid-cols-2 gap-2 max-h-[60vh] overflow-y-auto">
            {districts.map((d) => (
              <div key={d.id} className="border border-slate-200 rounded-lg p-3">
                <div className="font-medium text-slate-800 text-sm">{d.name}</div>
                <div className="text-xs text-slate-400">{d.code}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SlaTab() {
  const [rules, setRules] = useState<SLARule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    adminApi.listSLARules()
      .then((r) => setRules(unwrapResult(r) || []))
      .catch((err: unknown) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        setError((err as any)?.message || "Failed to load SLA rules");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const createRule = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await adminApi.createSLARule({
        from_status: String(fd.get("from_status")),
        to_status: String(fd.get("to_status")),
        max_hours: Number(fd.get("max_hours")),
        priority_override: String(fd.get("priority_override")) || undefined,
      });
      toast.success("SLA rule created");
      load();
      e.currentTarget.reset();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Failed to create rule");
    }
  };

  return (
    <div className="grid lg:grid-cols-2 gap-4">
      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 mb-3">SLA Rules</h3>
        {error ? (
          <ErrorState message={error} onRetry={load} />
        ) : loading ? (
          <div className="shimmer h-32 w-full" />
        ) : rules.length === 0 ? (
          <div className="text-sm text-slate-400">No SLA rules defined</div>
        ) : (
          <div className="space-y-2">
            {rules.map((r) => (
              <div key={r.id} className="border border-slate-200 rounded-lg p-3 text-sm">
                <span className="font-mono">{r.from_status}</span> → <span className="font-mono">{r.to_status}</span>
                <span className="ml-3 text-slate-600">Max: {r.max_hours} hrs</span>
                {r.priority_override && <span className="ml-2 text-xs text-slate-400">({r.priority_override})</span>}
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 mb-3">New SLA Rule</h3>
        <form onSubmit={createRule} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label-text">From Status *</label><input name="from_status" className="input-field" required /></div>
            <div><label className="label-text">To Status *</label><input name="to_status" className="input-field" required /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label-text">Max Hours *</label><input type="number" name="max_hours" className="input-field" required min={0} /></div>
            <div><label className="label-text">Priority Override</label><input name="priority_override" className="input-field" /></div>
          </div>
          <button type="submit" className="btn-primary">Create Rule</button>
        </form>
      </div>
    </div>
  );
}

function JurisdictionTab() {
  const [rules, setRules] = useState<JurisdictionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    adminApi.listJurisdictionRules()
      .then((r) => setRules(unwrapResult(r) || []))
      .catch((err: unknown) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        setError((err as any)?.message || "Failed to load rules");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const createRule = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await adminApi.createJurisdictionRule({
        project_type: String(fd.get("project_type")),
        public_category: String(fd.get("public_category")),
        jurisdiction_level: String(fd.get("jurisdiction_level")),
        description: String(fd.get("description")),
      });
      toast.success("Rule created");
      load();
      e.currentTarget.reset();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Failed to create rule");
    }
  };

  return (
    <div className="grid lg:grid-cols-2 gap-4">
      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 mb-3">Jurisdiction Rules</h3>
        {error ? (
          <ErrorState message={error} onRetry={load} />
        ) : loading ? (
          <div className="shimmer h-32 w-full" />
        ) : rules.length === 0 ? (
          <div className="text-sm text-slate-400">No jurisdiction rules defined</div>
        ) : (
          <div className="space-y-2">
            {rules.map((r) => (
              <div key={r.id} className="border border-slate-200 rounded-lg p-3">
                <div className="text-sm"><span className="font-medium text-slate-800">{r.project_type}</span> <span className="text-slate-400">/</span> {r.public_category}</div>
                <div className="text-xs text-slate-500 mt-1">Jurisdiction: {r.jurisdiction_level}</div>
                {r.description && <div className="text-xs text-slate-400 mt-0.5">{r.description}</div>}
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 mb-3">New Jurisdiction Rule</h3>
        <form onSubmit={createRule} className="space-y-3">
          <div><label className="label-text">Project Type *</label><input name="project_type" className="input-field" required /></div>
          <div><label className="label-text">Public Category</label><input name="public_category" className="input-field" /></div>
          <div><label className="label-text">Jurisdiction Level *</label>
            <select name="jurisdiction_level" className="select-field" required>
              <option>LOCAL</option><option>DISTRICT</option><option>STATE</option><option>CENTRAL</option>
            </select>
          </div>
          <div><label className="label-text">Description</label><textarea name="description" className="input-field" rows={2} /></div>
          <button type="submit" className="btn-primary">Create Rule</button>
        </form>
      </div>
    </div>
  );
}
