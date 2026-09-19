"use client";

import React, { useMemo, useState } from "react";
import { ChevronDown, Search } from "lucide-react";
import { ChargeFinding } from "@/types";
import { FINDING_CATEGORY_ORDER } from "@/lib/permissions";

interface FindingsAccordionProps {
  findings: ChargeFinding[];
  onViewEvidence: (finding: ChargeFinding) => void;
}

export function FindingsAccordion({ findings, onViewEvidence }: FindingsAccordionProps) {
  const grouped = useMemo(() => {
    const buckets: Record<string, ChargeFinding[]> = {};
    for (const cat of FINDING_CATEGORY_ORDER) buckets[cat] = [];
    for (const finding of findings) {
      const key = FINDING_CATEGORY_ORDER.includes(finding.category as (typeof FINDING_CATEGORY_ORDER)[number])
        ? finding.category
        : "Easily overlooked charge";
      if (!buckets[key]) buckets[key] = [];
      buckets[key].push(finding);
    }
    return buckets;
  }, [findings]);

  const [open, setOpen] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    for (const cat of FINDING_CATEGORY_ORDER) initial[cat] = true;
    return initial;
  });

  if (findings.length === 0) {
    return (
      <div className="py-6 text-center text-xs text-slate-500">
        No additional charges identified in the readable content. This does not establish that no other charges apply.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {FINDING_CATEGORY_ORDER.map((category) => {
        const items = grouped[category] || [];
        if (items.length === 0) return null;
        const isOpen = open[category];
        return (
          <div key={category} className="rounded-xl border border-slate-200 overflow-hidden">
            <button
              type="button"
              onClick={() => setOpen((prev) => ({ ...prev, [category]: !prev[category] }))}
              className="flex w-full items-center justify-between bg-slate-50 px-4 py-2.5 text-left"
            >
              <span className="text-xs font-semibold text-slate-800">{category}</span>
              <span className="flex items-center gap-2 text-[11px] text-slate-500">
                {items.length} item{items.length === 1 ? "" : "s"}
                <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
              </span>
            </button>
            {isOpen && (
              <div className="space-y-3 p-3 bg-white">
                {items.map((finding) => {
                  const isHigh = finding.severity === "high";
                  const isMed = finding.severity === "medium";
                  return (
                    <div
                      key={finding.id}
                      className={`rounded-xl p-4 border ${
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
                        </div>
                        {finding.amountOrCalculationBasis && (
                          <div className="rounded-lg bg-white px-2.5 py-1 text-xs font-semibold text-slate-800 border border-slate-200 font-mono">
                            {finding.amountOrCalculationBasis}
                          </div>
                        )}
                      </div>
                      <p className="mt-2 text-xs text-slate-700 leading-relaxed">
                        {finding.plainLanguageExplanation}
                      </p>
                      {finding.recommendedQuestionForLender && (
                        <div className="mt-2.5 rounded-lg bg-white/80 p-2.5 text-xs text-teal-900 border border-teal-100/80">
                          <span className="font-semibold block mb-0.5 text-[11px] text-teal-800">
                            Recommended question to ask lender:
                          </span>
                          <span className="italic">“{finding.recommendedQuestionForLender}”</span>
                        </div>
                      )}
                      <div className="mt-3 flex items-center justify-between border-t border-slate-200/50 pt-2 text-[11px]">
                        <span className="text-slate-500">Location: {finding.sourceReference || "General Clauses"}</span>
                        <button
                          type="button"
                          onClick={() => onViewEvidence(finding)}
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
        );
      })}
    </div>
  );
}
