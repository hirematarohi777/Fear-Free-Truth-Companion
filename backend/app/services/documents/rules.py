import re
import uuid
from typing import List, Dict, Any, Tuple
from app.schemas.analyses import (
    FinancialField,
    FieldStatus,
    ChargeFinding,
    ChargeCategory,
    Severity,
    EvidenceQuality,
    ExtractedLoanTerms
)
from app.services.documents.extractor import ExtractedUnit
from app.services.documents.quote_verifier import verify_quote_in_units


def find_pattern_with_quote(units: List[ExtractedUnit], pattern: str) -> List[Tuple[re.Match, str, str]]:
    """Scan units for regex matches and return (match, source_ref, snippet)."""
    matches = []
    regex = re.compile(pattern, re.IGNORECASE)
    for u in units:
        for m in regex.finditer(u.text):
            # Extract surrounding snippet (around 120 chars) for quote
            start = max(0, m.start() - 30)
            end = min(len(u.text), m.end() + 70)
            snippet = u.text[start:end].strip()
            matches.append((m, u.source_ref, snippet))
    return matches


def run_deterministic_rules(units: List[ExtractedUnit]) -> Tuple[ExtractedLoanTerms, List[ChargeFinding]]:
    """
    Deterministically scan document text for Indian home loan terms, disclosed fees,
    overlooked charges, and conditional clauses.
    """
    findings: List[ChargeFinding] = []

    # Helper to construct empty field
    def make_field(name: str) -> FinancialField:
        return FinancialField(fieldName=name, status=FieldStatus.NOT_FOUND)

    terms = ExtractedLoanTerms(
        lenderName=make_field("Lender Name"),
        borrowerName=make_field("Borrower Name"),
        loanAmount=make_field("Sanctioned Loan Amount"),
        amountDisbursed=make_field("Amount Disbursed"),
        interestRate=make_field("Interest Rate"),
        interestStructure=make_field("Interest Structure (Fixed/Floating)"),
        benchmarkAndSpread=make_field("Benchmark and Spread"),
        loanTenureMonths=make_field("Loan Tenure (Months)"),
        emi=make_field("Monthly EMI"),
        processingFee=make_field("Processing Fee"),
        administrativeFee=make_field("Administrative Fee"),
        legalValuationCharges=make_field("Legal & Valuation Charges"),
        insurancePremium=make_field("Insurance Premium"),
        taxesOnFees=make_field("Taxes on Fees (GST)"),
        prepaymentForeclosureConditions=make_field("Prepayment & Foreclosure Conditions"),
        latePaymentBounceCharges=make_field("Late Payment / Bounce Charges"),
        rateResetConditions=make_field("Rate Reset Conditions"),
        balloonPayments=make_field("Balloon Payments"),
        bundledOptionalProducts=make_field("Bundled or Optional Products"),
        cancellationRefundTerms=make_field("Cancellation and Refund Terms")
    )

    # 1. Sanctioned Loan Amount
    amount_matches = find_pattern_with_quote(
        units,
        r'(?:sanction(?:ed)?\s+(?:loan\s+)?amount|loan\s+amount|facility\s+amount)\s*[:=-]?\s*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)'
    )
    if amount_matches:
        m, ref, quote = amount_matches[0]
        raw_val = m.group(1).replace(",", "")
        try:
            val_num = float(raw_val)
            terms.loanAmount = FinancialField(
                fieldName="Sanctioned Loan Amount",
                value=f"₹{m.group(1)}",
                numericValue=val_num,
                unitOrCurrency="INR",
                sourceReference=ref,
                supportingQuote=quote,
                status=FieldStatus.FOUND
            )
        except ValueError:
            terms.loanAmount = FinancialField(
                fieldName="Sanctioned Loan Amount",
                value=m.group(1),
                unitOrCurrency="INR",
                sourceReference=ref,
                supportingQuote=quote,
                status=FieldStatus.AMBIGUOUS
            )

    # 2. Interest Rate & Rate Conflicts
    rate_matches = find_pattern_with_quote(
        units,
        r'(?:rate\s+of\s+interest|interest\s+rate|roi)\s*[:=-]?\s*([0-9]{1,2}(?:\.[0-9]{1,2})?)\s*(?:%|percent)'
    )
    if rate_matches:
        rates_found = set()
        for m, ref, quote in rate_matches:
            rates_found.add((m.group(1), ref, quote))

        if len(rates_found) == 1:
            r_val, ref, quote = list(rates_found)[0]
            terms.interestRate = FinancialField(
                fieldName="Interest Rate",
                value=f"{r_val}% p.a.",
                numericValue=float(r_val),
                unitOrCurrency="% p.a.",
                sourceReference=ref,
                supportingQuote=quote,
                status=FieldStatus.FOUND
            )
        else:
            # Conflicting interest rates found across pages/sections!
            first_r, first_ref, first_quote = list(rates_found)[0]
            diff_rates_desc = ", ".join([f"{r}% at {ref}" for r, ref, _ in rates_found])
            terms.interestRate = FinancialField(
                fieldName="Interest Rate",
                value=f"{first_r}% p.a. (conflicting mentions found)",
                numericValue=float(first_r),
                unitOrCurrency="% p.a.",
                sourceReference=first_ref,
                supportingQuote=first_quote,
                status=FieldStatus.CONFLICTING,
                notes=f"Conflicting rates detected: {diff_rates_desc}"
            )
            findings.append(ChargeFinding(
                id=f"finding-{uuid.uuid4().hex[:8]}",
                title="Conflicting Interest Rates in Document",
                category=ChargeCategory.CONFLICTING_TERMS,
                severity=Severity.HIGH,
                plainLanguageExplanation=(
                    f"Different interest rates are cited in different parts of your agreement ({diff_rates_desc}). "
                    "This ambiguity could result in higher than expected monthly EMI payments."
                ),
                amountOrCalculationBasis=diff_rates_desc,
                conditionsUnderWhichItApplies="Discrepancy between loan schedule and standard clause sections.",
                supportingQuote=first_quote,
                sourceReference=first_ref,
                evidenceQuality=EvidenceQuality.CLEAR,
                recommendedQuestionForLender=(
                    "Which exact interest rate is legally binding on disbursement date, and why are multiple distinct rates printed?"
                )
            ))

    # 3. Interest Structure (Floating / Fixed / Hybrid)
    floating_matches = find_pattern_with_quote(units, r'\b(floating|adjustable|variable|repo\s+linked|ebr|mclr)\b')
    fixed_matches = find_pattern_with_quote(units, r'\b(fixed\s+rate|fixed\s+for\s+entire\s+tenure)\b')
    if floating_matches and not fixed_matches:
        m, ref, quote = floating_matches[0]
        terms.interestStructure = FinancialField(
            fieldName="Interest Structure",
            value="Floating Rate",
            sourceReference=ref,
            supportingQuote=quote,
            status=FieldStatus.FOUND,
            notes="Floating interest benchmark linked."
        )
    elif fixed_matches and not floating_matches:
        m, ref, quote = fixed_matches[0]
        terms.interestStructure = FinancialField(
            fieldName="Interest Structure",
            value="Fixed Rate",
            sourceReference=ref,
            supportingQuote=quote,
            status=FieldStatus.FOUND
        )
    elif fixed_matches and floating_matches:
        terms.interestStructure = FinancialField(
            fieldName="Interest Structure",
            value="Hybrid / Floating with Fixed Period",
            sourceReference=floating_matches[0][1],
            supportingQuote=floating_matches[0][2],
            status=FieldStatus.AMBIGUOUS,
            notes="Mentions both fixed and floating terms."
        )

    # 4. Tenure (Months / Years)
    tenure_matches = find_pattern_with_quote(
        units,
        r'(?:tenor|tenure|repayment\s+period)\s*[:=-]?\s*([0-9]{1,3})\s*(months?|years?|yrs?)'
    )
    if tenure_matches:
        m, ref, quote = tenure_matches[0]
        num = int(m.group(1))
        unit_str = m.group(2).lower()
        if "year" in unit_str or "yr" in unit_str:
            tenure_months = num * 12
        else:
            tenure_months = num

        terms.loanTenureMonths = FinancialField(
            fieldName="Loan Tenure (Months)",
            value=f"{tenure_months} months ({tenure_months // 12} yrs {tenure_months % 12} mos)",
            numericValue=float(tenure_months),
            unitOrCurrency="months",
            sourceReference=ref,
            supportingQuote=quote,
            status=FieldStatus.FOUND
        )

    # 5. Monthly EMI
    emi_matches = find_pattern_with_quote(
        units,
        r'(?:monthly\s+emi|emi\s+amount|equated\s+monthly\s+installment)\s*[:=-]?\s*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)'
    )
    if emi_matches:
        m, ref, quote = emi_matches[0]
        raw_val = m.group(1).replace(",", "")
        try:
            terms.emi = FinancialField(
                fieldName="Monthly EMI",
                value=f"₹{m.group(1)}",
                numericValue=float(raw_val),
                unitOrCurrency="INR",
                sourceReference=ref,
                supportingQuote=quote,
                status=FieldStatus.FOUND
            )
        except ValueError:
            pass

    # 6. Processing Fee
    proc_matches = find_pattern_with_quote(
        units,
        r'(?:processing\s+(?:fee|charges?))\s*[:=-]?\s*(?:(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)|([0-9]+(?:\.[0-9]+)?\s*%))'
    )
    if proc_matches:
        m, ref, quote = proc_matches[0]
        fee_str = m.group(1) or m.group(2)
        terms.processingFee = FinancialField(
            fieldName="Processing Fee",
            value=f"{fee_str} (plus applicable taxes)",
            sourceReference=ref,
            supportingQuote=quote,
            status=FieldStatus.FOUND
        )
        findings.append(ChargeFinding(
            id=f"finding-{uuid.uuid4().hex[:8]}",
            title="Processing Fee Disclosed",
            category=ChargeCategory.EXPLICITLY_DISCLOSED,
            severity=Severity.INFORMATIONAL,
            plainLanguageExplanation=(
                f"The document states a processing fee of {fee_str}. "
                "Confirm whether this is paid upfront, whether it is non-refundable if the loan is not disbursed, "
                "and whether 18% GST is charged in addition."
            ),
            amountOrCalculationBasis=fee_str,
            conditionsUnderWhichItApplies="Payable upon application sanction or before disbursement.",
            supportingQuote=quote,
            sourceReference=ref,
            evidenceQuality=EvidenceQuality.CLEAR,
            recommendedQuestionForLender=(
                "Is this processing fee deducted from the sanctioned loan disbursement or paid separately, "
                "and is any portion refundable if the property deal does not materialize?"
            )
        ))
    else:
        findings.append(ChargeFinding(
            id=f"finding-{uuid.uuid4().hex[:8]}",
            title="Processing Fee Not Explicitly Stated",
            category=ChargeCategory.UNCLEAR_OR_MISSING,
            severity=Severity.MEDIUM,
            plainLanguageExplanation=(
                "No explicit processing fee amount or percentage was identified in the readable sections. "
                "Banks in India typically charge between 0.25% to 1.00% plus GST."
            ),
            amountOrCalculationBasis=None,
            conditionsUnderWhichItApplies="Sanction and documentation phase.",
            supportingQuote=None,
            sourceReference=None,
            evidenceQuality=EvidenceQuality.INSUFFICIENT,
            recommendedQuestionForLender="What is the total processing fee including all taxes, and when is it due?"
        ))

    # 7. Administrative / Documentation / Legal / Valuation Fees
    admin_matches = find_pattern_with_quote(
        units,
        r'(?:administrative\s+charges?|admin\s+fee|documentation\s+charges?|legal\s+(?:and|&)\s+valuation\s+charges?)\s*[:=-]?\s*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)'
    )
    if admin_matches:
        for m, ref, quote in admin_matches:
            fee_val = m.group(1)
            findings.append(ChargeFinding(
                id=f"finding-{uuid.uuid4().hex[:8]}",
                title="Administrative / Legal & Valuation Charges Disclosed",
                category=ChargeCategory.EASILY_OVERLOOKED,
                severity=Severity.LOW,
                plainLanguageExplanation=(
                    f"Additional administrative or legal/valuation fees of ₹{fee_val} are levied. "
                    "These are separate from standard processing fees."
                ),
                amountOrCalculationBasis=f"₹{fee_val}",
                conditionsUnderWhichItApplies="Due during title deed legal verification or technical valuation.",
                supportingQuote=quote,
                sourceReference=ref,
                evidenceQuality=EvidenceQuality.CLEAR,
                recommendedQuestionForLender="Are legal and valuation charges final or subject to additional inspection charges?"
            ))

    # 8. Insurance Premium & Bundling
    ins_matches = find_pattern_with_quote(
        units,
        r'(?:insurance\s+(?:premium|cover|policy)|property\s+insurance|credit\s+shield|loan\s+protect(?:ion)?)\s*[:=-]?\s*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)?'
    )
    if ins_matches:
        m, ref, quote = ins_matches[0]
        ins_val = m.group(1) or "Amount unspecified"
        # Check if described as mandatory or optional
        is_mandatory = bool(re.search(r'\b(mandatory|compulsory|required|must\s+obtain)\b', quote, re.I))
        findings.append(ChargeFinding(
            id=f"finding-{uuid.uuid4().hex[:8]}",
            title="Bundled Insurance Requirement Detected",
            category=ChargeCategory.EASILY_OVERLOOKED if not is_mandatory else ChargeCategory.CONDITIONAL,
            severity=Severity.MEDIUM,
            plainLanguageExplanation=(
                f"Document mentions an insurance policy ({ins_val}). "
                "Under RBI guidelines, borrowers have the right to purchase insurance from any IRDAI-licensed insurer of their choice, "
                "and lenders cannot make taking their bundled insurance policy a compulsory condition."
            ),
            amountOrCalculationBasis=f"₹{ins_val}" if m.group(1) else "Check fee schedule",
            conditionsUnderWhichItApplies="Often bundled into sanction or financed into principal.",
            supportingQuote=quote,
            sourceReference=ref,
            evidenceQuality=EvidenceQuality.CLEAR,
            recommendedQuestionForLender=(
                "Is this insurance policy strictly optional, and am I allowed to assign an existing life/term policy or choose an external insurer?"
            )
        ))

    # 9. Prepayment / Foreclosure Conditions
    foreclosure_matches = find_pattern_with_quote(
        units,
        r'(?:prepayment|foreclosure|part-payment)\s*(?:penalty|charges?)?\s*[:=-]?\s*([^.;\n]{10,120})'
    )
    if foreclosure_matches:
        m, ref, quote = foreclosure_matches[0]
        rule_text = m.group(1)
        # Check RBI guideline compliance (Floating individual home loans cannot have prepayment penalties)
        has_floating_penalty = bool(re.search(r'[1-9]\s*%', rule_text) and "floating" in (terms.interestStructure.value or "").lower())
        findings.append(ChargeFinding(
            id=f"finding-{uuid.uuid4().hex[:8]}",
            title="Prepayment & Foreclosure Clause",
            category=ChargeCategory.CONDITIONAL,
            severity=Severity.HIGH if has_floating_penalty else Severity.INFORMATIONAL,
            plainLanguageExplanation=(
                f"The agreement states: '{rule_text}'. "
                "Per RBI circulars, banks and NBFCs cannot charge foreclosure or prepayment fees on floating-rate home loans to individual borrowers. "
                "Verify that no prepayment fee will apply if you make lump-sum repayments."
            ),
            amountOrCalculationBasis=rule_text,
            conditionsUnderWhichItApplies="When borrower repays part or all of the outstanding balance early.",
            supportingQuote=quote,
            sourceReference=ref,
            evidenceQuality=EvidenceQuality.CLEAR,
            recommendedQuestionForLender="Can you confirm in writing that zero prepayment or foreclosure penalties apply to my floating-rate home loan?"
        ))

    # 10. Late Payment / Bounce Charges
    late_matches = find_pattern_with_quote(
        units,
        r'(?:penal\s+interest|late\s+payment\s+charges?|cheque\s+bounce|ecs\s+bounce|nach\s+dishonou?r)\s*[:=-]?\s*([^.;\n]{10,100})'
    )
    if late_matches:
        for m, ref, quote in late_matches:
            c_text = m.group(1)
            findings.append(ChargeFinding(
                id=f"finding-{uuid.uuid4().hex[:8]}",
                title="Penal Interest & Bounce Charges",
                category=ChargeCategory.CONDITIONAL,
                severity=Severity.MEDIUM,
                plainLanguageExplanation=(
                    f"Conditional charge triggered upon delayed installment or NACH/ECS bounce: '{c_text}'. "
                    "Under latest RBI guidelines, penal charges must be reasonable and cannot be compounded as penal interest."
                ),
                amountOrCalculationBasis=c_text,
                conditionsUnderWhichItApplies="Triggered if monthly repayment fails or is delayed.",
                supportingQuote=quote,
                sourceReference=ref,
                evidenceQuality=EvidenceQuality.CLEAR,
                recommendedQuestionForLender="Are late charges treated as penal charges rather than compounding penal interest?"
            ))

    # 11. Rate Reset Conditions (Spread alteration)
    reset_matches = find_pattern_with_quote(
        units,
        r'(?:reset|revision\s+of\s+spread|reset\s+periodicity|benchmark\s+reset)\s*[:=-]?\s*([^.;\n]{10,120})'
    )
    if reset_matches:
        m, ref, quote = reset_matches[0]
        findings.append(ChargeFinding(
            id=f"finding-{uuid.uuid4().hex[:8]}",
            title="Interest Rate Reset Clause",
            category=ChargeCategory.CONDITIONAL,
            severity=Severity.MEDIUM,
            plainLanguageExplanation=(
                f"Rate reset terms: '{m.group(1)}'. "
                "Borrowers should know whether resets happen quarterly or immediately upon external benchmark changes, and whether the bank can alter the spread."
            ),
            amountOrCalculationBasis=m.group(1),
            conditionsUnderWhichItApplies="Occurs periodically or when RBI repo rate changes.",
            supportingQuote=quote,
            sourceReference=ref,
            evidenceQuality=EvidenceQuality.CLEAR,
            recommendedQuestionForLender="What is the exact reset periodicity (e.g. 3 months) and is the spread over the benchmark contracted as fixed?"
        ))

    return terms, findings
