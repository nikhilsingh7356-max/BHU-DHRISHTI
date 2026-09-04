"use client";

import React, { useEffect, useState, useCallback } from "react";
import toast from "react-hot-toast";
import { notificationApi, unwrapResult } from "@/lib/api";
import { Notification } from "@/lib/types";
import ErrorState from "@/components/ErrorState";

export default function NotificationsPage() {
  const [items, setItems] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await notificationApi.list();
      setItems(unwrapResult(res) || []);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.message || "Failed to load notifications");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const markOneRead = async (id: number) => {
    try {
      await notificationApi.markRead(id);
      load();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Failed to mark read");
    }
  };

  const markAll = async () => {
    try {
      await notificationApi.markAllRead();
      toast.success("All marked as read");
      load();
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toast.error((err as any)?.response?.data?.message || "Failed");
    }
  };

  const unread = items.filter((n) => !n.is_read).length;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-800">Notifications</h2>
        {unread > 0 && (
          <button className="btn-secondary" onClick={markAll}>Mark all as read</button>
        )}
      </div>

      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : loading ? (
        <div className="card p-6"><div className="shimmer h-48 w-full" /></div>
      ) : items.length === 0 ? (
        <div className="card p-8 text-center text-slate-400">No notifications</div>
      ) : (
        <div className="space-y-3">
          {items.map((n) => (
            <button
              key={n.id}
              onClick={() => markOneRead(n.id)}
              className={`card w-full text-left p-4 transition-colors ${!n.is_read ? "border-blue-300 bg-blue-50/50" : ""}`}
            >
              <div className="flex items-start gap-3">
                <span className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${n.is_read ? "bg-slate-300" : "bg-blue-600"}`} />
                <div className="flex-1">
                  <div className="font-medium text-slate-800 text-sm">{n.title}</div>
                  <div className="text-sm text-slate-600 mt-0.5">{n.message}</div>
                  <div className="text-xs text-slate-400 mt-1">{new Date(n.created_at).toLocaleString()}</div>
                </div>
                {!n.is_read && (
                  <span className="text-xs text-blue-600 shrink-0">Unread</span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
