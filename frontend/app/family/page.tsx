"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Users,
  ShieldCheck,
  Lock,
  Trash2,
  Share2,
  AlertCircle,
  Clock,
  ExternalLink,
  CheckCircle2,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { ShareDialog } from "@/components/ShareDialog";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import Link from "next/link";

export default function FamilyPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [sharesByMe, setSharesByMe] = useState<any[]>([]);
  const [sharesWithMe, setSharesWithMe] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState<any | null>(null);

  const loadShares = async () => {
    try {
      const u = await api.getMe();
      setUser(u);
      const data = await api.getShares();
      setSharesByMe(data.sharedByMe || []);
      setSharesWithMe(data.sharedWithMe || []);
      const reportData = await api.getReports();
      setReports((reportData || []).filter((report: any) => !report.isSharedWithMe));
    } catch {
      router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  const openInviteDialog = () => {
    if (reports.length === 0) {
      setMessage("Create a report first, then you can invite a family member to review it in WhatsApp.");
      setTimeout(() => setMessage(null), 5000);
      return;
    }
    setSelectedReport(reports[0]);
    setInviteOpen(true);
  };

  useEffect(() => {
    loadShares();
  }, [router]);

  const handleRevoke = async (shareId: string) => {
    if (!confirm("Are you sure you want to immediately revoke access for this family member?")) return;
    try {
      await api.revokeShare(shareId);
      setMessage("Access revoked immediately. The family member can no longer access this report.");
      loadShares();
      setTimeout(() => setMessage(null), 4000);
    } catch (err: any) {
      alert(err.message || "Failed to revoke share.");
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar user={user} />

      <main className="flex-1 mx-auto w-full max-w-5xl px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
          <h1 className="text-xl font-bold text-slate-900">Consent-First Family Circle</h1>
          <p className="text-xs text-slate-500">
            Involve your trusted family members in major loan decisions without losing control over your private financial records.
          </p>
          </div>
          <button
            type="button"
            onClick={openInviteDialog}
            className="flex items-center gap-1.5 rounded-lg bg-teal-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-teal-700"
          >
            <Share2 className="h-4 w-4" />
            Invite a Family Member
          </button>
        </div>

        {message && (
          <div className="flex items-center gap-2 rounded-xl bg-emerald-50 p-4 text-xs text-emerald-800 border border-emerald-200">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            <span>{message}</span>
          </div>
        )}

        {/* Core Sharing Guarantees */}
        <div className="rounded-xl border border-teal-200 bg-teal-50/50 p-5 space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-bold text-teal-900">
            <ShieldCheck className="h-4 w-4 text-teal-600" />
            Consent-First Architectural Controls
          </div>
          <p className="text-xs text-teal-950/85 leading-relaxed">
            By default, all fields are kept strictly private. Recipients only see what you explicitly check. Unshared fields and raw documents are stripped directly on the backend before data leaves the server.
          </p>
        </div>

        {/* Section 1: Shares Created by You */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-teal-600" />
              <h2 className="text-sm font-semibold text-slate-900">
                Reports You Have Shared ({sharesByMe.length})
              </h2>
            </div>
          </div>

          {sharesByMe.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-500 space-y-2">
              <p>You haven't shared any reports yet.</p>
              <p className="text-[11px] text-slate-400">
                Open any document analysis or URL report and click "Share with Family" to generate an invitation link.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {sharesByMe.map((s) => (
                <div key={s.id} className="py-3.5 flex flex-wrap items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="text-xs font-semibold text-slate-900 flex items-center gap-2">
                      <span>Recipient: {s.recipientEmail}</span>
                      <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600 font-mono capitalize">
                        {s.reportType.replace(/_/g, " ")}
                      </span>
                    </div>

                    {/* Permissions summary */}
                    <div className="flex flex-wrap gap-1 text-[10px]">
                      <span className="text-slate-500">Granted:</span>
                      {Object.entries(s.permissions || {}).map(([k, v]) =>
                        v ? (
                          <span
                            key={k}
                            className="rounded bg-teal-50 text-teal-800 px-1.5 py-0.2 border border-teal-200/60"
                          >
                            {k.replace("share", "")}
                          </span>
                        ) : null
                      )}
                    </div>

                    <span className="text-[11px] text-slate-400 block">
                      Shared on {formatDate(s.createdAt)}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Link
                      href={`/analyze/${s.reportId}`}
                      className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-200 transition-colors"
                    >
                      View Report
                    </Link>
                    <button
                      onClick={() => handleRevoke(s.id)}
                      className="flex items-center gap-1 rounded-lg bg-red-50 px-3 py-1 text-xs font-medium text-red-700 hover:bg-red-100 transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Revoke
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Section 2: Reports Shared with You */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-teal-600" />
              <h2 className="text-sm font-semibold text-slate-900">
                Reports Shared With You ({sharesWithMe.length})
              </h2>
            </div>
          </div>

          {sharesWithMe.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-500">
              No reports have been shared with your account yet.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {sharesWithMe.map((s) => (
                <div key={s.id} className="py-3 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-semibold text-slate-900">
                      Shared by {s.ownerName} ({s.ownerEmail})
                    </div>
                    <span className="text-[11px] text-slate-500">
                      Report: {s.reportType} • Granted on {formatDate(s.createdAt)}
                    </span>
                  </div>

                  <Link
                    href={`/analyze/${s.reportId}`}
                    className="flex items-center gap-1 rounded-lg bg-teal-50 px-3 py-1 text-xs font-medium text-teal-700 hover:bg-teal-100 transition-colors"
                  >
                    Open Shared View <ExternalLink className="h-3.5 w-3.5" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {selectedReport && (
        <ShareDialog
          isOpen={inviteOpen}
          onClose={() => setInviteOpen(false)}
          reportId={selectedReport.id}
          reportType={selectedReport.reportType}
          reportTitle={selectedReport.title}
        />
      )}
    </div>
  );
}
