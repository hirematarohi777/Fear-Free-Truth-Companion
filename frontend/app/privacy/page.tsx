"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ShieldCheck,
  Lock,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Server,
  FileText,
  Clock,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";

export default function PrivacyPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [retentionDays, setRetentionDays] = useState(30);
  const [guarantees, setGuarantees] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  // Deletion modal
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    api
      .getMe()
      .then(setUser)
      .catch(() => router.push("/login"));

    api
      .getPrivacySettings()
      .then((data) => {
        setRetentionDays(data.documentRetentionDays || 30);
        setGuarantees(data.privacyGuarantees || []);
      })
      .catch(() => {});
  }, [router]);

  const handleUpdateRetention = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updatePrivacySettings(retentionDays);
      setSavedMessage("Retention settings updated successfully.");
      setTimeout(() => setSavedMessage(null), 3000);
    } catch (err: any) {
      alert(err.message || "Failed to update retention.");
    } finally {
      setSaving(false);
    }
  };

  const handleConfirmAccountDeletion = async () => {
    setDeleting(true);
    try {
      await api.deleteAccount();
      alert("Your account and all associated documents, reports, and shares have been permanently purged.");
      router.push("/login");
    } catch (err: any) {
      alert(err.message || "Failed to delete account.");
      setDeleting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar user={user} />

      <main className="flex-1 mx-auto w-full max-w-4xl px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Privacy, Retention & Security Settings</h1>
          <p className="text-xs text-slate-500">
            Control your data storage policies, understand local processing boundaries, and manage permanent account deletion.
          </p>
        </div>

        {savedMessage && (
          <div className="flex items-center gap-2 rounded-xl bg-emerald-50 p-4 text-xs text-emerald-800 border border-emerald-200">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            <span>{savedMessage}</span>
          </div>
        )}

        {/* Privacy Architecture Guarantees */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <ShieldCheck className="h-5 w-5 text-teal-600" />
            <h2 className="text-sm font-semibold text-slate-900">
              Our Privacy Commitments & Security Architecture
            </h2>
          </div>

          <ul className="space-y-3 text-xs text-slate-700">
            <li className="flex items-start gap-2.5">
              <span className="h-5 w-5 rounded-full bg-teal-50 flex items-center justify-center text-teal-700 font-bold shrink-0 text-[10px]">
                ✓
              </span>
              <div>
                <b className="text-slate-900">No Model Training:</b> Your uploaded financial documents are never used for AI model training or commercial profiling.
              </div>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="h-5 w-5 rounded-full bg-teal-50 flex items-center justify-center text-teal-700 font-bold shrink-0 text-[10px]">
                ✓
              </span>
              <div>
                <b className="text-slate-900">Zero Cloud AI Leakage:</b> Document analysis is powered entirely by a locally hosted Ollama model (Qwen 2.5:7B). No customer text is sent to third-party paid AI providers.
              </div>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="h-5 w-5 rounded-full bg-teal-50 flex items-center justify-center text-teal-700 font-bold shrink-0 text-[10px]">
                ✓
              </span>
              <div>
                <b className="text-slate-900">Isolated Private Storage:</b> Files are assigned cryptographically random storage keys and placed outside the public web server directory.
              </div>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="h-5 w-5 rounded-full bg-teal-50 flex items-center justify-center text-teal-700 font-bold shrink-0 text-[10px]">
                ✓
              </span>
              <div>
                <b className="text-slate-900">Consent-First Redaction:</b> Family sharing defaults to all fields being OFF. Unauthorized financial figures are redacted on the server before reaching recipient browsers.
              </div>
            </li>
          </ul>
        </div>

        {/* Data Retention Configuration */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Clock className="h-5 w-5 text-teal-600" />
            <h2 className="text-sm font-semibold text-slate-900">
              Automated Document Retention Period
            </h2>
          </div>

          <form onSubmit={handleUpdateRetention} className="space-y-4">
            <p className="text-xs text-slate-600 leading-relaxed">
              Define how many days your uploaded documents and text chunks should be preserved before automatic expiration. You can also manually delete files at any time.
            </p>

            <div className="max-w-xs space-y-1">
              <label className="text-xs font-semibold text-slate-700 block">
                Retention Window (Days)
              </label>
              <select
                value={retentionDays}
                onChange={(e) => setRetentionDays(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs bg-white text-slate-800 focus:border-teal-500 focus:outline-none"
              >
                <option value={7}>7 Days (High Privacy)</option>
                <option value={15}>15 Days</option>
                <option value={30}>30 Days (Recommended)</option>
                <option value={90}>90 Days</option>
                <option value={180}>180 Days</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="rounded-lg bg-teal-600 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-700 transition-colors shadow-2xs disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save Retention Setting"}
            </button>
          </form>
        </div>

        {/* Danger Zone: Account Deletion */}
        <div className="rounded-2xl border border-red-200 bg-red-50/40 p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-red-100 pb-3 text-red-900">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <h2 className="text-sm font-bold">Permanent Account & Data Deletion</h2>
          </div>

          <p className="text-xs text-red-800 leading-relaxed">
            Permanently delete your account, session credentials, uploaded documents, extracted paragraphs, analysis findings, URL verification logs, and family sharing invitations.
          </p>

          <button
            onClick={() => setDeleteModalOpen(true)}
            className="flex items-center gap-1.5 rounded-lg bg-red-600 px-4 py-2 text-xs font-semibold text-white hover:bg-red-700 transition-colors shadow-2xs"
          >
            <Trash2 className="h-4 w-4" /> Delete My Account & All Data
          </button>
        </div>
      </main>

      {/* Confirmation Modal */}
      {deleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-6 w-6" />
              <h3 className="text-base font-bold text-slate-900">Confirm Permanent Deletion</h3>
            </div>

            <div className="rounded-lg bg-amber-50 p-3.5 text-xs text-amber-900 border border-amber-200/80 space-y-2">
              <p className="font-semibold">Before proceeding, understand what happens:</p>
              <ul className="list-disc pl-4 space-y-1 text-[11px] text-amber-800">
                <li>All uploaded loan PDFs and DOCX files on disk will be wiped immediately.</li>
                <li>All text chunks and extracted financial data in MongoDB are deleted.</li>
                <li>All family share links generated by you will immediately stop working.</li>
                <li><b>This action is permanent and cannot be undone.</b></li>
              </ul>
            </div>

            <p className="text-xs text-slate-600">
              Type your email <b>{user?.email}</b> or click confirm to execute immediate deletion.
            </p>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setDeleteModalOpen(false)}
                disabled={deleting}
                className="rounded-lg px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmAccountDeletion}
                disabled={deleting}
                className="flex items-center gap-1.5 rounded-lg bg-red-600 px-4 py-2 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-50 shadow-sm"
              >
                <Trash2 className="h-4 w-4" />
                {deleting ? "Deleting Everything..." : "Yes, Permanently Delete All Data"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
