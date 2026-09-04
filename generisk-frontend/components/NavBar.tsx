"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { SunIcon, MoonIcon } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/lib/theme-context";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/search", label: "Search" },
  { href: "/history", label: "History" },
  { href: "/accuracy", label: "Model accuracy" },
  { href: "/settings", label: "Settings" },
];

export function NavBar() {
  const pathname = usePathname();
  const { isLoggedIn, initials } = useAuth();
  const { theme, toggleTheme } = useTheme();

  if (pathname === "/login" || !isLoggedIn) return null;

  return (
    <nav className="flex items-center justify-between px-10 py-5 border-b border-ink/10 bg-paper">
      <div className="flex items-center gap-2 font-mono font-bold text-sm tracking-wide text-ink">
        <span className="w-2 h-2 rounded-full bg-teal" />
        GeneRisk
      </div>

      <div className="flex items-center gap-7">
        {links.map((link) => {
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`text-sm font-medium transition-colors ${
                isActive ? "text-teal" : "text-ink-soft hover:text-ink"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5 text-xs font-mono text-teal border border-teal/20 bg-teal/10 px-2.5 py-1 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-teal" />
          API live
        </div>

        <button
          onClick={toggleTheme}
          className="w-8 h-8 rounded-full border border-line flex items-center justify-center text-ink-soft hover:text-ink hover:bg-paper transition-colors"
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? (
            <SunIcon className="w-4 h-4" />
          ) : (
            <MoonIcon className="w-4 h-4" />
          )}
        </button>

        <Link
          href="/settings"
          className="w-8 h-8 rounded-full bg-ink text-paper font-mono text-xs font-semibold flex items-center justify-center cursor-pointer transition-opacity hover:opacity-80"
          title="Settings"
        >
          {initials}
        </Link>
      </div>
    </nav>
  );
}