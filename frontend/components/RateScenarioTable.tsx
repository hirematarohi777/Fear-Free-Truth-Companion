"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { TrendingUp, AlertCircle, Info } from "lucide-react";
import { RateScenarioComparison } from "@/types";
import { formatINR, formatPercent } from "@/lib/utils";

interface RateScenarioTableProps {
  scenarios: RateScenarioComparison[];
}

export function RateScenarioTable({ scenarios }: RateScenarioTableProps) {
  if (!scenarios || scenarios.length === 0) return null;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
        <div className="rounded-lg bg-teal-50 p-2 text-teal-700">
          <TrendingUp className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-900">
            Floating Rate Sensitivity Scenarios (+1% & +2%)
          </h3>
          <p className="text-xs text-slate-500">
            Illustration of EMI and total borrower outflow if the external benchmark rate rises.
          </p>
        </div>
      </div>

      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={scenarios.map((scen) => ({
              name: scen.scenarioLabel,
              emi: Number(scen.monthlyEmi),
              interest: Number(scen.totalInterest),
            }))}
            margin={{ top: 8, right: 8, left: 8, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#64748b" }} />
            <YAxis tick={{ fontSize: 11, fill: "#64748b" }} tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`} />
            <Tooltip
              formatter={(value: any, name: string) => [formatINR(value), name === "emi" ? "Monthly EMI" : "Total Interest"]}
              contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", fontSize: "12px", border: "1px solid #e2e8f0" }}
            />
            <Legend />
            <Bar dataKey="emi" name="Monthly EMI" fill="#0d9488" radius={[6, 6, 0, 0]} />
            <Bar dataKey="interest" name="Total Interest" fill="#f59e0b" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        {scenarios.map((scen, idx) => {
          const isBase = idx === 0;
          return (
            <div
              key={idx}
              className={`rounded-xl p-4 border transition-all ${
                isBase
                  ? "bg-slate-50/70 border-slate-200"
                  : "bg-amber-50/30 border-amber-200 shadow-sm"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                  {scen.scenarioLabel}
                </span>
                <span
                  className={`rounded px-2 py-0.5 text-xs font-bold font-mono ${
                    isBase ? "bg-slate-200 text-slate-800" : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {formatPercent(scen.annualRatePercent)}
                </span>
              </div>

              <div className="space-y-2 pt-1">
                <div>
                  <span className="text-[11px] text-slate-500 block">Monthly EMI</span>
                  <div className="text-lg font-bold text-slate-900 font-mono">
                    {formatINR(scen.monthlyEmi)}
                  </div>
                  {!isBase && (
                    <span className="text-[11px] text-amber-700 font-medium">
                      +{formatINR(scen.monthlyEmiDifference)} / month
                    </span>
                  )}
                </div>

                <div className="pt-2 border-t border-slate-200/60 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-[11px] text-slate-500 block">Total Interest</span>
                    <span className="font-semibold text-slate-800 font-mono">
                      {formatINR(scen.totalInterest)}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 block">Total Outflow</span>
                    <span className="font-semibold text-slate-800 font-mono">
                      {formatINR(scen.totalOutflow)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Assumptions alert */}
      <div className="flex items-start gap-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-600 border border-slate-200">
        <Info className="h-4 w-4 text-teal-600 shrink-0 mt-0.5" />
        <span>
          <b>Key Assumption:</b> Tenure is kept constant across these rate-change illustrations. In practice, some Indian lenders automatically extend loan tenure instead of raising monthly EMI up to retirement age limits.
        </span>
      </div>
    </div>
  );
}
