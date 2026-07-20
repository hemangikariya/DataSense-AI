import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import (
    get_db,
    verify_workspace_access,
    get_authenticated_user_context,
    PermissionRequired
)
from src.modules.analytics.schemas import (
    ReportResponse,
    ReportCreate,
    ScheduledReportResponse,
    ScheduledReportCreate,
    ReportHistoryResponse,
    PredictionJobCreate,
    PredictionJobResponse
)
from src.modules.analytics.services import AnalyticsService

router = APIRouter(prefix="", tags=["Reports & Predictive Analytics Engine"])


@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(PermissionRequired("report:create"))])
async def create_report(
    schema: ReportCreate,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new custom metric layout report profile.
    """
    creator_id = uuid.UUID(user_context.get("sub"))
    org_id = uuid.UUID(user_context.get("org_id"))
    ip_addr = request.client.host if request.client else None
    
    return await AnalyticsService.create_report(
        db=db,
        org_id=org_id,
        workspace_id=workspace_id,
        creator_id=creator_id,
        schema=schema,
        request_ip=ip_addr
    )


@router.get("/reports/templates", response_model=List[ReportResponse], dependencies=[Depends(PermissionRequired("report:read"))])
async def get_report_templates(db: AsyncSession = Depends(get_db)):
    """
    Lists system pre-seeded layout templates.
    """
    return await AnalyticsService.list_templates(db)


@router.get("/reports/history", response_model=List[ReportHistoryResponse], dependencies=[Depends(PermissionRequired("report:read"))])
async def get_report_exports_history(
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves all historic export log statuses (Queued, Running, Completed).
    """
    return await AnalyticsService.list_exports_history(db, workspace_id)


@router.get("/reports", response_model=List[ReportResponse], dependencies=[Depends(PermissionRequired("report:read"))])
async def list_reports(
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all reports compiled in the active workspace.
    """
    return await AnalyticsService.list_reports(db, workspace_id, page, page_size)


@router.get("/reports/{id}", response_model=ReportResponse, dependencies=[Depends(PermissionRequired("report:read"))])
async def get_report_details(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves sections list matching report.
    """
    report = await AnalyticsService.get_report(db, id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report profile not found.")
    return report


@router.put("/reports/{id}", response_model=ReportResponse, dependencies=[Depends(PermissionRequired("report:update"))])
async def update_report(
    id: uuid.UUID,
    schema: ReportCreate,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Saves new sections lists layouts inside report.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    report = await AnalyticsService.update_report(db, id, schema, user_id, ip_addr)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return report


@router.delete("/reports/{id}", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("report:delete"))])
async def delete_report(
    id: uuid.UUID,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft deletes the report layouts parameters.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    success = await AnalyticsService.delete_report(db, id, user_id, ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return {"message": "Report deleted successfully."}


@router.post("/reports/{id}/export", response_model=ReportHistoryResponse, dependencies=[Depends(PermissionRequired("report:export"))])
async def trigger_report_export(
    id: uuid.UUID,
    format: str = Query("PDF", pattern="^(PDF|XLSX|CSV|JSON)$"),
    request: Request = None,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers asynchronous export enqueues inside Celery workers.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    return await AnalyticsService.export_report(db, id, format, user_id, workspace_id, ip_addr)


@router.post("/reports/{id}/schedule", response_model=ScheduledReportResponse, dependencies=[Depends(PermissionRequired("report:update"))])
async def schedule_automated_report(
    id: uuid.UUID,
    schema: ScheduledReportCreate,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Registers an email delivery cron schedule check.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    return await AnalyticsService.schedule_report(db, id, workspace_id, schema, user_id, ip_addr)


@router.get("/predictions", response_model=List[PredictionJobResponse], dependencies=[Depends(PermissionRequired("prediction:read"))])
async def list_prediction_history(
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all prediction jobs triggered in workspace context.
    """
    return await AnalyticsService.list_predictions(db, workspace_id)


@router.post("/predictions", response_model=PredictionJobResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(PermissionRequired("prediction:create"))])
async def trigger_prediction_job(
    schema: PredictionJobCreate,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Enqueues linear regression modeling predictions job inside Celery.
    """
    creator_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    return await AnalyticsService.run_prediction(db, workspace_id, creator_id, schema, ip_addr)


@router.get("/predictions/{id}", response_model=PredictionJobResponse, dependencies=[Depends(PermissionRequired("prediction:read"))])
async def get_prediction_job_details(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves predictive outputs metrics, accuracy, explanation, and confidence bands.
    """
    job = await AnalyticsService.get_prediction(db, id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction job not found.")
    return job


@router.get("/predictions/history", response_model=List[PredictionJobResponse], dependencies=[Depends(PermissionRequired("prediction:read"))])
async def get_prediction_runs_history(
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Historical prediction list proxy view.
    """
    return await AnalyticsService.list_predictions(db, workspace_id)


@router.get("/exports", response_model=List[ReportHistoryResponse], dependencies=[Depends(PermissionRequired("report:read"))])
async def list_all_workspace_exports(
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all document downloads history.
    """
    return await AnalyticsService.list_exports_history(db, workspace_id)
