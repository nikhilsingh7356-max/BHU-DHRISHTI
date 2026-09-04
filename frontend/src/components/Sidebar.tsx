"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useState } from "react";

const officerRoles = [
  "SUPER_ADMIN",
  "CENTRAL_AUTHORITY",
  "STATE_AUTHORITY",
  "DISTRICT_ADMIN",
  "LAND_ACQUIRING_OFFICER",
  "SURVEYOR_GIS_OFFICER",
  "VERIFICATION_OFFICER",
  "COMPENSATION_OFFICER",
  "RR_OFFICER",
  "REVIEWER",
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isAdmin = user?.role?.name === "SUPER_ADMIN" || user?.role?.name === "CENTRAL_AUTHORITY";
  const isOfficer = user?.role?.name ? officerRoles.includes(user.role.name) : false;
  const isAuditor = user?.role?.name === "AUDITOR" || user?.role?.name === "REVIEWER" || isAdmin;
  const isCompOfficer =
    user?.role?.name === "COMPENSATION_OFFICER" ||
    user?.role?.name === "DISTRICT_ADMIN" ||
    isAdmin;
  const isRR =
    user?.role?.name === "RR_OFFICER" || user?.role?.name === "DISTRICT_ADMIN" || isAdmin;

  const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: "\u25A0", show: true },
    { href: "/projects", label: "Projects", icon: "\u25A0", show: true },
    { href: "/parcels", label: "Parcels", icon: "\u25A0", show: true },
    { href: "/gis", label: "GIS / Map", icon: "\u25A0", show: true },
    { href: "/documents", label: "Documents", icon: "\u25A0", show: true },
    { href: "/workflow", label: "Workflow", icon: "\u25A0", show: isOfficer || isAdmin },
    { href: "/compensation", label: "Compensation", icon: "\u25A0", show: isCompOfficer },
    { href: "/rr", label: "R&R", icon: "\u25A0", show: isRR },
    { href: "/objections", label: "Objections", icon: "\u25A0", show: isOfficer || isAdmin },
    { href: "/notifications", label: "Notifications", icon: "\u25A0", show: true },
    { href: "/audit", label: "Audit Trail", icon: "\u25A0", show: isAuditor },
    { href: "/reports", label: "Reports", icon: "\u25A0", show: true },
    { href: "/command-center", label: "Command Center", icon: "\u25A0", show: isOfficer || isAdmin },
    { href: "/analytics", label: "Analytics", icon: "\u25A0", show: isOfficer || isAdmin },
    { href: "/conflicts", label: "Conflicts", icon: "\u25A0", show: isOfficer || isAdmin },
    { href: "/escalations", label: "Escalations", icon: "\u25A0", show: isOfficer || isAdmin },
    { href: "/integrations", label: "Integrations", icon: "\u25A0", show: isAuditor },
    { href: "/admin", label: "Admin", icon: "\u25A0", show: isAdmin },
    { href: "/search", label: "Search", icon: "\u25A0", show: true },
  ].filter((item) => item.show);

  const nav = (
    <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
      {navItems.map((item) => {
        const active = pathname?.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => setMobileOpen(false)}
            className={`sidebar-link ${active ? "active" : ""}`}
          >
            <span className="text-base leading-none">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );

  const sidebarContent = (
    <>
      <div className="p-4 border-b border-slate-700">
        <div className="text-lg font-bold text-white">Bhu-Drishti</div>
        <div className="text-xs text-slate-400 mt-1">National Land Acquisition</div>
      </div>
      {nav}
      <div className="p-4 border-t border-slate-700">
        <div className="flex items-center justify-between">
          <div className="min-w-0">
            <div className="text-sm font-medium text-white truncate">{user?.full_name}</div>
            <div className="text-xs text-slate-400 truncate">{user?.role?.name}</div>
          </div>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-64 bg-slate-900 text-slate-300 shrink-0 min-h-screen sticky top-0">
        {sidebarContent}
      </aside>

      {/* Mobile */}
      <button
        className="lg:hidden fixed bottom-4 right-4 z-50 bg-blue-600 text-white p-3 rounded-full shadow-lg"
        onClick={() => setMobileOpen(!mobileOpen)}
      >
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          {mobileOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40 bg-black/50" onClick={() => setMobileOpen(false)}>
          <div
            className="absolute left-0 top-0 bottom-0 w-64 bg-slate-900 flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
