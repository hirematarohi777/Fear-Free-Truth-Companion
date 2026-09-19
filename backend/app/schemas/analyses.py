from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FieldStatus(str, Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    CONFLICTING = "conflicting"


class EvidenceQuality(str, Enum):
    CLEAR = "clear"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


class Severity(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ChargeCategory(str, Enum):
    EXPLICITLY_DISCLOSED = "Explicitly disclosed charge"
    EASILY_OVERLOOKED = "Easily overlooked charge"
    CONDITIONAL = "Conditional charge"
    UNCLEAR_OR_MISSING = "Unclear or missing disclosure"
    CONFLICTING_TERMS = "Conflicting financial terms"


class FinancialField(BaseModel):
    fieldName: str
    value: Optional[str] = None
    numericValue: Optional[float] = None
    unitOrCurrency: Optional[str] = None
    sourceReference: Optional[str] = None
    supportingQuote: Optional[str] = None
    status: FieldStatus = FieldStatus.NOT_FOUND
    notes: Optional[str] = None


class ChargeFinding(BaseModel):
    id: str
    title: str
    category: ChargeCategory
    severity: Severity
    plainLanguageExplanation: str
    amountOrCalculationBasis: Optional[str] = None
    conditionsUnderWhichItApplies: Optional[str] = None
    supportingQuote: Optional[str] = None
    sourceReference: Optional[str] = None
    evidenceQuality: EvidenceQuality = EvidenceQuality.PARTIAL
    recommendedQuestionForLender: str


class ExtractedLoanTerms(BaseModel):
    lenderName: FinancialField
    borrowerName: FinancialField
    loanAmount: FinancialField
    amountDisbursed: FinancialField
    interestRate: FinancialField
    interestStructure: FinancialField  # fixed, floating, or hybrid
    benchmarkAndSpread: FinancialField
    loanTenureMonths: FinancialField
    emi: FinancialField
    processingFee: FinancialField
    administrativeFee: FinancialField
    legalValuationCharges: FinancialField
    insurancePremium: FinancialField
    taxesOnFees: FinancialField
    prepaymentForeclosureConditions: FinancialField
    latePaymentBounceCharges: FinancialField
    rateResetConditions: FinancialField
    balloonPayments: FinancialField
    bundledOptionalProducts: FinancialField
    cancellationRefundTerms: FinancialField


class LoanAnalysisResponse(BaseModel):
    id: str
    documentId: str
    ownerId: str
    status: str
    extractedTerms: ExtractedLoanTerms
    findings: List[ChargeFinding]
    calculations: Optional[Dict[str, Any]] = None
    evidenceQuality: EvidenceQuality
    limitations: List[str]
    modelName: str
    promptVersion: str
    analysisVersion: str
    summaryStatement: str
    createdAt: datetime
    completedAt: Optional[datetime] = None
