from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class LoanCalculationRequest(BaseModel):
    loanPrincipal: Decimal = Field(..., gt=0, description="Base principal sanction amount")
    annualInterestRatePercent: Decimal = Field(..., ge=0, description="Annual nominal interest rate percentage")
    tenureMonths: int = Field(..., gt=0, le=480, description="Tenure in months")
    upfrontCharges: Decimal = Field(default=Decimal("0.00"), ge=0, description="Fees paid upfront out-of-pocket")
    financedCharges: Decimal = Field(default=Decimal("0.00"), ge=0, description="Fees capitalized into loan principal")
    deductedCharges: Decimal = Field(default=Decimal("0.00"), ge=0, description="Fees deducted at disbursement")
    optionalInsurancePremium: Decimal = Field(default=Decimal("0.00"), ge=0, description="Optional insurance cost")
    includeInsuranceInLoan: bool = Field(default=False, description="Whether insurance is financed into principal")


class AmortizationMonth(BaseModel):
    month: int
    emi: Decimal
    principalPayment: Decimal
    interestPayment: Decimal
    remainingPrincipal: Decimal


class RateScenarioComparison(BaseModel):
    scenarioLabel: str
    annualRatePercent: Decimal
    monthlyEmi: Decimal
    totalInterest: Decimal
    totalOutflow: Decimal
    monthlyEmiDifference: Decimal
    assumptions: str


class LoanCalculationResponse(BaseModel):
    monthlyEmi: Decimal
    totalScheduledRepayments: Decimal
    totalInterest: Decimal
    knownAdditionalCharges: Decimal
    estimatedTotalBorrowerOutflow: Decimal
    estimatedNetDisbursement: Decimal
    totalFinancedPrincipal: Decimal
    rateScenarios: List[RateScenarioComparison]
    amortizationSchedule: List[AmortizationMonth]
    assumptionsAndLimitations: List[str]
