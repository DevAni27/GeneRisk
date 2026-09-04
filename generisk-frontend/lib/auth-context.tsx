"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

interface AuthState {
  isLoggedIn: boolean;
  workerName: string;
  workerId: string;
  facility: string;
  state: string;
}

interface AuthContextValue extends AuthState {
  isLoading: boolean;
  initials: string;
  login: (workerName: string, workerId: string, facility?: string, state?: string) => void;
  logout: () => void;
  updateProfile: (updates: Partial<Pick<AuthState, "workerName" | "facility" | "state">>) => void;
}

const STORAGE_KEY = "generisk_auth";

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    isLoggedIn: false,
    workerName: "",
    workerId: "",
    facility: "",
    state: "",
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setState(JSON.parse(stored));
    } catch {
      // ignore corrupt storage
    }
    setIsLoading(false);
  }, []);

  const login = (workerName: string, workerId: string, facility = "", stateName = "") => {
    const next: AuthState = { isLoggedIn: true, workerName, workerId, facility, state: stateName };
    setState(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  };

  const logout = () => {
    const next: AuthState = { isLoggedIn: false, workerName: "", workerId: "", facility: "", state: "" };
    setState(next);
    localStorage.removeItem(STORAGE_KEY);
  };

  const updateProfile = (updates: Partial<Pick<AuthState, "workerName" | "facility" | "state">>) => {
    setState((current) => {
      const next = { ...current, ...updates };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const initials =
    state.workerName
      .trim()
      .split(/\s+/)
      .map((part) => part[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() || "?";

  return (
    <AuthContext.Provider
      value={{ ...state, isLoading, initials, login, logout, updateProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}