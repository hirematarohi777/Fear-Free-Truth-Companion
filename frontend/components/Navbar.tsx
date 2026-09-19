"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ShieldCheck,
  FileText,
  Link as LinkIcon,
  Calculator,
  Users,
  FileSpreadsheet,
  Lock,
  Menu,
  X,
  LogOut,
  UserCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavbarProps {
  user?: { displayName: string; email: string } | null;
  onLogout?: () => void;
}

export function Navbar({ user, onLogout }: NavbarProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = [
    { href: "/", label: "Dashboard", icon: ShieldCheck },
    { href: "/analyze", label: "Analyze Document", icon: FileText },
    { href: "/check-link", label: "Check Loan Link", icon: LinkIcon },
    { href: "/calculator", label: "Loan Calculator", icon: Calculator },
    { href: "/family", label: "Family Circle", icon: Users },
    { href: "/reports", label: "Reports", icon: FileSpreadsheet },
    { href: "/privacy", label: "Privacy & Settings", icon: Lock },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2.5 transition-opacity hover:opacity-90">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-600 text-white shadow-sm">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="text-base font-semibold leading-tight text-slate-900">
              Fear-Free Truth Companion
            </div>
            <div className="text-[11px] text-slate-500 hidden sm:block">
              Understand your loan. Involve your family. Decide with confidence.
            </div>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                  active
                    ? "bg-teal-50 text-teal-700 font-semibold"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                )}
              >
                <Icon className={cn("h-4 w-4", active ? "text-teal-600" : "text-slate-400")} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* User Info & Actions */}
        <div className="hidden sm:flex items-center gap-3">
          {user ? (
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 text-xs font-medium text-slate-700 bg-slate-100 px-2.5 py-1 rounded-full">
                <UserCheck className="h-3.5 w-3.5 text-teal-600" />
                {user.displayName}
              </span>
              {onLogout && (
                <button
                  onClick={onLogout}
                  title="Log out"
                  className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              )}
            </div>
          ) : (
            <Link
              href="/login"
              className="rounded-md bg-teal-600 px-3.5 py-1.5 text-xs font-medium text-white hover:bg-teal-700 transition-colors shadow-sm"
            >
              Sign In
            </Link>
          )}
        </div>

        {/* Mobile menu trigger */}
        <div className="flex lg:hidden">
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="rounded-md p-2 text-slate-600 hover:bg-slate-100"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="lg:hidden border-b border-slate-200 bg-white px-4 pt-2 pb-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
                  active
                    ? "bg-teal-50 text-teal-700 font-semibold"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
          {user && onLogout && (
            <button
              onClick={() => {
                setMobileOpen(false);
                onLogout();
              }}
              className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
            >
              <LogOut className="h-4 w-4" />
              Sign Out ({user.displayName})
            </button>
          )}
        </div>
      )}
    </header>
  );
}
