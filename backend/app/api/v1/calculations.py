from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, AuthenticatedUser
from app.schemas.calculations import LoanCalculationRequest, LoanCalculationResponse
from app.services.calculations.loan_calculator import compute_loan_details


router = APIRouter(prefix="/calculations", tags=["Financial Calculations"])


@router.post("/loan", response_model=LoanCalculationResponse)
async def calculate_loan_finances(
    req: LoanCalculationRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Perform authoritative financial math using Python's Decimal library.
    Computes monthly EMI, financed principal adjustments, net disbursement,
    rate-change scenario comparisons (+1%, +2%), and a full amortization schedule.
    """
    return compute_loan_details(req)
