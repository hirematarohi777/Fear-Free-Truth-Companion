"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FileText,
  Link as LinkIcon,
  Calculator,
  Users,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ExternalLink,
  ChevronRight,
  PlusCircle,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import ScrollRevealText from "@/components/animations/ScrollRevealText";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

// 1. IMPORT THE ANIMATION COMPONENT HERE
import { ContainerTextFlip } from "@/components/ui/container-text-flip";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [urlChecks, setUrlChecks] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const u = await api.getMe();
        setUser(u);

        // Fetch recent documents, url checks, reports
        const [docs, urls, reps] = await Promise.allSettled([
          api.getDocuments(),
          api.getUrlChecks(),
          api.getReports(),
        ]);

        if (docs.status === "fulfilled") setDocuments(docs.value || []);
        if (urls.status === "fulfilled") setUrlChecks(urls.value || []);
        if (reps.status === "fulfilled") setReports(reps.value || []);
      } catch (err) {
        // Redirect to login if unauthenticated
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [router]);

  const handleLogout = async () => {
    await api.logout();
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3 text-slate-500 text-xs">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
          <span>Verifying secure session...</span>
        </div>
      </div>
    );
  }

  const sharedWithMe = reports.filter((r) => r.isSharedWithMe);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar user={user} onLogout={handleLogout} />

      <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Welcome & Primary Actions Banner */}
        <div className="rounded-2xl bg-gradient-to-r from-teal-800 via-teal-700 to-teal-900 p-6 sm:p-8 text-white shadow-sm">
          <div className="max-w-3xl space-y-4">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-600/60 px-3 py-0.5 text-xs font-medium text-teal-100 backdrop-blur-xs">
              <ShieldCheck className="h-3.5 w-3.5" />
              Indian Home Loan Clarity & Family Consensus
            </span>
            
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Welcome, {user?.displayName || "Borrower"}
            </h1>

            {/* 2. ADDED THE CONTAINER TEXT FLIP HERE AS A DYNAMIC HEADLINE */}
           <ContainerTextFlip
  words={["Fear-Free", "Companion", "Finance", "Truth"]}
  className="text-3xl sm:text-4xl md:text-5xl font-bold text-white"
  duration={2500}
