"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { isLoggedIn, isLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isLoginPage = pathname === "/login";

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn && !isLoginPage) router.replace("/login");
    if (isLoggedIn && isLoginPage) router.replace("/");
  }, [isLoading, isLoggedIn, isLoginPage, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center font-mono text-sm text-ink-soft">
        Loading…
      </div>
    );
  }

  if (!isLoggedIn && !isLoginPage) return null;

  return <>{children}</>;
}