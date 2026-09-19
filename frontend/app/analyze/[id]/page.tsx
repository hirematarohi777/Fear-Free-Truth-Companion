"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  Download,
  Share2,
  AlertTriangle,
  HelpCircle,
  TrendingUp,
  Search,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
  ArrowLeft,
  Calendar,
  Lock,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { EvidenceModal } from "@/components/EvidenceModal";
import { ShareDialog } from "@/components/ShareDialog";
import { QuestionPanel } from "@/components/QuestionPanel";
import { RateScenarioTable } from "@/components/RateScenarioTable";
import { AmortizationSchedule } from "@/components/AmortizationSchedule";
import { DemoModeBanner } from "@/components/DemoModeBanner";
import { api } from "@/lib/api";
import { formatINR, formatPercent, formatDate } from "@/lib/utils";
import { LoanAnalysisReport, ChargeFinding, FinancialField } from "@/types";

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const analysisId = params.id as string;

  const [user, setUser] = useState<any>(null);
  const [report, setReport] = useState<LoanAnalysisReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Evidence modal state
  const [selectedEvidence, setSelectedEvidence] = useState<{
    title: string;
    sourceReference?: string | null;
    supportingQuote?: string | null;
    evidenceQuality: any;
    explanation: string;
    recommendedQuestion?: string;
  } | null>(null);

  // Share dialog state
  const [shareOpen, setShareOpen] = useState(false);

  useEffect(() => {
    async function fetchAnalysis() {
      try {
        const u = await api.getMe();
        setUser(u);
        const data = await api.getAnalysis(analysisId);
        setReport(data);
      } catch (err: any) {
        setError(err.message || "Failed to load loan analysis report.");
      } finally {
        setLoading(false);
      }
    }
    fetchAnalysis();
  }, [analysisId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3 text-slate-500 text-xs">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
          <span>Retrieving report evidence...</span>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen flex flex-col bg-slate-50">
        <Navbar user={user} />
        <main className="flex-1 max-w-2xl mx-auto py-16 px-4 text-center space-y-4">
          <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
          <h2 className="text-lg font-bold text-slate-900">Report Unavailable</h2>
          <p className="text-xs text-slate-600">{error || "The requested analysis report could not be found."}</p>
          <Link
            href="/analyze"
            className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-700"
          >
            <ArrowLeft className="h-4 w-4" /> Return to Analyzer
          </Link>
        </main>
      </div>
    );
  }

  const terms = report.extractedTerms;
  const findings = report.findings || [];
  const isOcrDegraded =
    report.evidenceQuality === "partial" || report.evidenceQuality === "insufficient";

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar user={user} />

      <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Breadcrumb & Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Link
            href="/reports"
            className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-900"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to All Reports
          </Link>

          <div className="flex items-center gap-2">
            {/* PDF Export */}
            <a
              href={`/api/v1/reports/document_analysis/${report.id}/export?format=pdf`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-slate-700 border border-slate-200 hover:bg-slate-50 shadow-2xs"
            >
              <Download className="h-3.5 w-3.5 text-slate-500" />
              Download PDF Report
            </a>

            {/* JSON Export */}
            <a
              href={`/api/v1/reports/document_analysis/${report.id}/export?format=json`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-slate-700 border border-slate-200 hover:bg-slate-50 shadow-2xs"
            >
              <FileSpreadsheet className="h-3.5 w-3.5 text-slate-500" />
              JSON Data
            </a>

            {/* Family Sharing */}
            {!report.isSharedView && (
              <button
                onClick={() => setShareOpen(true)}
                className="flex items-center gap-1.5 rounded-lg bg-teal-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-teal-700 shadow-sm transition-colors"
              >
                <Share2 className="h-3.5 w-3.5" />
                Share with Family
              </button>
            )}
          </div>
        </div>

        {/* Shared View Disclaimer Badge if family member */}
        {report.isSharedView && (
          <div className="flex items-center gap-2 rounded-xl bg-teal-50 p-4 border border-teal-200 text-xs text-teal-900">
            <Lock className="h-4 w-4 text-teal-600 shrink-0" />
            <div>
              <span className="font-semibold block">Shared Family Consensus View</span>
              <span>
                You are viewing this report under permissions explicitly selected by the loan applicant. Unshared or confidential personal figures are withheld at the source.
              </span>
            </div>
          </div>
        )}

        {/* OCR Degradation Banner */}
        {isOcrDegraded && (
          <div className="flex items-start gap-2.5 rounded-xl bg-amber-50 p-4 text-xs text-amber-900 border border-amber-200 shadow-2xs">
            <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold block">Incomplete Extraction Notice (OCR Used)</span>
              <span>
                Portions of this document were image-based scans with degraded contrast. While optical character recognition was performed, faint footnotes or faint text may be incomplete. Always confirm terms against original printed records.
              </span>
            </div>
          </div>
        )}

        {/* Header Summary Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-1 max-w-2xl">
              <span className="text-[11px] font-semibold text-teal-700 uppercase tracking-wider">
                Loan Truth & Clarity Assessment
              </span>
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900">
                {terms.lenderName.value || "Home Loan Offer Analysis"}
              </h1>
              <p className="text-xs text-slate-500">
                Analysis completed on {formatDate(report.completedAt || report.createdAt)} • Engine: {report.modelName}
              </p>
            </div>

            <div className="rounded-xl bg-slate-50 p-3 text-right border border-slate-100">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">
                Evidence Confidence
              </span>
              <span className="text-xs font-bold capitalize text-slate-800">
                {report.evidenceQuality} Yield
              </span>
            </div>
          </div>

          {/* Carefully worded summary statement */}
          <div className="rounded-xl bg-slate-50/70 p-4 border border-slate-200/80 text-xs text-slate-800 leading-relaxed">
            <p className="font-medium text-slate-900 mb-0.5">Summary Assessment:</p>
            {report.summaryStatement}
          </div>

          {/* Key Metric Highlights Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-100">
              <span className="text-[11px] text-slate-500 block">Sanctioned Principal</span>
              <div className="text-base font-bold text-slate-900 font-mono mt-0.5">
                {terms.loanAmount.value || "Not found"}
              </div>
              <button
                onClick={() =>
                  setSelectedEvidence({
                    title: "Sanctioned Loan Amount",
                    sourceReference: terms.loanAmount.sourceReference,
                    supportingQuote: terms.loanAmount.supportingQuote,
                    evidenceQuality: report.evidenceQuality,
                    explanation: "Principal credit facility approved by the lender.",
                  })
                }
                className="mt-1 text-[11px] font-medium text-teal-600 hover:underline flex items-center gap-1"
              >
                <Search className="h-3 w-3" /> View Source
              </button>
            </div>

            <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-100">
              <span className="text-[11px] text-slate-500 block">Rate of Interest</span>
              <div className="text-base font-bold text-slate-900 font-mono mt-0.5">
                {terms.interestRate.value || "Not found"}
              </div>
              <button
                onClick={() =>
                  setSelectedEvidence({
                    title: "Interest Rate",
                    sourceReference: terms.interestRate.sourceReference,
                    supportingQuote: terms.interestRate.supportingQuote,
                    evidenceQuality: report.evidenceQuality,
                    explanation: terms.interestRate.notes || "Annual nominal interest rate.",
                  })
                }
                className="mt-1 text-[11px] font-medium text-teal-600 hover:underline flex items-center gap-1"
              >
                <Search className="h-3 w-3" /> View Source
              </button>
            </div>

            <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-100">
              <span className="text-[11px] text-slate-500 block">Repayment Tenure</span>
              <div className="text-base font-bold text-slate-900 font-mono mt-0.5">
                {terms.loanTenureMonths.value || "Not found"}
              </div>
              <button
                onClick={() =>
                  setSelectedEvidence({
                    title: "Tenure Period",
                    sourceReference: terms.loanTenureMonths.sourceReference,
                    supportingQuote: terms.loanTenureMonths.supportingQuote,
                    evidenceQuality: report.evidenceQuality,
                    explanation: "Total contracted repayment duration.",
                  })
                }
                className="mt-1 text-[11px] font-medium text-teal-600 hover:underline flex items-center gap-1"
              >
                <Search className="h-3 w-3" /> View Source
              </button>
            </div>

            <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-100">
              <span className="text-[11px] text-slate-500 block">Monthly EMI</span>
              <div className="text-base font-bold text-slate-900 font-mono mt-0.5">
                {terms.emi.value ||
                  (report.calculations ? formatINR(report.calculations.monthlyEmi) : "Not stated")}
              </div>
              <span className="text-[10px] text-slate-400">Monthly rest formula</span>
            </div>
          </div>
        </div>

        {/* Categorized Charge Findings Accordion */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">
                Disclosed & Overlooked Charges ({findings.length} Identified)
              </h2>
              <p className="text-xs text-slate-500">
                Categorized by transparency, conditionality, and potential borrower impact
              </p>
            </div>
          </div>

          {findings.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-500">
              No additional charges identified in the readable content. This does not establish that no other charges apply.
            </div>
          ) : (
            <div className="space-y-3">
              {findings.map((finding) => {
                const isHigh = finding.severity === "high";
                const isMed = finding.severity === "medium";
                return (
                  <div
                    key={finding.id}
                    className={`rounded-xl p-4 border transition-colors ${
                      isHigh
                        ? "bg-red-50/40 border-red-200"
                        : isMed
                        ? "bg-amber-50/40 border-amber-200"
                        : "bg-slate-50/50 border-slate-200"
                    }`}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="space-y-1 max-w-xl">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-900">{finding.title}</span>
                          <span
                            className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                              isHigh
                                ? "bg-red-100 text-red-800"
                                : isMed
                                ? "bg-amber-100 text-amber-800"
                                : "bg-slate-200 text-slate-700"
                            }`}
                          >
                            {finding.severity}
                          </span>
                        </div>
                        <span className="text-[11px] text-slate-500 font-medium block">
                          Category: {finding.category}
                        </span>
                      </div>

                      {finding.amountOrCalculationBasis && (
                        <div className="rounded-lg bg-white px-2.5 py-1 text-xs font-semibold text-slate-800 border border-slate-200 shadow-2xs font-mono">
                          {finding.amountOrCalculationBasis}
                        </div>
                      )}
                    </div>

                    <p className="mt-2 text-xs text-slate-700 leading-relaxed">
                      {finding.plainLanguageExplanation}
                    </p>

                    {/* Recommended question */}
                    {finding.recommendedQuestionForLender && (
                      <div className="mt-2.5 rounded-lg bg-white/80 p-2.5 text-xs text-teal-900 border border-teal-100/80">
                        <span className="font-semibold block mb-0.5 text-[11px] text-teal-800">
                          Recommended question to ask lender:
                        </span>
                        <span className="italic">“{finding.recommendedQuestionForLender}”</span>
                      </div>
                    )}

                    {/* Evidence viewer trigger */}
                    <div className="mt-3 flex items-center justify-between border-t border-slate-200/50 pt-2 text-[11px]">
                      <span className="text-slate-500">
                        Location: {finding.sourceReference || "General Clauses"}
                      </span>
                      <button
                        onClick={() =>
                          setSelectedEvidence({
                            title: finding.title,
                            sourceReference: finding.sourceReference,
                            supportingQuote: finding.supportingQuote,
                            evidenceQuality: finding.evidenceQuality,
                            explanation: finding.plainLanguageExplanation,
                            recommendedQuestion: finding.recommendedQuestionForLender,
                          })
                        }
                        className="font-medium text-teal-600 hover:text-teal-700 flex items-center gap-1"
                      >
                        <Search className="h-3 w-3" /> View Verbatim Clause
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Rate Sensitivity & Repayment Illustrations */}
        {report.calculations && (
          <div className="space-y-6">
            <RateScenarioTable scenarios={report.calculations.rateScenarios} />
            <AmortizationSchedule schedule={report.calculations.amortizationSchedule} />
          </div>
        )}

        {/* Full Terms Reference Table */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <h2 className="text-sm font-semibold text-slate-900 border-b border-slate-100 pb-3">
            All Extracted Sanction Terms & Clauses
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Field Name</th>
                  <th className="py-2.5 px-3">Extracted Value</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Source Location</th>
                  <th className="py-2.5 px-3 text-right">Evidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {Object.entries(terms).map(([key, f]: [string, any]) => (
                  <tr key={key} className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-medium text-slate-800">{f.fieldName}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-900">{f.value || "Not found"}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] font-semibold capitalize ${
                          f.status === "found"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : f.status === "conflicting"
                            ? "bg-red-50 text-red-700 border border-red-200 font-bold"
                            : "bg-slate-100 text-slate-500"
                        }`}
                      >
                        {f.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-500">{f.sourceReference || "—"}</td>
                    <td className="py-2.5 px-3 text-right">
                      {f.supportingQuote ? (
                        <button
                          onClick={() =>
                            setSelectedEvidence({
                              title: f.fieldName,
                              sourceReference: f.sourceReference,
                              supportingQuote: f.supportingQuote,
                              evidenceQuality: report.evidenceQuality,
                              explanation: f.notes || "Direct sanction term extraction.",
                            })
                          }
                          className="text-teal-600 hover:text-teal-700 font-medium inline-flex items-center gap-1"
                        >
                          <Search className="h-3 w-3" /> View
                        </button>
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Scoped Q&A Panel */}
        <QuestionPanel reportId={report.id} reportType="document_analysis" />
      </main>

      {/* Evidence Viewer Modal */}
      {selectedEvidence && (
        <EvidenceModal
          isOpen={!!selectedEvidence}
          onClose={() => setSelectedEvidence(null)}
          title={selectedEvidence.title}
          sourceReference={selectedEvidence.sourceReference}
          supportingQuote={selectedEvidence.supportingQuote}
          evidenceQuality={selectedEvidence.evidenceQuality}
          explanation={selectedEvidence.explanation}
          recommendedQuestion={selectedEvidence.recommendedQuestion}
        />
      )}

      {/* Family Sharing Dialog */}
      <ShareDialog
        isOpen={shareOpen}
        onClose={() => setShareOpen(false)}
        reportId={report.id}
        reportType="document_analysis"
      />
    </div>
  );
}
