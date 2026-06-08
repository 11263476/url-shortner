from fastapi import APIRouter, Depends, Query

from src.core.deps import get_current_user, get_analytics_service
from src.models.user import User
from src.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/{short_code}/summary",
    summary="Get URL analytics summary",
    description="Returns click count, unique visitors, device breakdown, and geo data for a short URL.")
async def get_summary(short_code: str, current_user: User = Depends(get_current_user), svc: AnalyticsService = Depends(get_analytics_service)):
    return await svc.get_summary(short_code, current_user.id)


@router.get("/{short_code}/timeseries",
    summary="Get analytics time series",
    description="Daily click counts over the last N days (max 90).")
async def get_timeseries(short_code: str, days: int = Query(7, ge=1, le=90, description="Number of days to look back"), current_user: User = Depends(get_current_user), svc: AnalyticsService = Depends(get_analytics_service)):
    return await svc.get_timeseries(short_code, current_user.id, days)
