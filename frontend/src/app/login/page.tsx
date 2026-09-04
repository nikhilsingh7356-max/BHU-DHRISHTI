"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { useAuth } from "@/lib/auth";

const demoAccounts = [
  { label: "Super Admin", email: "superadmin@bhudrishti.gov.in", password: "Super@123" },
  { label: "Central Admin", email: "admin@bhudrishti.gov.in", password: "Admin@123" },
  { label: "State Authority", email: "state@bhudrishti.gov.in", password: "State@123" },
  { label: "District Admin", email: "district@bhudrishti.gov.in", password: "District@123" },
  { label: "Land Acquiring Officer", email: "lao@bhudrishti.gov.in", password: "Lao@123" },
  { label: "Project Sponsor", email: "sponsor@bhudrishti.gov.in", password: "Sponsor@123" },
  { label: "GIS Officer", email: "gis@bhudrishti.gov.in", password: "Gis@123" },
  { label: "Verification Officer", email: "verification@bhudrishti.gov.in", password: "Verify@123" },
  { label: "Compensation Officer", email: "compensation@bhudrishti.gov.in", password: "Comp@123" },
  { label: "R&R Officer", email: "rr@bhudrishti.gov.in", password: "Rr@123" },
  { label: "Reviewer", email: "reviewer@bhudrishti.gov.in", password: "Review@123" },
  { label: "Auditor", email: "auditor@bhudrishti.gov.in", password: "Audit@123" },
  { label: "Viewer", email: "viewer@bhudrishti.gov.in", password: "Viewer@123" },
];

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { login, user } = useAuth();

  useEffect(() => {
    if (user) router.replace("/dashboard");
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email.trim(), password);
      toast.success("Login successful");
      router.replace("/dashboard");
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const msg = (err as any)?.response?.data?.message || "Login failed. Check credentials.";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const quickFill = (email: string, password: string) => {
    setEmail(email);
    setPassword(password);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <div className="government-header py-8 text-center">
        <div className="flex items-center justify-center gap-3 mb-2">
          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6M9 10h.01M15 10h.01M12 10h.01" />
          </svg>
          <span className="text-3xl font-bold text-white">Bhu-Drishti</span>
        </div>
        <div className="text-blue-200 text-sm">
          National Land Acquisition & Management System
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="card p-8">
            <h2 className="text-xl font-semibold text-slate-800 mb-1">Sign in to your account</h2>
            <p className="text-sm text-slate-500 mb-6">Authorized government personnel only</p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="label-text">Email Address</label>
                <input
                  type="email"
                  className="input-field"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@bhudrishti.gov.in"
                />
              </div>
              <div>
                <label className="label-text">Password</label>
                <input
                  type="password"
                  className="input-field"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>
              <button type="submit" className="btn-primary w-full !py-2.5" disabled={loading}>
                {loading ? "Signing in..." : "Sign In"}
              </button>
            </form>

            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-200"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="bg-white px-4 text-slate-400">Demo Accounts</span>
                </div>
              </div>
              <select
                className="select-field mt-4"
                defaultValue=""
                onChange={(e) => {
                  const acct = demoAccounts.find((d) => d.email === e.target.value);
                  if (acct) quickFill(acct.email, acct.password);
                }}
              >
                <option value="" disabled>Select a demo role...</option>
                {demoAccounts.map((d) => (
                  <option key={d.email} value={d.email}>{d.label}</option>
                ))}
              </select>
              <button
                type="button"
                className="btn-secondary w-full mt-2"
                onClick={() => {
                  if (email && password) handleSubmit({ preventDefault: () => {} } as React.FormEvent);
                }}
              >
                Quick Sign In (fill above)
              </button>
            </div>
          </div>

          <div className="text-center mt-4 text-xs text-slate-400">
            Trouble signing in? Contact your system administrator.
          </div>
        </div>
      </div>
    </div>
  );
}
