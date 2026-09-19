"use client";

import React, { useState, useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Calendar, ChevronLeft, ChevronRight } from "lucide-react";
import { AmortizationMonth } from "@/types";
import { formatINR } from "@/lib/utils";

interface AmortizationScheduleProps {
  schedule: AmortizationMonth[];
}

export function AmortizationSchedule({ schedule }: AmortizationScheduleProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 12; // 1 year per page

  // Sample data for chart (every 6th or 12th month if long tenure)
  const chartData = useMemo(() => {
    if (!schedule || schedule.length === 0) return [];
    const step = schedule.length > 60 ? 6 : 1;
    const sampled = [];
    for (let i = 0; i < schedule.length; i += step) {
      const item = schedule[i];
      sampled.push({
        name: `M${item.month}`,
        remainingPrincipal: Number(item.remainingPrincipal),
        interestPaid: Number(item.interestPayment),
        principalPaid: Number(item.principalPayment),
      });
    }
    return sampled;
  }, [schedule]);

  if (!schedule || schedule.length === 0) return null;

  const totalPages = Math.ceil(schedule.length / pageSize);
  const displayedRows = schedule.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-6">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-teal-50 p-2 text-teal-700">
            <Calendar className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Amortization Trajectory</h3>
            <p className="text-xs text-slate-500">
              Outstanding loan balance and principal payoff progression
            </p>
          </div>
        </div>
        <span className="text-xs font-mono text-slate-500">
          Total: {schedule.length} Months ({Math.floor(schedule.length / 12)} Yrs)
        </span>
      </div>

      {/* Chart */}
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorPrincipal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0d9488" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#64748b" }} />
            <YAxis
              tick={{ fontSize: 11, fill: "#64748b" }}
              tickFormatter={(val) => `₹${(val / 100000).toFixed(1)}L`}
            />
            <Tooltip
              formatter={(value: any) => [formatINR(value), "Remaining Principal"]}
              contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", fontSize: "12px", border: "1px solid #e2e8f0" }}
            />
            <Area
              type="monotone"
              dataKey="remainingPrincipal"
              stroke="#0d9488"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorPrincipal)"
              name="Remaining Principal"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Paginated Schedule Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-600">
          <span>
            Showing Year {Math.ceil(displayedRows[0]?.month / 12)} (Months {displayedRows[0]?.month}–{displayedRows[displayedRows.length - 1]?.month})
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="rounded p-1 text-slate-500 hover:bg-slate-100 disabled:opacity-30"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="font-mono text-xs px-2">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="rounded p-1 text-slate-500 hover:bg-slate-100 disabled:opacity-30"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3">Month</th>
                <th className="py-2.5 px-3">EMI Payment</th>
                <th className="py-2.5 px-3">Principal Portion</th>
                <th className="py-2.5 px-3">Interest Portion</th>
                <th className="py-2.5 px-3">Remaining Balance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {displayedRows.map((row) => (
                <tr key={row.month} className="hover:bg-slate-50/60">
                  <td className="py-2 px-3 text-slate-600">Month {row.month}</td>
                  <td className="py-2 px-3 font-medium text-slate-900">{formatINR(row.emi)}</td>
                  <td className="py-2 px-3 text-emerald-700">+{formatINR(row.principalPayment)}</td>
                  <td className="py-2 px-3 text-amber-700">-{formatINR(row.interestPayment)}</td>
                  <td className="py-2 px-3 text-slate-800">{formatINR(row.remainingPrincipal)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
