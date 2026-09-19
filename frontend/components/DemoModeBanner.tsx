"use client";

import React from "react";
import { AlertCircle, FileCode } from "lucide-react";

interface DemoModeBannerProps {
  label?: string;
}

export function DemoModeBanner({ label = "Synthetic demonstration data — not a real lender assessment." }: DemoModeBannerProps) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-amber-50 px-4 py-2.5 text-xs text-amber-800 border border-amber-200/80 shadow-xs mb-4">
      <FileCode className="h-4 w-4 text-amber-600 shrink-0" />
      <span className="font-medium">{label}</span>
      <span className="text-[11px] text-amber-600/90 ml-auto hidden sm:inline">
        For testing and evaluation only
      </span>
    </div>
  );
}
