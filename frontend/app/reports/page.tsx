"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FileSpreadsheet,
  FileText,
  Link as LinkIcon,
  Download,
  Users,
  ChevronRight,
  Filter,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function ReportsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [reports, setReports] = useState<any[]>([]);
  const [filter, setFilter] = useState<"all" | "documents" | "urls" | "shared">("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchReports() {
      try {
        const u = await api.getMe();
        setUser(u);
        const data = await api.getReports();
        setReports(data || []);
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }
    fetchReports();
  }, [router]);

  const filteredReports = reports.filter((r) => {
    if (filter === "documents") return r.reportType === "document_analysis" && !r.isSharedWithMe;
    if (filter === "urls") return r.reportType === "url_check";
    if (filter === "shared") return r.isSharedWithMe;
    return true;
  });

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar user={user} />

      <main className="flex-1 mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Truth & Clarity Reports Directory</h1>
          <p className="text-xs text-slate-500">
            View, review evidence, export to PDF/JSON, or share findings from your document analyses and website scans.
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 border-b border-slate-200 pb-2">
          <button
            onClick={() => setFilter("all")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
              filter === "all" ? "bg-teal-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            All Reports ({reports.length})
          </button>
          <button
            onClick={() => setFilter("documents")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
              filter === "documents" ? "bg-teal-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            My Documents ({reports.filter((r) => r.reportType === "document_analysis" && !r.isSharedWithMe).length})
          </button>
          <button
            onClick={() => setFilter("urls")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
              filter === "urls" ? "bg-teal-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            URL Scans ({reports.filter((r) => r.reportType === "url_check").length})
          </button>
          <button
            onClick={() => setFilter("shared")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
              filter === "shared" ? "bg-teal-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            Family Shared ({reports.filter((r) => r.isSharedWithMe).length})
          </button>
        </div>

        {/* Reports Table */}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          {loading ? (
            <div className="py-12 text-center text-xs text-slate-400">Loading reports...</div>
          ) : filteredReports.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500 space-y-2">
              <p>No reports found matching selected category.</p>
              <Link href="/analyze" className="text-teal-600 font-semibold hover:underline">
                Upload a document to generate your first report
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {filteredReports.map((item) => {
                const isDoc = item.reportType === "document_analysis";
                const targetHref = isDoc ? `/analyze/${item.id}` : `/check-link?id=${item.id}`;

                return (
                  <div
                    key={item.id}
                    className="p-4 flex flex-wrap items-center justify-between gap-4 hover:bg-slate-50/50 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <div className="rounded-lg bg-teal-50 p-2 text-teal-700 mt-0.5">
                        {isDoc ? <FileText className="h-4 w-4" /> : <LinkIcon className="h-4 w-4" />}
                      </div>
                      <div className="space-y-0.5">
                        <Link
                          href={targetHref}
                          className="text-xs font-bold text-slate-900 hover:text-teal-600 transition-colors"
                        >
                          {item.title}
                        </Link>
                        <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                          <span>Created {formatDate(item.createdAt)}</span>
                          <span>•</span>
                          <span className="capitalize">{item.reportType.replace(/_/g, " ")}</span>
                          {item.isSharedWithMe && (
                            <>
                              <span>•</span>
                              <span className="rounded bg-teal-100 px-1.5 py-0.2 text-[10px] font-semibold text-teal-800">
                                Shared by {item.ownerDisplayName || "Family Member"}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <a
                        href={`/api/v1/reports/${item.reportType}/${item.id}/export?format=pdf`}
                        target="_blank"
                        rel="noreferrer"
                        title="Download PDF"
                        className="rounded-lg border border-slate-200 p-1.5 text-slate-500 hover:bg-slate-100 transition-colors"
                      >
                        <Download className="h-4 w-4" />
                      </a>

                      <Link
                        href={targetHref}
                        className="flex items-center gap-1 rounded-lg bg-teal-50 px-3 py-1.5 text-xs font-semibold text-teal-700 hover:bg-teal-100 transition-colors"
                      >
                        Open <ChevronRight className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
