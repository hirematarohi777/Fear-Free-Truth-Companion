"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Link as LinkIcon,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ExternalLink,
  Lock,
  FileCode,
  ArrowRight,
  Clock,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { DemoModeBanner } from "@/components/DemoModeBanner";
import { QuestionPanel } from "@/components/QuestionPanel";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { UrlCheckReport, SingleUrlCheckItem } from "@/types";

const URL_STAGES = [
  { key: "fetching_website", label: "Fetching website" },
  { key: "checking_signals", label: "Checking risk signals" },
  { key: "verifying_entity", label: "Verifying regulatory entity" },
  { key: "preparing_explanation", label: "Preparing explanation" },
];

function CheckLinkPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const idFromQuery = searchParams.get("id");

  const [user, setUser] = useState<any>(null);
  const [urlInput, setUrlInput] = useState("");
  const [report, setReport] = useState<UrlCheckReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Background job tracking
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStage, setJobStage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    api.getMe().then(setUser).catch(() => router.push("/login"));
  }, [router]);

  // Load existing report if ID in URL
  useEffect(() => {
    if (idFromQuery) {
      setLoading(true);
      api
        .getUrlCheck(idFromQuery)
        .then((data) => {
          setReport(data);
          setUrlInput(data.submittedUrl);
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [idFromQuery]);

  // Job polling
  useEffect(() => {
    if (!jobId || !isProcessing) return;

    const interval = setInterval(async () => {
      try {
        const job = await api.getJobStatus(jobId);
        setJobStage(job.stage);

        if (job.status === "completed") {
          setIsProcessing(false);
          clearInterval(interval);
          const fullData = await api.getUrlCheck(job.resourceId);
          setReport(fullData);
        } else if (job.status === "failed" || job.status === "cancelled") {
          setIsProcessing(false);
          clearInterval(interval);
          setError(job.errorCode || "URL verification failed.");
        }
      } catch (err) {
        // Polling error
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [jobId, isProcessing]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setError(null);
    setReport(null);
    setIsProcessing(true);
    setJobStage("fetching_website");

    try {
      const res = await api.submitUrl(urlInput.trim());
      setJobId(res.jobId);
    } catch (err: any) {
      setIsProcessing(false);
      setError(err.message || "Failed to submit URL.");
    }
  };

  const handleLoadDemo = (type: "suspicious" | "incomplete") => {
    if (type === "suspicious") {
      setUrlInput("http://fast-instant-sanction-now.test/apply");
    } else {
      setUrlInput("https://urban-fintech-cooperative.test");
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar user={user} />

      <main className="flex-1 mx-auto w-full max-w-4xl px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Check Loan Website or Offer Link</h1>
          <p className="text-xs text-slate-500">
            Scan loan offer links with server-side SSRF defenses, explainable risk heuristics, and configured RBI registry cross-checks.
          </p>
        </div>

        {/* Input Form Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            <label className="text-xs font-semibold text-slate-800 block">
              Enter Webpage URL (HTTP or HTTPS)
            </label>
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="relative flex-1">
                <LinkIcon className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  required
                  placeholder="https://example-bank.co.in/home-loans"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  disabled={isProcessing}
                  className="w-full rounded-xl border border-slate-200 pl-10 pr-4 py-2 text-xs focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 font-mono"
                />
              </div>
              <button
                type="submit"
                disabled={isProcessing || !urlInput.trim()}
                className="rounded-xl bg-teal-600 px-5 py-2 text-xs font-semibold text-white hover:bg-teal-700 transition-colors shadow-xs disabled:opacity-50 shrink-0"
              >
                {isProcessing ? "Checking..." : "Verify Loan Link"}
              </button>
            </div>
            <p className="text-[11px] text-slate-400">
              Only standard ports 80/443 permitted. Private IP destinations and cloud metadata requests are blocked automatically.
            </p>
          </form>

          {/* Synthetic Demo Buttons */}
          <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
              <FileCode className="h-3 w-3 text-amber-600" /> Try Synthetic Demos:
            </span>
            <button
              type="button"
              onClick={() => handleLoadDemo("suspicious")}
              disabled={isProcessing}
              className="rounded-lg bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-200 transition-colors"
            >
              1. Suspicious Advance Fee & 100% Approval (.test)
            </button>
            <button
              type="button"
              onClick={() => handleLoadDemo("incomplete")}
              disabled={isProcessing}
              className="rounded-lg bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-200 transition-colors"
            >
              2. Unverified Regulatory Domain (.test)
            </button>
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-2.5 rounded-xl bg-red-50 p-4 text-xs text-red-700 border border-red-200">
            <AlertCircle className="h-5 w-5 shrink-0 text-red-600 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold block">Verification Notice</span>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Real Processing Tracker */}
        {isProcessing && (
          <div className="rounded-xl border border-teal-200 bg-teal-50/50 p-6 space-y-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
                <span className="text-xs font-bold text-teal-900 uppercase tracking-wider">
                  Scanning Website Signals...
                </span>
              </div>
              <span className="text-xs font-mono text-teal-700">
                Stage: {jobStage?.replace(/_/g, " ").toUpperCase() || "INITIALIZING"}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
              {URL_STAGES.map((s, idx) => {
                const isCurrent = jobStage === s.key;
                const isPast =
                  URL_STAGES.findIndex((x) => x.key === jobStage) > idx;
                return (
                  <div
                    key={s.key}
                    className={`rounded-lg p-2.5 text-center text-xs border transition-colors ${
                      isCurrent
                        ? "bg-teal-600 text-white font-semibold border-teal-700"
                        : isPast
                        ? "bg-white text-teal-800 border-teal-200"
                        : "bg-slate-100/70 text-slate-400 border-slate-200"
                    }`}
                  >
                    <span className="text-[10px] block font-mono">0{idx + 1}</span>
                    <span className="text-[11px] leading-tight block mt-0.5">{s.label}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Results View */}
        {report && (
          <div className="space-y-6">
            {report.submittedUrl.includes(".test") && <DemoModeBanner />}

            {/* Overall Outcome Banner */}
            <div
              className={`rounded-2xl border p-6 shadow-sm space-y-4 ${
                report.overallOutcome === "Significant risk indicators found"
                  ? "bg-red-50/50 border-red-200"
                  : report.overallOutcome === "Some concerns require verification"
                  ? "bg-amber-50/50 border-amber-200"
                  : "bg-emerald-50/40 border-emerald-200"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 block mb-1">
                    Overall Risk Assessment
                  </span>
                  <h2 className="text-lg font-bold text-slate-900">{report.overallOutcome}</h2>
                  <span className="text-xs text-slate-600 font-mono mt-0.5 block">
                    Target: {report.finalUrl}
                  </span>
                </div>

                {/* Identity verification badge */}
                <div className="rounded-xl bg-white p-3 border border-slate-200 shadow-2xs">
                  <span className="text-[10px] uppercase font-semibold text-slate-400 block">
                    Official Entity Match
                  </span>
                  <span className="text-xs font-semibold text-slate-800">
                    {report.identityVerificationStatus}
                  </span>
                </div>
              </div>

              {/* HTTPS Disclaimer */}
              <div className="rounded-lg bg-white/80 p-3 text-xs text-slate-700 border border-slate-200/60 leading-relaxed">
                <b>Crucial Truth Notice:</b> HTTPS confirms that traffic between your browser and the website is encrypted. <b>HTTPS does NOT prove that a business is legitimate, licensed, or trustworthy.</b> Scammers frequently use free SSL certificates on fraudulent sites.
              </div>

              {/* Model Summary if available */}
              {report.modelSummary && (
                <div className="rounded-xl bg-white p-4 border border-slate-200 space-y-1">
                  <span className="text-xs font-bold text-teal-900 block">
                    Plain-Language Assessment:
                  </span>
                  <p className="text-xs text-slate-700 leading-relaxed">
                    {report.modelSummary}
                  </p>
                </div>
              )}
            </div>

            {/* Detailed Signal Checks Table */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-semibold text-slate-900 border-b border-slate-100 pb-3">
                Evaluated Website Signals & Registry Cross-Checks
              </h3>

              <div className="space-y-3">
                {report.checks.map((chk, idx) => {
                  const isConcern = chk.status === "concern";
                  const isNoConcern = chk.status === "no_concern_found";
                  return (
                    <div
                      key={idx}
                      className={`rounded-xl p-4 border text-xs space-y-1.5 ${
                        isConcern
                          ? "bg-red-50/30 border-red-200"
                          : isNoConcern
                          ? "bg-slate-50/40 border-slate-200"
                          : "bg-amber-50/30 border-amber-200"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-bold text-slate-900">{chk.checkName}</span>
                        <span
                          className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                            isConcern
                              ? "bg-red-100 text-red-800"
                              : isNoConcern
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-slate-200 text-slate-700"
                          }`}
                        >
                          {chk.status.replace(/_/g, " ")}
                        </span>
                      </div>

                      <p className="text-slate-700 leading-relaxed">{chk.explanation}</p>

                      {chk.evidenceUrlOrQuote && (
                        <div className="rounded bg-white p-2 font-mono text-[11px] text-slate-600 border border-slate-200">
                          Evidence: “{chk.evidenceUrlOrQuote}”
                        </div>
                      )}

                      <div className="text-[11px] text-teal-800 italic pt-1">
                        <b>Recommended Next Step:</b> {chk.recommendedNextStep}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Q&A Panel for URL */}
            <QuestionPanel reportId={report.id} reportType="url_check" />
          </div>
        )}
      </main>
    </div>
  );
}

export default function CheckLinkPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-slate-50 text-xs text-slate-500">Loading verification page…</div>}>
      <CheckLinkPageContent />
    </Suspense>
  );
}
