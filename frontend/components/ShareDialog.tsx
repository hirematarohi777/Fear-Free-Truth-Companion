"use client";

import React, { useState } from "react";
import { X, Users, Share2, AlertCircle, Copy, Check, Lock, MessageCircle, Mail } from "lucide-react";
import { SharingPermissions } from "@/types";
import { api } from "@/lib/api";
import { describeSharePreview } from "@/lib/permissions";

interface ShareDialogProps {
  isOpen: boolean;
  onClose: () => void;
  reportId: string;
  reportType?: string;
  reportTitle?: string;
}

export function ShareDialog({
  isOpen,
  onClose,
  reportId,
  reportType = "document_analysis",
  reportTitle = "Loan Analysis Report",
}: ShareDialogProps) {
  const [email, setEmail] = useState("");
  const [expiryHours, setExpiryHours] = useState(72);
  const [permissions, setPermissions] = useState<SharingPermissions>({
    shareSummary: false,
    shareFindings: false,
    shareFinancialAmounts: false,
    shareSourceExcerpts: false,
    shareOriginalDocument: false,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdLink, setCreatedLink] = useState<string | null>(null);
  const [invitationId, setInvitationId] = useState<string | null>(null);
  const [phone, setPhone] = useState("");
  const [copied, setCopied] = useState(false);
  const [whatsappLoading, setWhatsappLoading] = useState(false);
  const [whatsappStatus, setWhatsappStatus] = useState<string | null>(null);

  if (!isOpen) return null;

  const toggle = (key: keyof SharingPermissions) => {
    setPermissions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleCreateInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError("Please specify recipient's email address.");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      const res = await api.createInvitation({
        recipientEmail: email,
        reportId,
        reportType,
        permissions,
        expiresInHours: expiryHours,
      });
      setCreatedLink(res.invitationLink);
      setInvitationId(res.invitationId);
    } catch (err: any) {
      setError(err.message || "Failed to create family share invitation.");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (createdLink) {
      navigator.clipboard.writeText(createdLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const shareOnWhatsApp = async () => {
    if (!createdLink || !invitationId) return;
    setWhatsappLoading(true);
    setWhatsappStatus(null);
    try {
      const result = await api.shareInvitationViaWhatsApp({
        invitationId,
        invitationLink: createdLink,
        recipientPhone: phone,
      });
      setWhatsappStatus(result.message || "The WhatsApp workflow accepted the invitation.");
    } catch (err: any) {
      setWhatsappStatus(err.message || "The WhatsApp workflow could not accept the invitation.");
    } finally {
      setWhatsappLoading(false);
    }
  };

  const shareByEmail = () => {
    if (!createdLink) return;
    const subject = encodeURIComponent(`Family report invitation: ${reportTitle || "Loan report"}`);
    const body = encodeURIComponent(
      `I am sharing a report with you securely. Please sign in with ${email} to accept this invitation:\n\n${createdLink}`
    );
    window.location.href = `mailto:${email}?subject=${subject}&body=${body}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
      <div
        className="max-h-[calc(100vh-2rem)] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-6 shadow-xl border border-slate-200"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-start justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="rounded-lg bg-teal-50 p-2 text-teal-700">
              <Users className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900">Share with Family Member</h3>
              <p className="text-xs text-slate-500">Consent-First Granular Permission Control</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {!createdLink ? (
          <form onSubmit={handleCreateInvitation} className="mt-4 space-y-4">
            {error && (
              <div className="flex items-start gap-2 rounded-lg bg-red-50 p-3 text-xs text-red-700 border border-red-200">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Family Member's Email Address
              </label>
              <input
                type="email"
                required
                placeholder="spouse@family.example or parent@family.example"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              />
              <span className="text-[11px] text-slate-400">
                The recipient must log in with this exact email to accept access.
              </span>
            </div>

            {/* Granular Permission Checklist (All default OFF) */}
            <div className="rounded-lg bg-slate-50 p-3.5 border border-slate-200/80 space-y-2.5">
              <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                <Lock className="h-3.5 w-3.5 text-slate-500" />
                Select Permitted Fields (Default is Strictly Private)
              </span>

              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={permissions.shareSummary}
                  onChange={() => toggle("shareSummary")}
                  className="mt-0.5 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <div>
                  <span className="text-xs font-medium text-slate-800 block">Share Summary</span>
                  <span className="text-[11px] text-slate-500 block">
                    Allow recipient to see the plain-language executive summary assessment.
                  </span>
                </div>
              </label>

              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={permissions.shareFindings}
                  onChange={() => toggle("shareFindings")}
                  className="mt-0.5 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <div>
                  <span className="text-xs font-medium text-slate-800 block">Share Findings</span>
                  <span className="text-[11px] text-slate-500 block">
                    Allow recipient to view categorized overlooked charges and lender questions.
                  </span>
                </div>
              </label>

              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={permissions.shareFinancialAmounts}
                  onChange={() => toggle("shareFinancialAmounts")}
                  className="mt-0.5 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <div>
                  <span className="text-xs font-medium text-slate-800 block">Share Financial Figures</span>
                  <span className="text-[11px] text-slate-500 block">
                    Allow recipient to see exact loan amount, interest rate, EMI, and rupee figures. (If off, figures are replaced with [Private Amount]).
                  </span>
                </div>
              </label>

              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={permissions.shareSourceExcerpts}
                  onChange={() => toggle("shareSourceExcerpts")}
                  className="mt-0.5 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <div>
                  <span className="text-xs font-medium text-slate-800 block">Share Source Excerpts</span>
                  <span className="text-[11px] text-slate-500 block">
                    Allow recipient to view verbatim quoted clauses and section citations.
                  </span>
                </div>
              </label>

              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={permissions.shareOriginalDocument}
                  onChange={() => toggle("shareOriginalDocument")}
                  className="mt-0.5 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <div>
                  <span className="text-xs font-medium text-slate-800 block">Share Original Document File</span>
                  <span className="text-[11px] text-slate-500 block">
                    Allow recipient to download the raw PDF or DOCX file.
                  </span>
                </div>
              </label>
            </div>

            <div className="rounded-lg border border-teal-100 bg-teal-50/40 p-3 space-y-1">
              <span className="text-[11px] font-semibold text-teal-900">Recipient preview</span>
              {describeSharePreview(permissions).map((line) => (
                <p key={line} className="text-[11px] text-teal-900/80">
                  {line}
                </p>
              ))}
            </div>

            {/* Expiry Selector */}
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Link Expiration
              </label>
              <select
                value={expiryHours}
                onChange={(e) => setExpiryHours(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-xs bg-white text-slate-700 focus:border-teal-500 focus:outline-none"
              >
                <option value={24}>Expires in 24 hours</option>
                <option value={72}>Expires in 3 days (72 hours)</option>
                <option value={168}>Expires in 7 days</option>
                <option value={720}>Expires in 30 days</option>
              </select>
            </div>

            <div className="rounded-lg border border-teal-200 bg-teal-50/60 p-3 text-[11px] text-teal-900">
              <b>Step 1:</b> Create the secure invitation below. <b>Step 2:</b> On the confirmation screen, press <b>Share in WhatsApp</b> to send it.
            </div>

            {/* Permanent download warning */}
            <div className="rounded-lg bg-amber-50 p-3 text-[11px] text-amber-800 border border-amber-200 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
              <span>
                <b>Important:</b> You can revoke access at any moment, which immediately blocks online viewing and exports. However, revocation cannot erase files or screenshots already downloaded by a recipient.
              </span>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-1.5 rounded-lg bg-teal-600 px-4 py-2 text-xs font-medium text-white hover:bg-teal-700 transition-colors shadow-sm disabled:opacity-50"
              >
                <Share2 className="h-4 w-4" />
                {loading ? "Generating Secure Link..." : "Create Secure Invitation"}
              </button>
            </div>
          </form>
        ) : (
          <div className="mt-4 space-y-4">
            <div className="rounded-lg bg-emerald-50 p-4 border border-emerald-200 text-center">
              <span className="text-xs font-semibold text-emerald-800 block mb-1">
                Invitation Created Securely!
              </span>
              <p className="text-xs text-emerald-700">
                Only <b>{email}</b> can accept this invitation using an authenticated account.
              </p>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                One-Time Acceptance Link
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={createdLink}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-mono text-slate-700"
                />
                <button
                  onClick={copyToClipboard}
                  className="flex items-center gap-1 rounded-lg bg-teal-600 px-3 py-2 text-xs font-medium text-white hover:bg-teal-700 transition-colors shrink-0"
                >
                  {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                WhatsApp Number (include country code)
              </label>
              <input
                type="tel"
                required
                placeholder="919876543210"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              />
              <span className="text-[11px] text-slate-400">
                This number is sent only from the backend to your private n8n workflow.
              </span>
            </div>

            <div className="rounded-lg border border-emerald-200 bg-emerald-50/60 p-3">
              <p className="text-[11px] font-semibold text-emerald-900">Send this invitation in WhatsApp</p>
              <p className="mt-1 text-[11px] text-emerald-800">
                The backend sends safe invitation metadata to the n8n workflow. The recipient must still sign in with the invited email.
              </p>
              <button
                type="button"
                onClick={shareOnWhatsApp}
                disabled={whatsappLoading || !phone.trim()}
                className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-[#128C7E] px-3 py-2 text-xs font-semibold text-white hover:bg-[#075E54] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <MessageCircle className="h-4 w-4" />
                {whatsappLoading ? "Sending to WhatsApp Workflow..." : "Share via WhatsApp"}
              </button>
              {whatsappStatus && (
                <p className="mt-2 text-[11px] text-emerald-800" role="status">{whatsappStatus}</p>
              )}
            </div>

            <button
              type="button"
              onClick={shareByEmail}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              <Mail className="h-4 w-4" />
              Share via Email
            </button>

            <div className="flex justify-end pt-2">
              <button
                onClick={onClose}
                className="rounded-lg bg-slate-100 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-200"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
