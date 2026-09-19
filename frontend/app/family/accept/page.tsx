"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Users, CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";
import Link from "next/link";

function AcceptInvitationPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reportId, setReportId] = useState<string | null>(null);

  useEffect(() => {
    api
      .getMe()
      .then((u) => {
        setUser(u);
        if (token) {
          handleAccept(token);
        } else {
          setError("No invitation token found in the URL.");
          setLoading(false);
        }
      })
      .catch(() => {
        // Redirect to login preserving destination
        router.push(`/login?redirect=/family/accept?token=${token || ""}`);
      });
  }, [token, router]);

  const handleAccept = async (t: string) => {
    try {
      const res = await api.acceptInvitation(t);
      setSuccess("You have accepted the family report invitation!");
      setReportId(res.reportId);
    } catch (err: any) {
      setError(err.message || "Failed to accept invitation. The link may be expired or already used.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar user={user} />

      <main className="flex-1 max-w-md mx-auto py-16 px-4 text-center space-y-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm space-y-4">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-teal-50 text-teal-600">
            <Users className="h-6 w-6" />
          </div>

          <h1 className="text-lg font-bold text-slate-900">Family Circle Invitation</h1>

          {loading ? (
            <div className="flex flex-col items-center gap-2 py-4 text-xs text-slate-500">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
              <span>Verifying cryptographic token & recipient identity...</span>
            </div>
          ) : success ? (
            <div className="space-y-4">
              <div className="rounded-lg bg-emerald-50 p-4 text-xs text-emerald-800 border border-emerald-200">
                <CheckCircle2 className="h-5 w-5 mx-auto text-emerald-600 mb-1" />
                <span className="font-semibold block">Invitation Accepted</span>
                <span>You now have read-only access to this loan assessment report.</span>
              </div>

              {reportId && (
                <Link
                  href={`/analyze/${reportId}`}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-teal-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-teal-700 shadow-sm transition-colors"
                >
                  View Shared Report <ArrowRight className="h-4 w-4" />
                </Link>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-lg bg-red-50 p-4 text-xs text-red-800 border border-red-200">
                <AlertCircle className="h-5 w-5 mx-auto text-red-600 mb-1" />
                <span className="font-semibold block">Unable to Accept</span>
                <span>{error}</span>
              </div>

              <Link
                href="/family"
                className="inline-flex items-center gap-1 text-xs font-medium text-slate-600 hover:text-slate-900"
              >
                Go to Family Circle
              </Link>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function AcceptInvitationPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-slate-50 text-xs text-slate-500">Loading invitation…</div>}>
      <AcceptInvitationPageContent />
    </Suspense>
  );
}
