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
from src.modules.dashboards.schemas import (
    DashboardResponse,
    DashboardCreate,
    DashboardUpdate,
    WidgetResponse,
    WidgetCreate,
    WidgetUpdate,
    LayoutUpdate,
    LayoutItemResponse,
    DashboardTemplateResponse
)
from src.modules.dashboards.services import DashboardService

router = APIRouter(prefix="", tags=["Dashboard & Visualizations Engine"])


@router.post("/dashboards", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(PermissionRequired("dashboard:create"))])
async def create_dashboard(
    schema: DashboardCreate,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new dashboard metadata profile.
    """
    creator_id = uuid.UUID(user_context.get("sub"))
    org_id = uuid.UUID(user_context.get("org_id"))
    ip_addr = request.client.host if request.client else None
    
    return await DashboardService.create_dashboard(
        db=db,
        org_id=org_id,
        workspace_id=workspace_id,
        creator_id=creator_id,
        schema=schema,
        request_ip=ip_addr
    )


@router.get("/dashboards/templates", response_model=List[DashboardResponse], dependencies=[Depends(PermissionRequired("dashboard:read"))])
async def get_dashboard_templates(db: AsyncSession = Depends(get_db)):
    """
    Lists available built-in templates (Sales, Marketing, HR, Finance, Operations).
    """
    return await DashboardService.list_templates(db)


@router.get("/dashboards", response_model=List[DashboardResponse], dependencies=[Depends(PermissionRequired("dashboard:read"))])
async def list_dashboards(
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all dashboards active inside the workspace context.
    """
    return await DashboardService.list_dashboards(db, workspace_id, page, page_size)


@router.get("/dashboards/{id}", response_model=DashboardResponse, dependencies=[Depends(PermissionRequired("dashboard:read"))])
async def get_dashboard_details(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves complete dashboard widgets list and layout coordinates.
    """
    dashboard = await DashboardService.get_dashboard(db, id)
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")
    return dashboard


@router.put("/dashboards/{id}", response_model=DashboardResponse, dependencies=[Depends(PermissionRequired("dashboard:update"))])
async def update_dashboard(
    id: uuid.UUID,
    schema: DashboardUpdate,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates dashboard attributes (status, templates flags, categories).
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    dashboard = await DashboardService.update_dashboard(db, id, schema, user_id, ip_addr)
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")
    return dashboard


@router.delete("/dashboards/{id}", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("dashboard:delete"))])
async def delete_dashboard(
    id: uuid.UUID,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Performs soft delete of dashboard.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    success = await DashboardService.delete_dashboard(db, id, user_id, ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")
    return {"message": "Dashboard deleted successfully."}


@router.post("/dashboards/{id}/clone", response_model=DashboardResponse, dependencies=[Depends(PermissionRequired("dashboard:create"))])
async def clone_dashboard(
    id: uuid.UUID,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Clones all widgets and layout mappings of target dashboard.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    dashboard = await DashboardService.clone_dashboard(db, id, user_id, ip_addr)
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")
    return dashboard


@router.post("/dashboards/{id}/favorite", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("dashboard:update"))])
async def add_dashboard_to_favorites(
    id: uuid.UUID,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Flags dashboard as user favorite.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    success = await DashboardService.toggle_favorite(db, id, user_id, is_favorite=True, request_ip=ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")
    return {"message": "Dashboard added to favorites."}


@router.delete("/dashboards/{id}/favorite", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("dashboard:update"))])
async def remove_dashboard_from_favorites(
    id: uuid.UUID,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Removes dashboard from user favorites list.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    success = await DashboardService.toggle_favorite(db, id, user_id, is_favorite=False, request_ip=ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")
    return {"message": "Dashboard removed from favorites."}


@router.get("/dashboards/{id}/export", dependencies=[Depends(PermissionRequired("dashboard:read"))])
async def export_dashboard_configuration(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Exports layout and widget configurations as JSON.
    """
    config = await DashboardService.export_config(db, id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")
    return config


@router.post("/dashboards/{id}/widgets", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(PermissionRequired("dashboard:update"))])
async def add_dashboard_widget(
    id: uuid.UUID,
    schema: WidgetCreate,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Adds a new chart widget to the dashboard layout.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    widget = await DashboardService.add_widget(db, id, schema, user_id, ip_addr)
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")
    return widget


@router.put("/widgets/{id}", response_model=WidgetResponse, dependencies=[Depends(PermissionRequired("dashboard:update"))])
async def update_dashboard_widget(
    id: uuid.UUID,
    schema: WidgetUpdate,
    request: Request,
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates widget chart properties (types, aggregations, ranges).
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    widget = await DashboardService.update_widget(db, id, schema, user_id, ip_addr)
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found.")
    return widget


@router.delete("/widgets/{id}", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("dashboard:update"))])
async def delete_dashboard_widget(
    id: uuid.UUID,
    request: Request,
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Removes widget and deletes its layout placement.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    success = await DashboardService.delete_widget(db, id, user_id, ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found.")
    return {"message": "Widget deleted successfully."}


@router.get("/dashboards/{id}/layout", response_model=List[LayoutItemResponse], dependencies=[Depends(PermissionRequired("dashboard:read"))])
async def get_dashboard_layout(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves widget coordinate layouts list.
    """
    dashboard = await DashboardService.get_dashboard(db, id)
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")
    return dashboard.layouts


@router.put("/dashboards/{id}/layout", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("dashboard:update"))])
async def update_dashboard_layout(
    id: uuid.UUID,
    schema: LayoutUpdate,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates coordinate values arrays for grid widgets positions.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    success = await DashboardService.update_layout(db, id, schema, user_id, ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")
    return {"message": "Dashboard layout saved successfully."}
