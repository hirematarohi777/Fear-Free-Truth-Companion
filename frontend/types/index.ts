export type FieldStatus = "found" | "not_found" | "ambiguous" | "conflicting";
export type EvidenceQuality = "clear" | "partial" | "insufficient";
export type Severity = "informational" | "low" | "medium" | "high";
export type ChargeCategory =
  | "Explicitly disclosed charge"
  | "Easily overlooked charge"
  | "Conditional charge"
  | "Unclear or missing disclosure"
  | "Conflicting financial terms";

export interface FinancialField {
  fieldName: string;
  value?: string | null;
  numericValue?: number | null;
  unitOrCurrency?: string | null;
  sourceReference?: string | null;
  supportingQuote?: string | null;
  status: FieldStatus;
  notes?: string | null;
}

export interface ChargeFinding {
  id: string;
  title: string;
  category: ChargeCategory;
  severity: Severity;
  plainLanguageExplanation: string;
  amountOrCalculationBasis?: string | null;
  conditionsUnderWhichItApplies?: string | null;
  supportingQuote?: string | null;
  sourceReference?: string | null;
  evidenceQuality: EvidenceQuality;
  recommendedQuestionForLender: string;
}

export interface ExtractedLoanTerms {
  lenderName: FinancialField;
  borrowerName: FinancialField;
  loanAmount: FinancialField;
  amountDisbursed: FinancialField;
  interestRate: FinancialField;
  interestStructure: FinancialField;
  benchmarkAndSpread: FinancialField;
  loanTenureMonths: FinancialField;
  emi: FinancialField;
  processingFee: FinancialField;
  administrativeFee: FinancialField;
  legalValuationCharges: FinancialField;
  insurancePremium: FinancialField;
  taxesOnFees: FinancialField;
  prepaymentForeclosureConditions: FinancialField;
  latePaymentBounceCharges: FinancialField;
  rateResetConditions: FinancialField;
  balloonPayments: FinancialField;
  bundledOptionalProducts: FinancialField;
  cancellationRefundTerms: FinancialField;
}

export interface RateScenarioComparison {
  scenarioLabel: string;
  annualRatePercent: number;
  monthlyEmi: number;
  totalInterest: number;
  totalOutflow: number;
  monthlyEmiDifference: number;
  assumptions: string;
}

export interface AmortizationMonth {
  month: number;
  emi: number;
  principalPayment: number;
  interestPayment: number;
  remainingPrincipal: number;
}

export interface LoanCalculationResponse {
  monthlyEmi: number;
  totalScheduledRepayments: number;
  totalInterest: number;
  knownAdditionalCharges: number;
  estimatedTotalBorrowerOutflow: number;
  estimatedNetDisbursement: number;
  totalFinancedPrincipal: number;
  rateScenarios: RateScenarioComparison[];
  amortizationSchedule: AmortizationMonth[];
  assumptionsAndLimitations: string[];
}

export interface LoanAnalysisReport {
  id: string;
  documentId: string;
  ownerId: string;
  status: string;
  extractedTerms: ExtractedLoanTerms;
  findings: ChargeFinding[];
  calculations?: LoanCalculationResponse | null;
  evidenceQuality: EvidenceQuality;
  limitations: string[];
  modelName: string;
  summaryStatement: string;
  createdAt: string;
  completedAt?: string | null;
  isSharedView?: boolean;
  grantedPermissions?: SharingPermissions;
}

export type CheckStatus = "concern" | "no_concern_found" | "inconclusive" | "not_checked";
export type OverallOutcome =
  | "Significant risk indicators found"
  | "Some concerns require verification"
  | "No major indicators found in completed checks"
  | "Insufficient evidence to assess";

export type IdentityVerificationStatus =
  | "Entity matched; website ownership corroborated"
  | "Entity matched; website ownership unverified"
  | "Entity match uncertain"
  | "Not checked";

export interface SingleUrlCheckItem {
  checkName: string;
  status: CheckStatus;
  explanation: string;
  evidenceUrlOrQuote?: string | null;
  timestamp: string;
  recommendedNextStep: string;
}

export interface UrlCheckReport {
  id: string;
  ownerId: string;
  submittedUrl: string;
  finalUrl: string;
  redirectChain: string[];
  claimedEntity?: string | null;
  overallOutcome: OverallOutcome;
  identityVerificationStatus: IdentityVerificationStatus;
  checks: SingleUrlCheckItem[];
  evidence: Record<string, any>;
  limitations: string[];
  modelSummary?: string | null;
  createdAt: string;
  completedAt?: string | null;
}

export interface SharingPermissions {
  shareSummary: boolean;
  shareFindings: boolean;
  shareFinancialAmounts: boolean;
  shareSourceExcerpts: boolean;
  shareOriginalDocument: boolean;
}

export interface UserProfile {
  id: string;
  email: string;
  displayName: string;
  createdAt: string;
}

export interface JobStatusResponse {
  id: string;
  type: string;
  resourceId: string;
  status: "queued" | "processing" | "completed" | "completed_with_limitations" | "failed" | "cancelled";
  stage: string;
  attemptCount: number;
  errorCode?: string | null;
  resultSummary?: Record<string, any> | null;
}
