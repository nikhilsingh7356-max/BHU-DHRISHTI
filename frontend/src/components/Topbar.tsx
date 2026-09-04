"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/auth";
import { notificationApi, unwrapResult } from "@/lib/api";
import { Notification } from "@/lib/types";

export default function Topbar({ title }: { title?: string }) {
  const { user, logout } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [notifOpen, setNotifOpen] = useState(false);
  const [unread, setUnread] = useState(0);

  const loadNotifications = useCallback(async () => {
    try {
      const res = await notificationApi.list();
      const data = unwrapResult(res);
      setNotifications(data || []);
      setUnread((data || []).filter((n) => !n.is_read).length);
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 60000);
    return () => clearInterval(interval);
  }, [loadNotifications]);

  const markAllRead = async () => {
    try {
      await notificationApi.markAllRead();
      await loadNotifications();
    } catch {
      // silent
    }
  };

  const markOneRead = async (id: number) => {
    try {
      await notificationApi.markRead(id);
      await loadNotifications();
    } catch {
      // silent
    }
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
      <div className="flex items-center justify-between px-4 lg:px-6 py-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-800">{title || "Bhu-Drishti"}</h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <button
              className="relative p-2 text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-100"
              onClick={() => setNotifOpen(!notifOpen)}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {unread > 0 && (
                <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-0.5 text-xs font-bold text-white bg-red-500 rounded-full">
                  {unread}
                </span>
              )}
            </button>
            {notifOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-slate-200 z-50">
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                  <span className="text-sm font-semibold text-slate-700">Notifications</span>
                  {unread > 0 && (
                    <button className="text-xs text-blue-600 hover:text-blue-800" onClick={markAllRead}>
                      Mark all read
                    </button>
                  )}
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="p-4 text-sm text-slate-400 text-center">No notifications</div>
                  ) : (
                    notifications.slice(0, 10).map((n) => (
                      <button
                        key={n.id}
                        className={`w-full text-left px-4 py-3 hover:bg-slate-50 border-b border-slate-50 ${
                          !n.is_read ? "bg-blue-50/50" : ""
                        }`}
                        onClick={() => markOneRead(n.id)}
                      >
                        <div className="text-sm font-medium text-slate-700">{n.title}</div>
                        <div className="text-xs text-slate-500 mt-0.5 line-clamp-2">{n.message}</div>
                        <div className="text-xs text-slate-400 mt-1">
                          {new Date(n.created_at).toLocaleString()}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-medium text-slate-700">{user?.full_name}</div>
              <div className="text-xs text-slate-400">{user?.role?.name}</div>
            </div>
            <button
              className="p-2 text-slate-500 hover:text-red-600 rounded-lg hover:bg-red-50"
              onClick={logout}
              title="Logout"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
