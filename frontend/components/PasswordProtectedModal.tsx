"use client";

import React from "react";
import { Lock, X } from "lucide-react";

interface PasswordProtectedModalProps {
  isOpen: boolean;
  onClose: () => void;
  message?: string;
}

export function PasswordProtectedModal({ isOpen, onClose, message }: PasswordProtectedModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl border border-slate-200 space-y-4" role="dialog">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2.5">
            <div className="rounded-lg bg-amber-50 p-2 text-amber-700">
              <Lock className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900">Password-protected PDF detected</h3>
              <p className="text-xs text-slate-500">The local parser cannot unlock bank-encrypted files.</p>
            </div>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100">
            <X className="h-5 w-5" />
          </button>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed">
          {message ||
            "This PDF is password-protected. Unlock it in your PDF viewer, then save an unprotected copy before uploading."}
        </p>
        <ol className="list-decimal pl-5 space-y-1 text-[11px] text-slate-600">
          <li>Open the sanction letter in Chrome, Edge, or Adobe Reader and enter the password.</li>
          <li>Press Ctrl + P and choose “Save as PDF”.</li>
          <li>Upload the newly saved, unlocked copy here.</li>
        </ol>
        <div className="flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg bg-teal-600 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-700"
          >
            Understood
          </button>
        </div>
      </div>
    </div>
  );
}
