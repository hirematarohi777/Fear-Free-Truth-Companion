"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, FileText, Link as LinkIcon, Calculator, Users, FileSpreadsheet, Lock, Menu, X, LogOut, UserCheck, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface NavbarProps { user?: { displayName: string; email: string } | null; onLogout?: () => void; }

export function Navbar({ user, onLogout }: NavbarProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const navItems = [
    { href: "/", label: "Overview", icon: ShieldCheck },
    { href: "/analyze", label: "Analyze", icon: FileText },
    { href: "/check-link", label: "Check a link", icon: LinkIcon },
    { href: "/calculator", label: "Calculator", icon: Calculator },
    { href: "/family", label: "Family Circle", icon: Users },
    { href: "/reports", label: "Reports", icon: FileSpreadsheet },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
      <div className="mx-auto flex min-h-[4.5rem] max-w-[1440px] items-center justify-between gap-6 px-4 sm:px-6 lg:px-10">
        <Link href="/" className="flex shrink-0 items-center gap-3" aria-label="Fear-Free Truth Companion home">
          <span className="flex size-10 items-center justify-center rounded-xl bg-slate-950 text-white shadow-lg shadow-slate-950/10"><ShieldCheck className="size-5" /></span>
          <span className="hidden sm:block"><span className="block text-sm font-bold tracking-[-0.02em] text-slate-950">Fear-Free</span><span className="block text-[11px] font-medium text-slate-500">Truth Companion</span></span>
        </Link>

        <nav className="hidden xl:flex items-center gap-1" aria-label="Primary navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return <Link key={item.href} href={item.href} className={cn("group flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium transition-colors", active ? "bg-teal-50 text-teal-800" : "text-slate-500 hover:bg-slate-50 hover:text-slate-900")}><Icon className={cn("size-4", active ? "text-teal-700" : "text-slate-400 group-hover:text-slate-600")} />{item.label}</Link>;
          })}
        </nav>

        <div className="flex items-center gap-2">
          <Link href="/privacy" className="hidden md:flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-slate-500 hover:bg-slate-50 hover:text-slate-900"><Lock className="size-3.5" />Privacy</Link>
          {user ? <div className="hidden sm:flex items-center gap-2 border-l border-slate-200 pl-3"><span className="flex items-center gap-2 rounded-full bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700"><span className="flex size-6 items-center justify-center rounded-full bg-teal-100 text-[10px] font-bold text-teal-800">{user.displayName?.slice(0, 1).toUpperCase()}</span>{user.displayName}<ChevronDown className="size-3 text-slate-400" /></span>{onLogout && <button onClick={onLogout} title="Log out" className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"><LogOut className="size-4" /></button>}</div> : <Link href="/login" className="hidden sm:inline-flex rounded-lg bg-slate-950 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-slate-800">Sign in</Link>}
          <button className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 xl:hidden" onClick={() => setMobileOpen(!mobileOpen)} aria-label={mobileOpen ? "Close menu" : "Open menu"} aria-expanded={mobileOpen}>{mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}</button>
        </div>
      </div>
      {mobileOpen && <div className="border-t border-slate-100 bg-white px-4 py-3 xl:hidden"><nav className="mx-auto flex max-w-[1440px] flex-col gap-1" aria-label="Mobile navigation">{navItems.map((item) => { const Icon = item.icon; const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href)); return <Link key={item.href} href={item.href} onClick={() => setMobileOpen(false)} className={cn("flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium", active ? "bg-teal-50 text-teal-800" : "text-slate-600 hover:bg-slate-50")}><Icon className="size-4" />{item.label}</Link>; })}{user && onLogout && <button onClick={() => { setMobileOpen(false); onLogout(); }} className="mt-2 flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium text-rose-700 hover:bg-rose-50"><LogOut className="size-4" />Sign out</button>}</nav></div>}
    </header>
  );
}