/>

            <p className="text-sm text-teal-100/90 leading-relaxed max-w-xl">
              Analyze your home loan offer letter, uncover overlooked or conditional charges, verify online loan links, and selectively involve trusted family members before signing.
            </p>
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/analyze"
              className="flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-teal-900 shadow-sm hover:bg-teal-50 transition-colors"
            >
              <FileText className="h-4 w-4 text-teal-700" />
              Upload Loan Document
            </Link>

            <Link
              href="/check-link"
              className="flex items-center gap-2 rounded-xl bg-teal-600/80 hover:bg-teal-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm transition-colors border border-teal-500/50"
            >
              <LinkIcon className="h-4 w-4 text-teal-200" />
              Check Loan Link
            </Link>

            <Link
              href="/calculator"
              className="flex items-center gap-2 rounded-xl bg-teal-900/60 hover:bg-teal-900 px-4 py-2.5 text-xs font-semibold text-teal-100 transition-colors border border-teal-700/50"
            >
              <Calculator className="h-4 w-4 text-teal-300" />
              Repayment Calculator
            </Link>
          </div>
        </div>

        <ScrollRevealText />

        {/* Dashboard Grid (Rest of your code remains exactly the same) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Columns: Recent Analyses & Link Checks */}
          <div className="lg:col-span-2 space-y-6">
            {/* Recent Document Analyses */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <div className="rounded-lg bg-teal-50 p-2 text-teal-700">
                    <FileText className="h-4 w-4" />
                  </div>
                  <h2 className="text-sm font-semibold text-slate-900">Recent Document Analyses</h2>
                </div>
                <Link
                  href="/analyze"
                  className="flex items-center gap-1 text-xs font-medium text-teal-600 hover:text-teal-700"
                >
                  <PlusCircle className="h-3.5 w-3.5" />
                  Analyze New
                </Link>
              </div>

              {documents.length === 0 ? (
                <div className="py-8 text-center text-slate-400 text-xs space-y-2">
                  <p>No loan documents analyzed yet.</p>
                  <Link
                    href="/analyze"
                    className="inline-flex items-center gap-1 font-medium text-teal-600 hover:underline"
                  >
                    Upload your first sanction letter <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {documents.slice(0, 4).map((doc) => (
                    <div key={doc.id} className="py-3 flex items-center justify-between hover:bg-slate-50/50 px-2 rounded-lg transition-colors">
                      <div className="space-y-0.5">
                        <div className="text-xs font-semibold text-slate-900 flex items-center gap-2">
                          {doc.originalFilename}
                          <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600 font-mono">
                            {doc.detectedMimeType?.includes("pdf") ? "PDF" : "DOCX"}
                          </span>
                        </div>
                        <span className="text-[11px] text-slate-500">
                          Uploaded {formatDate(doc.createdAt)} • {(doc.sizeBytes / 1024).toFixed(0)} KB
                        </span>
                      </div>

                      {doc.latestAnalysisId ? (
                        <Link
                          href={`/analyze/${doc.latestAnalysisId}`}
                          className="flex items-center gap-1 rounded-lg bg-teal-50 px-3 py-1 text-xs font-medium text-teal-700 hover:bg-teal-100 transition-colors"
                        >
                          View Report <ChevronRight className="h-3.5 w-3.5" />
                        </Link>
                      ) : (
                        <span className="text-xs text-amber-600 flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Processing
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent URL Checks */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <div className="rounded-lg bg-teal-50 p-2 text-teal-700">
                    <LinkIcon className="h-4 w-4" />
                  </div>
                  <h2 className="text-sm font-semibold text-slate-900">Recent Loan Link Checks</h2>
                </div>
                <Link
                  href="/check-link"
                  className="flex items-center gap-1 text-xs font-medium text-teal-600 hover:text-teal-700"
                >
                  <PlusCircle className="h-3.5 w-3.5" />
                  Check Link
                </Link>
              </div>

              {urlChecks.length === 0 ? (
                <div className="py-6 text-center text-slate-400 text-xs">
                  No URLs checked yet. Check any online loan website for SSRF-safe risk signals.
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {urlChecks.slice(0, 4).map((chk) => (
                    <div key={chk.id} className="py-3 flex items-center justify-between hover:bg-slate-50/50 px-2 rounded-lg transition-colors">
                      <div className="space-y-0.5 max-w-[70%]">
                        <span className="text-xs font-mono font-medium text-slate-900 truncate block">
                          {chk.submittedUrl}
                        </span>
                        <div className="flex items-center gap-2 text-[11px] text-slate-500">
                          <span>{formatDate(chk.createdAt)}</span>
                          {chk.claimedEntity && <span>• Claimed: {chk.claimedEntity}</span>}
                        </div>
                      </div>

                      <Link
                        href={`/check-link?id=${chk.id}`}
                        className="flex items-center gap-1 rounded-lg bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-200 transition-colors shrink-0"
                      >
                        Result <ChevronRight className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Family Circle & Attention Flags */}
          <div className="space-y-6">
            {/* Shared Family Reports */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <div className="rounded-lg bg-teal-50 p-2 text-teal-700">
                    <Users className="h-4 w-4" />
                  </div>
                  <h2 className="text-sm font-semibold text-slate-900">Family Circle</h2>
                </div>
                <Link
                  href="/family"
                  className="text-xs font-medium text-teal-600 hover:text-teal-700"
                >
                  Manage
                </Link>
              </div>

              {sharedWithMe.length === 0 ? (
                <div className="rounded-lg bg-slate-50 p-4 text-center space-y-2">
                  <p className="text-xs text-slate-600 font-medium">No family reports shared with you yet.</p>
                  <p className="text-[11px] text-slate-400">
                    When a family member invites you to view their loan assessment, their report will appear here.
                  </p>
                  <Link
                    href="/family"
                    className="inline-block rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-teal-700 border border-slate-200 shadow-xs hover:bg-slate-50"
                  >
                    Invite a Family Member
                  </Link>
                </div>
              ) : (
                <div className="space-y-2">
                  {sharedWithMe.map((item) => (
                    <Link
                      key={item.id}
                      href={`/analyze/${item.id}`}
                      className="block rounded-lg bg-slate-50 p-3 border border-slate-200/80 hover:border-teal-500 transition-colors"
                    >
                      <div className="text-xs font-semibold text-slate-900 flex items-center justify-between">
                        <span>{item.title}</span>
                        <span className="rounded bg-teal-100 text-teal-800 px-1.5 py-0.2 text-[10px]">
                          Shared View
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-500 block mt-1">
                        Shared by {item.ownerDisplayName || "Family Member"}
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {/* Core Values & Truth Commitments Card */}
            <div className="rounded-xl border border-teal-100 bg-teal-50/50 p-5 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-teal-900 flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-teal-600" />
                Our Truth Commitments
              </h3>
              <ul className="text-xs text-teal-950/80 space-y-2">
                <li className="flex items-start gap-1.5">
                  <span className="text-teal-600 font-bold">•</span>
                  <span><b>Zero Sales Pressure:</b> We do not sell mortgages or earn commissions.</span>
                </li>
                <li className="flex items-start gap-1.5">
                  <span className="text-teal-600 font-bold">•</span>
                  <span><b>Private & Local:</b> Uploaded files are processed using free, local Ollama models. No cloud AI leakage.</span>
                </li>
                <li className="flex items-start gap-1.5">
                  <span className="text-teal-600 font-bold">•</span>
                  <span><b>Consent-First Sharing:</b> Financial figures are redacted by default unless explicitly permitted.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
