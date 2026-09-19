"use client";

import React from "react";
import { X, Search, FileText, AlertTriangle, CheckCircle2 } from "lucide-react";
import { EvidenceQuality } from "@/types";

interface EvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  sourceReference?: string | null;
  supportingQuote?: string | null;
  evidenceQuality: EvidenceQuality;
  explanation: string;
  recommendedQuestion?: string;
  isOcr?: boolean;
}

export function EvidenceModal({
  isOpen,
  onClose,
  title,
  sourceReference,
  supportingQuote,
  evidenceQuality,
  explanation,
  recommendedQuestion,
  isOcr = false,
}: EvidenceModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
      <div
        className="w-full max-w-xl rounded-xl bg-white p-6 shadow-xl border border-slate-200 animate-in fade-in zoom-in-95 duration-150"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="rounded-lg bg-teal-50 p-2 text-teal-700">
              <Search className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900">{title}</h3>
              <p className="text-xs text-slate-500">Supporting Document Citation & Limitations</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="mt-4 space-y-4">
          {/* Source reference & extraction method badges */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
              <FileText className="h-3.5 w-3.5 text-slate-500" />
              Location: {sourceReference || "Document Header / General Terms"}
            </span>

            {isOcr ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 border border-amber-200">
                <AlertTriangle className="h-3 w-3" />
                OCR Extracted Scan
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="h-3 w-3" />
                Direct Digital Text
              </span>
            )}

            <span className="text-xs text-slate-400 ml-auto capitalize">
              Quality: {evidenceQuality}
            </span>
          </div>

          {/* Quoted clause */}
          {supportingQuote ? (
            <div>
              <label className="text-xs font-medium uppercase tracking-wider text-slate-500 block mb-1.5">
                Exact Extracted Clause
              </label>
              <div className="rounded-lg bg-slate-50 p-3.5 text-sm text-slate-800 border-l-4 border-teal-600 font-mono leading-relaxed whitespace-pre-wrap">
                “{supportingQuote}”
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Note: Exact characters matched against raw extracted text. OCR approximations may reflect minor scan artifacts.
              </p>
            </div>
          ) : (
            <div className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800 border border-amber-200">
              No direct verbatim quote found in readable text. This finding was deduced from missing disclosures or structural absence.
            </div>
          )}

          {/* Plain language explanation */}
          <div>
            <label className="text-xs font-medium uppercase tracking-wider text-slate-500 block mb-1">
              Plain-Language Interpretation
            </label>
            <p className="text-sm text-slate-700 leading-relaxed bg-slate-50/50 p-3 rounded-lg border border-slate-100">
              {explanation}
            </p>
          </div>

          {/* Recommended Question */}
          {recommendedQuestion && (
            <div className="rounded-lg bg-teal-50/60 p-3.5 border border-teal-100">
              <span className="text-xs font-semibold text-teal-900 block mb-1">
                Suggested Clarification for Your Lender:
              </span>
              <p className="text-sm text-teal-800 italic">“{recommendedQuestion}”</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-lg bg-slate-100 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-200 transition-colors"
          >
            Close Viewer
          </button>
        </div>
      </div>
    </div>
  );
}
