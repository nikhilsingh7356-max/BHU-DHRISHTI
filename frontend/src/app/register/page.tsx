"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import toast from "react-hot-toast";
import { authApi, adminApi, unwrapResult } from "@/lib/api";
import { Role } from "@/lib/types";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const [form, setForm] = useState({ email: "", password: "", full_name: "", role_id: "" });
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { user } = useAuth();

  useEffect(() => {
    if (user) router.replace("/dashboard");
    adminApi
      .listRoles()
      .then((res) => setRoles(unwrapResult(res)))
      .catch(() => {});
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.register({
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        role_id: Number(form.role_id),
      });
      toast.success("Account created. You can now sign in.");
      router.replace("/login");
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <div className="government-header py-8 text-center">
        <div className="text-3xl font-bold text-white">Bhu-Drishti</div>
        <div className="text-blue-200 text-sm">Register an account</div>
      </div>
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="card p-8">
            <h2 className="text-xl font-semibold text-slate-800 mb-6">Create Account</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="label-text">Full Name *</label>
                <input className="input-field" required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
              </div>
              <div>
                <label className="label-text">Email *</label>
                <input type="email" className="input-field" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </div>
              <div>
                <label className="label-text">Password *</label>
                <input type="password" className="input-field" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
              </div>
              <div>
                <label className="label-text">Role *</label>
                <select className="select-field" required value={form.role_id} onChange={(e) => setForm({ ...form, role_id: e.target.value })}>
                  <option value="">Select role</option>
                  {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
                </select>
              </div>
              <button type="submit" className="btn-primary w-full !py-2.5" disabled={loading}>
                {loading ? "Registering..." : "Register"}
              </button>
            </form>
            <div className="text-center mt-4 text-sm">
              <span className="text-slate-500">Already have an account? </span>
              <Link href="/login" className="text-blue-600 hover:text-blue-800 font-medium">Sign in</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
