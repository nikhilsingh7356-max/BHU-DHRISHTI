"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { authApi, unwrapResult } from "./api";
import { User } from "./types";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => {},
  logout: () => {},
  hasPermission: () => false,
  hasRole: () => false,
  refreshUser: async () => {},
});

function normalizeUser(u: Partial<User>): User {
  const perms =
    (u.role?.permissions?.map((p) => p.name) as string[]) || u.permissions || [];
  return {
    ...(u as User),
    permissions: perms,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setUser(null);
        return;
      }
      const res = await authApi.me();
      setUser(normalizeUser(unwrapResult(res)));
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setLoading(false));
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    const res = await authApi.login(email, password);
    const data = unwrapResult(res);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    setUser(normalizeUser(data.user));
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    window.location.href = "/login";
  };

  const hasPermission = (permission: string) => {
    if (!user) return false;
    if (user.role?.name === "SUPER_ADMIN") return true;
    return user.permissions?.some((p) => p === permission || p === `*`) || false;
  };

  const hasRole = (role: string) => {
    if (!user) return false;
    return user.role?.name === role;
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, hasPermission, hasRole, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
