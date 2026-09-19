"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  FileText,
  AlertTriangle,
  Lock,
  CheckCircle2,
  Clock,
  ArrowRight,
  AlertCircle,
  FileCode,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { DemoModeBanner } from "@/components/DemoModeBanner";
import { api } from "@/lib/api";

const PROCESSING_STAGES = [
  { key: "uploading", label: "Uploading" },
  { key: "extracting_text", label: "Extracting text" },
  { key: "reading_financial_terms", label: "Reading financial terms" },
  { key: "checking_charges", label: "Checking charges" },
  { key: "preparing_explanation", label: "Preparing explanation" },
];

export default function AnalyzePage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Real job state tracking
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStage, setJobStage] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    api.getMe().then(setUser).catch(() => router.push("/login"));
  }, [router]);

  // Real job polling without fake percentages
  useEffect(() => {
    if (!jobId || !isProcessing) return;

    const interval = setInterval(async () => {
      try {
        const job = await api.getJobStatus(jobId);
        setJobStage(job.stage);
        setJobStatus(job.status);

        if (job.status === "completed" || job.status === "completed_with_limitations") {
          setIsProcessing(false);
          clearInterval(interval);
          if (job.resultSummary && job.resultSummary.analysisId) {
            router.push(`/analyze/${job.resultSummary.analysisId}`);
          }
        } else if (job.status === "failed" || job.status === "cancelled") {
          setIsProcessing(false);
          clearInterval(interval);
          setError(job.errorCode || "Document analysis failed.");
        }
      } catch (err: any) {
        // Polling error
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [jobId, isProcessing, router]);

  const handleUpload = async (uploadFile: File) => {
    setError(null);
    setIsProcessing(true);
    setJobStage("uploading");
    setJobStatus("processing");

    const formData = new FormData();
    formData.append("file", uploadFile);

    try {
      const res = await api.uploadDocument(formData);
      setJobId(res.jobId);
    } catch (err: any) {
      setIsProcessing(false);
      setError(err.message || "Failed to upload document.");
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      handleUpload(selected);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const dropped = e.dataTransfer.files[0];
      setFile(dropped);
      handleUpload(dropped);
    }
  };

  // Helper to load synthetic fixtures directly
  const handleLoadSyntheticFixture = async (fixtureName: string) => {
    setError(null);
    setIsProcessing(true);
    setJobStage("uploading");
    
    // In our backend fixtures, we have standard PDFs and DOCX files.
    // Let's create a synthetic File object or fetch the fixture
    try {
      let content: string = "";
      if (fixtureName === "standard") {
        content = "Borrower Name: Smt. Priya Sharma. Sanctioned Loan Amount: Rs. 40,00,000. Facility: Regular Home Loan (Floating Rate). Rate of Interest: 8.5% p.a. Repayment Period: 240 months. Monthly EMI: Rs. 34,713.00. Processing fee: 0.5% payable upfront. Prepayment: Nil foreclosure charges.";
      } else if (fixtureName === "additional") {
        content = "Sanctioned Loan Amount: Rs. 50,00,000. Rate of Interest: 8.9% p.a. Tenor: 180 months. Processing charges: Rs. 25,000. Administrative charges: Rs. 12,500. Legal & valuation charges: Rs. 7,500. Insurance cover: Rs. 42,000 mandatory protection bundled. Late payment charges: Rs. 500 per month. Cheque bounce: Rs. 450.";
      } else if (fixtureName === "conflicting") {
        content = "Sanctioned Loan Amount: Rs. 35,00,000. Section 2: Rate of Interest: 8.75% p.a. Section 8: Rate of Interest: 9.25% p.a. upon second tranche. Tenor: 180 months. Prepayment terms: Subject to conditions in circulars.";
      } else {
        content = "Sanctioned Loan Amount: Rs. 28,00,000. Rate of Interest: 9.1% p.a. [Faded OCR text]. Processing fee: 0.75%.";
      }

      // Generate a mock PDF client-side or send a text file as PDF header
      const blob = new Blob([`%PDF-1.4\n% Synthetic Demo\n${content}`], { type: "application/pdf" });
      const mockFile = new File([blob], `${fixtureName}_demo_loan.pdf`, { type: "application/pdf" });
      setFile(mockFile);
      handleUpload(mockFile);
    } catch (err: any) {
      setError(err.message || "Failed to load fixture.");
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar user={user} />

      <main className="flex-1 mx-auto w-full max-w-4xl px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Analyze Loan Document</h1>
          <p className="text-xs text-slate-500">
            Upload your home loan sanction letter, draft agreement, or schedule to reveal disclosed fees and overlooked clauses.
          </p>
        </div>

        {error && (
          <div className="flex items-start gap-2.5 rounded-xl bg-red-50 p-4 text-xs text-red-700 border border-red-200">
            <AlertCircle className="h-5 w-5 shrink-0 text-red-600 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold block">Processing Alert</span>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Real Processing Tracker (Only visible during processing) */}
        {isProcessing && (
          <div className="rounded-xl border border-teal-200 bg-teal-50/50 p-6 space-y-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
                <span className="text-xs font-bold text-teal-900 uppercase tracking-wider">
                  Analyzing Document in Private Worker...
                </span>
              </div>
              <span className="text-xs font-mono text-teal-700">
                Stage: {jobStage?.replace(/_/g, " ").toUpperCase() || "INITIALIZING"}
              </span>
            </div>

            {/* Real Stages List - No fake progress bar! */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2">
              {PROCESSING_STAGES.map((s, idx) => {
                const isCurrent = jobStage === s.key;
                const isPast =
                  PROCESSING_STAGES.findIndex((x) => x.key === jobStage) > idx ||
                  jobStatus === "completed";
                return (
                  <div
                    key={s.key}
                    className={`rounded-lg p-2.5 text-center text-xs border transition-colors ${
                      isCurrent
                        ? "bg-teal-600 text-white font-semibold border-teal-700 shadow-xs"
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

            <p className="text-[11px] text-teal-800/80 italic text-center">
              Processing runs on local hardware without uploading your private document to external paid AI services.
            </p>
          </div>
        )}

        {/* Upload Zone */}
        {!isProcessing && (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            className={`relative rounded-2xl border-2 border-dashed p-10 text-center transition-all bg-white shadow-xs ${
              dragActive
                ? "border-teal-600 bg-teal-50/40"
                : "border-slate-200 hover:border-slate-300"
            }`}
          >
            <input
              type="file"
              id="doc-upload"
              accept=".pdf,.docx,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              className="absolute inset-0 h-full w-full opacity-0 cursor-pointer"
            />

            <div className="flex flex-col items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-teal-50 text-teal-600">
                <UploadCloud className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">
                  Click to select or drag and drop your document
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  PDF, DOCX, PNG, JPG accepted (Maximum 20 MB, up to 100 pages)
                </p>
              </div>
              <button
                type="button"
                className="mt-2 rounded-lg bg-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-teal-700 pointer-events-none"
              >
                Browse Files
              </button>
            </div>
          </div>
        )}

        {/* Password & Preparation Guidance */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-800">
            <Lock className="h-4 w-4 text-teal-600" />
            Handling Password-Protected or Encrypted Bank PDFs
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Many Indian banks (SBI, HDFC, ICICI, etc.) protect sanction letters with passwords (e.g. your date of birth or PAN). For security, our local parser cannot crack password-locked files.
          </p>
          <div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-700 space-y-1.5 border border-slate-200/80">
            <p className="font-medium text-slate-800">How to unlock before uploading:</p>
            <ol className="list-decimal pl-5 space-y-1 text-[11px] text-slate-600">
              <li>Open your sanction letter in Google Chrome, Microsoft Edge, or Adobe Reader.</li>
              <li>Enter your password to open the file.</li>
              <li>Press <kbd className="rounded bg-slate-200 px-1 py-0.5 font-mono">Ctrl + P</kbd> (or Print).</li>
              <li>Select destination as <b>"Save as PDF"</b> and save an unlocked copy to upload here.</li>
            </ol>
          </div>
        </div>

        {/* Synthetic Demo Fixtures Launcher */}
        <div className="rounded-xl border border-amber-200/80 bg-amber-50/40 p-5 space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-amber-900">
            <FileCode className="h-4 w-4 text-amber-600" />
            Quick Test: Load Pre-Packaged Synthetic Fixtures
          </div>
          <p className="text-xs text-amber-800/90">
            Evaluate document extraction and fee categorization with synthetic, clearly labeled home loan scenarios:
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            <button
              onClick={() => handleLoadSyntheticFixture("standard")}
              disabled={isProcessing}
              className="rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-slate-700 border border-slate-200 hover:bg-slate-50 shadow-2xs"
            >
              1. Standard Home Loan (₹40L, 8.5%)
            </button>
            <button
              onClick={() => handleLoadSyntheticFixture("additional")}
              disabled={isProcessing}
              className="rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-slate-700 border border-slate-200 hover:bg-slate-50 shadow-2xs"
            >
              2. Additional Charges (Admin & Bundled Insurance)
            </button>
            <button
              onClick={() => handleLoadSyntheticFixture("conflicting")}
              disabled={isProcessing}
              className="rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-slate-700 border border-slate-200 hover:bg-slate-50 shadow-2xs"
            >
              3. Conflicting Interest Rates (8.75% vs 9.25%)
            </button>
            <button
              onClick={() => handleLoadSyntheticFixture("scanned")}
              disabled={isProcessing}
              className="rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-slate-700 border border-slate-200 hover:bg-slate-50 shadow-2xs"
            >
              4. Degraded Scan / OCR Sample
            </button>
          </div>
          <div className="text-[11px] text-amber-700 italic">
            Synthetic demonstration data — not a real lender assessment.
          </div>
        </div>
      </main>
    </div>
  );
}
