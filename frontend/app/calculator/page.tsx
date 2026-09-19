"use client";

import React, { useState, useEffect } from "react";
import {
  Calculator,
  Info,
  TrendingUp,
  RotateCcw,
  CheckCircle2,
  DollarSign,
  ShieldAlert,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { RateScenarioTable } from "@/components/RateScenarioTable";
import { AmortizationSchedule } from "@/components/AmortizationSchedule";
import { api } from "@/lib/api";
import { formatINR, formatPercent } from "@/lib/utils";
import { LoanCalculationResponse } from "@/types";

export default function CalculatorPage() {
  const [user, setUser] = useState<any>(null);

  // Form Inputs
  const [principal, setPrincipal] = useState<number>(4000000); // ₹40 Lakhs
  const [rate, setRate] = useState<number>(8.5); // 8.5%
  const [tenureYears, setTenureYears] = useState<number>(20); // 20 years = 240 months
  const [upfrontCharges, setUpfrontCharges] = useState<number>(20000); // 0.5%
  const [financedCharges, setFinancedCharges] = useState<number>(0);
  const [deductedCharges, setDeductedCharges] = useState<number>(5000);
  const [insurance, setInsurance] = useState<number>(0);
  const [includeInsuranceInLoan, setIncludeInsuranceInLoan] = useState<boolean>(false);

  const [result, setResult] = useState<LoanCalculationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getMe().then(setUser).catch(() => {});
  }, []);

  const runCalculation = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        loanPrincipal: String(principal),
        annualInterestRatePercent: String(rate),
        tenureMonths: tenureYears * 12,
        upfrontCharges: String(upfrontCharges),
        financedCharges: String(financedCharges),
        deductedCharges: String(deductedCharges),
        optionalInsurancePremium: String(insurance),
        includeInsuranceInLoan: includeInsuranceInLoan,
      };
      const res = await api.calculateLoan(payload);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to calculate repayment schedule.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runCalculation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    principal,
    rate,
    tenureYears,
    upfrontCharges,
    financedCharges,
    deductedCharges,
    insurance,
    includeInsuranceInLoan,
  ]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar user={user} />

      <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Truth & Clarity Loan Calculator</h1>
          <p className="text-xs text-slate-500">
            Authoritative Decimal-based reducing balance calculations. Transparently distinguish financed fees from out-of-pocket costs.
          </p>
        </div>

        {error && (
          <div className="rounded-xl bg-red-50 p-4 text-xs text-red-700 border border-red-200">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls Column */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
            <h2 className="text-sm font-semibold text-slate-900 border-b border-slate-100 pb-3 flex items-center gap-2">
              <Calculator className="h-4 w-4 text-teal-600" />
              Loan Parameters
            </h2>

            {/* Principal */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <label className="font-medium text-slate-700">Sanctioned Principal</label>
                <span className="font-bold text-slate-900 font-mono">{formatINR(principal)}</span>
              </div>
              <input
                type="range"
                min={500000}
                max={20000000}
                step={100000}
                value={principal}
                onChange={(e) => setPrincipal(Number(e.target.value))}
                className="w-full accent-teal-600 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>₹5 Lakhs</span>
                <span>₹2 Crores</span>
              </div>
            </div>

            {/* Interest Rate */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <label className="font-medium text-slate-700">Annual Interest Rate</label>
                <span className="font-bold text-slate-900 font-mono">{formatPercent(rate)}</span>
              </div>
              <input
                type="range"
                min={6.0}
                max={16.0}
                step={0.05}
                value={rate}
                onChange={(e) => setRate(Number(e.target.value))}
                className="w-full accent-teal-600 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>6.0%</span>
                <span>16.0%</span>
              </div>
            </div>

            {/* Tenure */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <label className="font-medium text-slate-700">Repayment Tenure</label>
                <span className="font-bold text-slate-900 font-mono">
                  {tenureYears} Years ({tenureYears * 12} Months)
                </span>
              </div>
              <input
                type="range"
                min={5}
                max={30}
                step={1}
                value={tenureYears}
                onChange={(e) => setTenureYears(Number(e.target.value))}
                className="w-full accent-teal-600 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>5 Yrs</span>
                <span>30 Yrs</span>
              </div>
            </div>

            {/* Additional Charges Section */}
            <div className="border-t border-slate-100 pt-4 space-y-3 text-xs">
              <span className="font-semibold text-slate-800 block">
                Additional Fees & Charges Breakdown
              </span>

              <div>
                <label className="text-[11px] text-slate-600 block mb-1">
                  Upfront Fees Paid Out-of-Pocket (₹)
                </label>
                <input
                  type="number"
                  min={0}
                  value={upfrontCharges}
                  onChange={(e) => setUpfrontCharges(Number(e.target.value))}
                  className="w-full rounded-lg border border-slate-200 px-3 py-1.5 font-mono text-xs focus:border-teal-500 focus:outline-none"
                />
                <span className="text-[10px] text-slate-400">Paid directly; does not accrue interest.</span>
              </div>

              <div>
                <label className="text-[11px] text-slate-600 block mb-1">
                  Financed Charges Added to Principal (₹)
                </label>
                <input
                  type="number"
                  min={0}
                  value={financedCharges}
                  onChange={(e) => setFinancedCharges(Number(e.target.value))}
                  className="w-full rounded-lg border border-slate-200 px-3 py-1.5 font-mono text-xs focus:border-teal-500 focus:outline-none"
                />
                <span className="text-[10px] text-slate-400">Increases loan balance and attracts interest.</span>
              </div>

              <div>
                <label className="text-[11px] text-slate-600 block mb-1">
                  Charges Deducted at Disbursement (₹)
                </label>
                <input
                  type="number"
                  min={0}
                  value={deductedCharges}
                  onChange={(e) => setDeductedCharges(Number(e.target.value))}
                  className="w-full rounded-lg border border-slate-200 px-3 py-1.5 font-mono text-xs focus:border-teal-500 focus:outline-none"
                />
                <span className="text-[10px] text-slate-400">Subtracted before bank releases funds.</span>
              </div>

              <div>
                <label className="text-[11px] text-slate-600 block mb-1">
                  Optional Insurance Policy (₹)
                </label>
                <input
                  type="number"
                  min={0}
                  value={insurance}
                  onChange={(e) => setInsurance(Number(e.target.value))}
                  className="w-full rounded-lg border border-slate-200 px-3 py-1.5 font-mono text-xs focus:border-teal-500 focus:outline-none"
                />
                <label className="flex items-center gap-1.5 mt-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeInsuranceInLoan}
                    onChange={(e) => setIncludeInsuranceInLoan(e.target.checked)}
                    className="rounded text-teal-600"
                  />
                  <span className="text-[10px] text-slate-600">Finance insurance into loan</span>
                </label>
              </div>
            </div>
          </div>

          {/* Results Overview (Right 2 Columns) */}
          <div className="lg:col-span-2 space-y-6">
            {result && (
              <>
                {/* Metric Summary Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5">
                  <div className="rounded-xl border border-teal-200 bg-teal-50/40 p-4">
                    <span className="text-xs text-teal-700 font-medium block">Monthly EMI</span>
                    <div className="text-2xl font-extrabold text-teal-900 font-mono mt-1">
                      {formatINR(result.monthlyEmi)}
                    </div>
                    <span className="text-[10px] text-teal-700">For {tenureYears * 12} months</span>
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
                    <span className="text-xs text-slate-500 font-medium block">Total Interest Payable</span>
                    <div className="text-xl font-bold text-slate-900 font-mono mt-1">
                      {formatINR(result.totalInterest)}
                    </div>
                    <span className="text-[10px] text-amber-700">
                      {( (Number(result.totalInterest) / Number(result.totalFinancedPrincipal)) * 100 ).toFixed(1)}% of principal
                    </span>
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
                    <span className="text-xs text-slate-500 font-medium block">Estimated Total Outflow</span>
                    <div className="text-xl font-bold text-slate-900 font-mono mt-1">
                      {formatINR(result.estimatedTotalBorrowerOutflow)}
                    </div>
                    <span className="text-[10px] text-slate-400">Repayments + upfront fees</span>
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
                    <span className="text-xs text-slate-500 font-medium block">Net Bank Disbursement</span>
                    <div className="text-xl font-bold text-emerald-800 font-mono mt-1">
                      {formatINR(result.estimatedNetDisbursement)}
                    </div>
                    <span className="text-[10px] text-slate-400">After deducted charges</span>
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
                    <span className="text-xs text-slate-500 font-medium block">Total Financed Principal</span>
                    <div className="text-xl font-bold text-slate-800 font-mono mt-1">
                      {formatINR(result.totalFinancedPrincipal)}
                    </div>
                    <span className="text-[10px] text-slate-400">Sanction + capitalized fees</span>
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
                    <span className="text-xs text-slate-500 font-medium block">Total Additional Charges</span>
                    <div className="text-xl font-bold text-slate-800 font-mono mt-1">
                      {formatINR(result.knownAdditionalCharges)}
                    </div>
                    <span className="text-[10px] text-slate-400">Disclosed fees total</span>
                  </div>
                </div>

                {/* Rate Scenarios Component */}
                <RateScenarioTable scenarios={result.rateScenarios} />

                {/* Amortization Chart & Schedule */}
                <AmortizationSchedule schedule={result.amortizationSchedule} />
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
