from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import List, Tuple
from app.schemas.calculations import (
    LoanCalculationRequest,
    LoanCalculationResponse,
    RateScenarioComparison,
    AmortizationMonth
)

# Set high precision for intermediate financial calculations
getcontext().prec = 28

TWO_PLACES = Decimal("0.01")


def round_curr(val: Decimal) -> Decimal:
    """Round to two decimal places (currency standard)."""
    return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_emi(principal: Decimal, annual_rate_percent: Decimal, tenure_months: int) -> Decimal:
    """
    Calculate monthly EMI using reducing balance formula:
    EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
    For r == 0: EMI = P / n
    """
    if tenure_months <= 0:
        raise ValueError("Tenure must be greater than zero months.")
    if principal < Decimal("0"):
        raise ValueError("Principal cannot be negative.")

    if annual_rate_percent == Decimal("0"):
        return round_curr(principal / Decimal(str(tenure_months)))

    # Monthly nominal rate
    r = annual_rate_percent / Decimal("12") / Decimal("100")
    n = Decimal(str(tenure_months))

    # (1 + r)^n
    factor = (Decimal("1") + r) ** n
    emi = principal * (r * factor) / (factor - Decimal("1"))
    return round_curr(emi)


def generate_amortization_schedule(
    financed_principal: Decimal,
    annual_rate_percent: Decimal,
    tenure_months: int,
    monthly_emi: Decimal
) -> List[AmortizationMonth]:
    """Generate month-by-month amortization schedule with zero-drift reconciliation."""
    schedule: List[AmortizationMonth] = []
    remaining = financed_principal
    
    if annual_rate_percent == Decimal("0"):
        monthly_principal = round_curr(financed_principal / Decimal(str(tenure_months)))
        for m in range(1, tenure_months + 1):
            if m == tenure_months:
                p_pay = remaining
            else:
                p_pay = min(monthly_principal, remaining)
            remaining = max(Decimal("0.00"), remaining - p_pay)
            schedule.append(AmortizationMonth(
                month=m,
                emi=p_pay,
                principalPayment=p_pay,
                interestPayment=Decimal("0.00"),
                remainingPrincipal=round_curr(remaining)
            ))
        return schedule

    r = annual_rate_percent / Decimal("12") / Decimal("100")

    for m in range(1, tenure_months + 1):
        if remaining <= Decimal("0.00"):
            schedule.append(AmortizationMonth(
                month=m,
                emi=Decimal("0.00"),
                principalPayment=Decimal("0.00"),
                interestPayment=Decimal("0.00"),
                remainingPrincipal=Decimal("0.00")
            ))
            continue

        interest = round_curr(remaining * r)
        
        if m == tenure_months:
            # Final month balances out any fractional rounding
            principal_pay = remaining
            actual_emi = principal_pay + interest
            remaining = Decimal("0.00")
        else:
            principal_pay = monthly_emi - interest
            if principal_pay > remaining:
                principal_pay = remaining
                actual_emi = principal_pay + interest
                remaining = Decimal("0.00")
            else:
                actual_emi = monthly_emi
                remaining = round_curr(remaining - principal_pay)

        schedule.append(AmortizationMonth(
            month=m,
            emi=round_curr(actual_emi),
            principalPayment=round_curr(principal_pay),
            interestPayment=round_curr(interest),
            remainingPrincipal=round_curr(remaining)
        ))

    return schedule


def compute_loan_details(req: LoanCalculationRequest) -> LoanCalculationResponse:
    """Compute complete loan breakdown, rate scenarios, and assumptions."""
    # 1. Financed charges are added to sanction principal
    total_financed_principal = req.loanPrincipal + req.financedCharges
    if req.includeInsuranceInLoan:
        total_financed_principal += req.optionalInsurancePremium

    # 2. Base EMI calculation
    base_emi = calculate_emi(total_financed_principal, req.annualInterestRatePercent, req.tenureMonths)
    total_repayments = round_curr(base_emi * Decimal(str(req.tenureMonths)))
    total_interest = max(Decimal("0.00"), round_curr(total_repayments - total_financed_principal))

    # 3. Known additional charges breakdown
    total_additional_charges = req.upfrontCharges + req.financedCharges + req.deductedCharges
    if req.optionalInsurancePremium > Decimal("0") and not req.includeInsuranceInLoan:
        total_additional_charges += req.optionalInsurancePremium

    # 4. Total borrower outflow: what the borrower actually pays across the lifetime
    total_outflow = total_repayments + req.upfrontCharges
    if req.optionalInsurancePremium > Decimal("0") and not req.includeInsuranceInLoan:
        total_outflow += req.optionalInsurancePremium

    # 5. Net disbursement: sanction principal minus charges deducted at source
    estimated_net_disbursement = max(Decimal("0.00"), round_curr(req.loanPrincipal - req.deductedCharges))

    # 6. Rate-change scenarios (+0%, +1%, +2%)
    scenarios: List[RateScenarioComparison] = []
    increments = [
        ("Current Rate", Decimal("0.0")),
        ("Rate + 1.00% Scenario", Decimal("1.0")),
        ("Rate + 2.00% Scenario", Decimal("2.0"))
    ]

    for label, bump in increments:
        scen_rate = req.annualInterestRatePercent + bump
        scen_emi = calculate_emi(total_financed_principal, scen_rate, req.tenureMonths)
        scen_repayments = round_curr(scen_emi * Decimal(str(req.tenureMonths)))
        scen_interest = max(Decimal("0.00"), round_curr(scen_repayments - total_financed_principal))
        scen_outflow = scen_repayments + req.upfrontCharges
        if req.optionalInsurancePremium > Decimal("0") and not req.includeInsuranceInLoan:
            scen_outflow += req.optionalInsurancePremium

        diff = scen_emi - base_emi
        scenarios.append(RateScenarioComparison(
            scenarioLabel=label,
            annualRatePercent=scen_rate,
            monthlyEmi=scen_emi,
            totalInterest=scen_interest,
            totalOutflow=scen_outflow,
            monthlyEmiDifference=diff,
            assumptions="Tenure kept fixed at " + str(req.tenureMonths) + " months. In practice, lenders may adjust tenure or EMI."
        ))

    # 7. Amortization schedule
    schedule = generate_amortization_schedule(
        total_financed_principal,
        req.annualInterestRatePercent,
        req.tenureMonths,
        base_emi
    )

    # 8. Documented assumptions
    assumptions = [
        "Reducing balance monthly rest calculation method applied.",
        "Tenure is assumed to remain constant across rate-change illustrations.",
        "Financed charges increase the loan principal and attract interest over tenure.",
        "Deducted charges are subtracted from sanction amount at the time of disbursement.",
        "Illustrative only for floating-rate loans; resets and benchmark changes will alter future cash outflows.",
        "This calculation does not constitute a statutory or regulatory APR unless official disclosure guidelines are fulfilled."
    ]

    return LoanCalculationResponse(
        monthlyEmi=base_emi,
        totalScheduledRepayments=total_repayments,
        totalInterest=total_interest,
        knownAdditionalCharges=round_curr(total_additional_charges),
        estimatedTotalBorrowerOutflow=round_curr(total_outflow),
        estimatedNetDisbursement=estimated_net_disbursement,
        totalFinancedPrincipal=round_curr(total_financed_principal),
        rateScenarios=scenarios,
        amortizationSchedule=schedule,
        assumptionsAndLimitations=assumptions
    )
