"use client";

import React, { useState } from "react";
import { HelpCircle, Send, AlertCircle, BookOpen, Sparkles } from "lucide-react";
import { api } from "@/lib/api";

interface QuestionPanelProps {
  reportId: string;
  reportType: "document_analysis" | "url_check";
}

interface QAItem {
  question: string;
  answer: string;
  citedSources: Array<{ sourceReference: string; quote?: string | null }>;
  cannotAnswerReason?: string | null;
}

export function QuestionPanel({ reportId, reportType }: QuestionPanelProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [qaHistory, setQaHistory] = useState<QAItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const quickQuestions =
    reportType === "document_analysis"
      ? [
          "Which charges do I need to clarify?",
          "Is insurance described as optional?",
          "What happens if I repay early?",
          "Are there conflicting interest rates?",
        ]
      : [
          "Which website checks could not be completed?",
          "Does this website ask for any upfront fees?",
          "Is the lender entity corroborated with official sources?",
        ];

  const handleAsk = async (qText: string) => {
    if (!qText.trim()) return;
    setError(null);
    setLoading(true);

    try {
      const res = await api.askReportQuestion(reportType, reportId, qText);
      setQaHistory((prev) => [
        ...prev,
        {
          question: qText,
          answer: res.answer,
          citedSources: res.citedSources || [],
          cannotAnswerReason: res.cannotAnswerReason,
        },
      ]);
      setQuestion("");
    } catch (err: any) {
      setError(err.message || "Unable to retrieve answer.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
        <div className="rounded-lg bg-teal-50 p-2 text-teal-700">
          <HelpCircle className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Ask Questions About This Report</h3>
          <p className="text-xs text-slate-500">
            Answers are strictly bounded by your accessible evidence.
          </p>
        </div>
      </div>

      {/* Suggested quick questions */}
      <div className="flex flex-wrap gap-1.5">
        {quickQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleAsk(q)}
            disabled={loading}
            className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700 hover:bg-teal-50 hover:text-teal-700 transition-colors border border-slate-200/80 disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Q&A Transcript */}
      {qaHistory.length > 0 && (
        <div className="space-y-3 pt-2 max-h-96 overflow-y-auto pr-1">
          {qaHistory.map((item, idx) => (
            <div key={idx} className="rounded-lg bg-slate-50 p-4 border border-slate-200 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-800">
                <span className="rounded bg-teal-100 px-1.5 py-0.5 text-teal-800 font-mono">Q</span>
                {item.question}
              </div>
              <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap pl-6">
                {item.answer}
              </p>

              {item.citedSources.length > 0 && (
                <div className="pl-6 pt-1">
                  <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1 mb-1">
                    <BookOpen className="h-3 w-3 text-teal-600" />
                    Cited Source Evidence:
                  </span>
                  <div className="space-y-1">
                    {item.citedSources.map((cs, cIdx) => (
                      <div
                        key={cIdx}
                        className="rounded bg-white p-2 text-[11px] text-slate-600 border border-slate-200 font-mono"
                      >
                        <b>[{cs.sourceReference}]</b> {cs.quote ? `“${cs.quote}”` : ""}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {item.cannotAnswerReason && (
                <div className="pl-6 text-[11px] text-amber-700 italic">
                  Note: {item.cannotAnswerReason}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Question Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleAsk(question);
        }}
        className="flex items-center gap-2 pt-2"
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about this document or loan terms..."
          className="flex-1 rounded-lg border border-slate-200 px-3.5 py-2 text-xs focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="flex items-center gap-1 rounded-lg bg-teal-600 px-4 py-2 text-xs font-medium text-white hover:bg-teal-700 transition-colors shadow-sm disabled:opacity-50"
        >
          <Send className="h-3.5 w-3.5" />
          {loading ? "Checking..." : "Ask"}
        </button>
      </form>

      {error && (
        <div className="flex items-center gap-1.5 text-xs text-red-600">
          <AlertCircle className="h-3.5 w-3.5" />
          <span>{error}</span>
        </div>
      )}

      <div className="text-[11px] text-slate-400 italic">
        Answers are educational and evidence-bound. Does not constitute legal, tax, or investment advice.
      </div>
    </div>
  );
}
