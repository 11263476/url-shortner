from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.deps import get_current_user, get_db
from src.models.user import PlanEnum, User
from src.repositories.user_repository import UserRepository
from src.schemas.billing import UpgradePlanRequest, UpgradePlanResponse

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post("/upgrade", response_model=UpgradePlanResponse, summary="Upgrade or downgrade plan")
async def upgrade_plan(
    payload: UpgradePlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = payload.plan.lower()
    valid_plans = [p.value for p in PlanEnum]
    if plan not in valid_plans:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan '{plan}'. Valid plans: {', '.join(valid_plans)}",
        )
    if plan == current_user.plan:
        return UpgradePlanResponse(detail=f"You are already on the {plan} plan.", plan=plan)

    repo = UserRepository(db)
    await repo.update(current_user.id, plan=PlanEnum(plan))
    return UpgradePlanResponse(detail=f"Plan upgraded to {plan}.", plan=plan)
