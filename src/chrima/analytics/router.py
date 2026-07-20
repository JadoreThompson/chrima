from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_jwt, depends_object
from chrima.jwt.schema import JWTPayload
from chrima.workspace import WorkspaceService
from .enums import TimePeriod
from .schema import AnalyticsSummary, AnalyticsTimeSeries, SubscriptionAnalytics
from .service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    workspace_id: UUID = Query(),
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    analytics_service: AnalyticsService = Depends(depends_object(AnalyticsService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    workspace = await workspace_service.get(workspace_id, jwt.sub, db_sess)
    return await analytics_service.get_summary(workspace.id, db_sess)


@router.get("/revenue", response_model=AnalyticsTimeSeries)
async def get_revenue_timeseries(
    workspace_id: UUID = Query(),
    period: TimePeriod = Query(),
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    analytics_service: AnalyticsService = Depends(depends_object(AnalyticsService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    await workspace_service.get(workspace_id, jwt.sub, db_sess)
    return await analytics_service.get_revenue_timeseries(workspace_id, period, db_sess)


@router.get("/active-customers", response_model=AnalyticsTimeSeries)
async def get_active_customers_timeseries(
    workspace_id: UUID = Query(),
    period: TimePeriod = Query(),
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    analytics_service: AnalyticsService = Depends(depends_object(AnalyticsService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    workspace = await workspace_service.get(workspace_id, jwt.sub, db_sess)
    return await analytics_service.get_active_customers_timeseries(
        workspace.id, period, db_sess
    )


@router.get("/subscriptions", response_model=SubscriptionAnalytics)
async def get_subscription_analytics(
    workspace_id: UUID = Query(),
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    analytics_service: AnalyticsService = Depends(depends_object(AnalyticsService)),
    workspace_service: WorkspaceService = Depends(depends_object(WorkspaceService)),
):
    workspace = await workspace_service.get(workspace_id, jwt.sub, db_sess)
    return await analytics_service.get_subscription_breakdown(workspace.id, db_sess)
