import pytest
from decimal import Decimal
from app.services.calculations.loan_calculator import (
    calculate_emi,
    compute_loan_details,
    generate_amortization_schedule
)
from app.schemas.calculations import LoanCalculationRequest


def test_standard_reducing_balance_emi():
    """
    Standard test case: ₹40,00,000 at 8.5% p.a. for 240 months (20 years).
    P = 4,000,000
    r = 8.5 / 12 / 100 = 0.007083333333333333...
    n = 240
    Expected EMI is approximately ₹34,713.00
    """
    principal = Decimal("4000000.00")
    annual_rate = Decimal("8.50")
    tenure_months = 240

    emi = calculate_emi(principal, annual_rate, tenure_months)
    assert emi == Decimal("34712.93")

    req = LoanCalculationRequest(
        loanPrincipal=principal,
        annualInterestRatePercent=annual_rate,
        tenureMonths=tenure_months,
        upfrontCharges=Decimal("20000.00"),
        financedCharges=Decimal("0.00"),
        deductedCharges=Decimal("5000.00")
    )
    res = compute_loan_details(req)
    assert res.monthlyEmi > Decimal("34000.00")
    assert res.totalScheduledRepayments > principal
    assert res.totalInterest > Decimal("4000000.00")
    assert res.estimatedNetDisbursement == Decimal("3995000.00")  # 40L minus 5k deducted
    assert len(res.rateScenarios) == 3
    assert len(res.amortizationSchedule) == 240


def test_zero_interest_loan():
    """
    Zero-interest loan calculation:
    EMI = P / n exactly without division by zero.
    """
    principal = Decimal("120000.00")
    annual_rate = Decimal("0.00")
    tenure_months = 12

    emi = calculate_emi(principal, annual_rate, tenure_months)
    assert emi == Decimal("10000.00")

    req = LoanCalculationRequest(
        loanPrincipal=principal,
        annualInterestRatePercent=annual_rate,
        tenureMonths=tenure_months
    )
    res = compute_loan_details(req)
    assert res.monthlyEmi == Decimal("10000.00")
    assert res.totalInterest == Decimal("0.00")
    assert res.totalScheduledRepayments == Decimal("120000.00")


def test_financed_fees_vs_upfront_fees_distinction():
    """
    Financed fees increase sanctioned principal.
    Upfront fees do NOT increase principal or interest, but increase total outflow.
    Deducted fees do NOT increase principal, but decrease net disbursement.
    """
    base_p = Decimal("1000000.00")
    rate = Decimal("10.00")
    tenure = 120

    # Scenario A: No fees
    base_res = compute_loan_details(LoanCalculationRequest(
        loanPrincipal=base_p,
        annualInterestRatePercent=rate,
        tenureMonths=tenure
    ))

    # Scenario B: Financed fee ₹50,000
    financed_res = compute_loan_details(LoanCalculationRequest(
        loanPrincipal=base_p,
        annualInterestRatePercent=rate,
        tenureMonths=tenure,
        financedCharges=Decimal("50000.00")
    ))

    # Financed fees increase monthly EMI and interest
    assert financed_res.monthlyEmi > base_res.monthlyEmi
    assert financed_res.totalInterest > base_res.totalInterest
    assert financed_res.totalFinancedPrincipal == Decimal("1050000.00")

    # Scenario C: Upfront fee ₹50,000
    upfront_res = compute_loan_details(LoanCalculationRequest(
        loanPrincipal=base_p,
        annualInterestRatePercent=rate,
        tenureMonths=tenure,
        upfrontCharges=Decimal("50000.00")
    ))

    # Upfront fees keep monthly EMI identical to base, but increase total outflow
    assert upfront_res.monthlyEmi == base_res.monthlyEmi
    assert upfront_res.totalInterest == base_res.totalInterest
    assert upfront_res.estimatedTotalBorrowerOutflow == base_res.estimatedTotalBorrowerOutflow + Decimal("50000.00")


def test_rate_change_scenarios_keep_tenure_fixed():
    """Rate scenarios (+1%, +2%) should accurately compute increased EMI with constant tenure."""
    req = LoanCalculationRequest(
        loanPrincipal=Decimal("2500000.00"),
        annualInterestRatePercent=Decimal("8.00"),
        tenureMonths=180
    )
    res = compute_loan_details(req)

    scenarios = res.rateScenarios
    assert len(scenarios) == 3
    base_scen, bump1, bump2 = scenarios

    assert base_scen.annualRatePercent == Decimal("8.00")
    assert bump1.annualRatePercent == Decimal("9.00")
    assert bump2.annualRatePercent == Decimal("10.00")

    assert bump1.monthlyEmi > base_scen.monthlyEmi
    assert bump2.monthlyEmi > bump1.monthlyEmi
    assert bump1.monthlyEmiDifference > Decimal("0.00")
    assert "fixed" in bump1.assumptions.lower()
