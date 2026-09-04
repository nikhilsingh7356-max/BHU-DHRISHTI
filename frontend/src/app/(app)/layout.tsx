"use client";

import React from "react";
import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";
import ProtectedRoute from "@/components/ProtectedRoute";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <Topbar />
          <main className="flex-1 p-4 lg:p-6 overflow-y-auto">{children}</main>
        </div>
      </div>
    </ProtectedRoute>
  );
}
