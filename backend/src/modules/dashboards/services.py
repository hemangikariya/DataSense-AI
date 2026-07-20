import uuid
import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logging import logger
from src.modules.dashboards.models import Dashboard, DashboardWidget, DashboardLayout, DashboardShare, DashboardFavorite
from src.modules.dashboards.schemas import DashboardCreate, DashboardUpdate, WidgetCreate, WidgetUpdate, LayoutUpdate
from src.modules.auth.services import AuditLogService


class DashboardService:
    @staticmethod
    async def create_dashboard(
        db: AsyncSession,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID,
        creator_id: uuid.UUID,
        schema: DashboardCreate,
        request_ip: Optional[str] = None
    ) -> Dashboard:
        """
        Creates a new dashboard, logging the security event audits.
        """
        dashboard = Dashboard(
            organization_id=org_id,
            workspace_id=workspace_id,
            creator_id=creator_id,
            name=schema.name,
            description=schema.description,
            category=schema.category,
            is_template=schema.is_template,
            template_name=schema.template_name,
            status="Draft"
        )
        db.add(dashboard)
        await db.flush()

        await AuditLogService.log_event(
            db, user_id=creator_id, org_id=org_id, workspace_id=workspace_id, action="DASHBOARD_CREATE", ip_address=request_ip
        )
        await db.commit()
        await db.refresh(dashboard)
        return dashboard

    @staticmethod
    async def get_dashboard(db: AsyncSession, dashboard_id: uuid.UUID) -> Optional[Dashboard]:
        query = select(Dashboard).where(
            Dashboard.id == dashboard_id, Dashboard.is_deleted == False
        ).options(
            selectinload(Dashboard.widgets),
            selectinload(Dashboard.layouts)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_dashboard(
        db: AsyncSession,
        dashboard_id: uuid.UUID,
        schema: DashboardUpdate,
        user_id: uuid.UUID,
        request_ip: Optional[str] = None
    ) -> Optional[Dashboard]:
        dashboard = await DashboardService.get_dashboard(db, dashboard_id)
        if not dashboard:
            return None

        for field, val in schema.model_dump(exclude_unset=True).items():
            setattr(dashboard, field, val)

        # Increment layout version
        dashboard.version += 1

        await AuditLogService.log_event(
            db, user_id=user_id, org_id=dashboard.organization_id, workspace_id=dashboard.workspace_id, action="DASHBOARD_UPDATE", ip_address=request_ip
        )
        await db.commit()
        await db.refresh(dashboard)
        return dashboard

    @staticmethod
    async def delete_dashboard(
        db: AsyncSession,
        dashboard_id: uuid.UUID,
        user_id: uuid.UUID,
        request_ip: Optional[str] = None
    ) -> bool:
        dashboard = await DashboardService.get_dashboard(db, dashboard_id)
        if not dashboard:
            return False

        dashboard.is_deleted = True
        await AuditLogService.log_event(
            db, user_id=user_id, org_id=dashboard.organization_id, workspace_id=dashboard.workspace_id, action="DASHBOARD_DELETE", ip_address=request_ip
        )
        await db.commit()
        return True

    @staticmethod
    async def clone_dashboard(
        db: AsyncSession,
        dashboard_id: uuid.UUID,
        user_id: uuid.UUID,
        request_ip: Optional[str] = None
    ) -> Optional[Dashboard]:
        """
        Clones layout and widget variables of target dashboard to a new copy.
        """
        source = await DashboardService.get_dashboard(db, dashboard_id)
        if not source:
            return None

        # 1. Create duplicate dashboard
        cloned = Dashboard(
            organization_id=source.organization_id,
            workspace_id=source.workspace_id,
            creator_id=user_id,
            name=f"{source.name} - Copy",
            description=source.description,
            category=source.category,
            is_template=False,
            status="Draft"
        )
        db.add(cloned)
        await db.flush()

        # Map widget old_id to new_id to map layouts properly
        widget_id_map = {}

        # 2. Duplicate Widgets
        for w in source.widgets:
            widget_copy = DashboardWidget(
                dashboard_id=cloned.id,
                dataset_id=w.dataset_id,
                dataset_version=w.dataset_version,
                title=w.title,
                description=w.description,
                widget_type=w.widget_type,
                x_axis_column=w.x_axis_column,
                y_axis_column=w.y_axis_column,
                aggregation=w.aggregation,
                filters_json=w.filters_json,
                sorting_column=w.sorting_column,
                color_theme=w.color_theme,
                refresh_interval=w.refresh_interval
            )
            db.add(widget_copy)
            await db.flush()
            widget_id_map[w.id] = widget_copy.id

        # 3. Duplicate Layout Coordinates
        for l in source.layouts:
            if l.widget_id in widget_id_map:
                layout_copy = DashboardLayout(
                    dashboard_id=cloned.id,
                    widget_id=widget_id_map[l.widget_id],
                    pos_x=l.pos_x,
                    pos_y=l.pos_y,
                    width=l.width,
                    height=l.height
                )
                db.add(layout_copy)

        await AuditLogService.log_event(
            db, user_id=user_id, org_id=cloned.organization_id, workspace_id=cloned.workspace_id, action="DASHBOARD_CLONE", ip_address=request_ip
        )
        await db.commit()
        
        # Query fully populated dashboard copy details
        return await DashboardService.get_dashboard(db, cloned.id)

    @staticmethod
    async def add_widget(
        db: AsyncSession,
        dashboard_id: uuid.UUID,
        schema: WidgetCreate,
        user_id: uuid.UUID,
        request_ip: Optional[str] = None
    ) -> Optional[DashboardWidget]:
        dashboard = await DashboardService.get_dashboard(db, dashboard_id)
        if not dashboard:
            return None

        # Register Widget
        widget = DashboardWidget(
            dashboard_id=dashboard_id,
            dataset_id=schema.dataset_id,
            dataset_version=schema.dataset_version,
            title=schema.title,
            description=schema.description,
            widget_type=schema.widget_type,
            x_axis_column=schema.x_axis_column,
            y_axis_column=schema.y_axis_column,
            aggregation=schema.aggregation,
            filters_json=schema.filters_json,
            sorting_column=schema.sorting_column,
            color_theme=schema.color_theme,
            refresh_interval=schema.refresh_interval
        )
        db.add(widget)
        await db.flush()

        # Add Default Grid Layout coordinates (pos=0, size=4x3)
        layout = DashboardLayout(
            dashboard_id=dashboard_id,
            widget_id=widget.id,
            pos_x=0,
            pos_y=0,
            width=4,
            height=3
        )
        db.add(layout)

        await AuditLogService.log_event(
            db, user_id=user_id, org_id=dashboard.organization_id, workspace_id=dashboard.workspace_id, action="WIDGET_CREATE", ip_address=request_ip
        )
        await db.commit()
        return widget

    @staticmethod
    async def update_widget(
        db: AsyncSession,
        widget_id: uuid.UUID,
        schema: WidgetUpdate,
        user_id: uuid.UUID,
        request_ip: Optional[str] = None
    ) -> Optional[DashboardWidget]:
        query = select(DashboardWidget).where(DashboardWidget.id == widget_id)
        result = await db.execute(query)
        widget = result.scalar_one_or_none()
        if not widget:
            return None

        for field, val in schema.model_dump(exclude_unset=True).items():
            setattr(widget, field, val)

        # Retrieve dashboard for logging contexts
        d_query = select(Dashboard).where(Dashboard.id == widget.dashboard_id)
        d_res = await db.execute(d_query)
        dashboard = d_res.scalar_one()

        await AuditLogService.log_event(
            db, user_id=user_id, org_id=dashboard.organization_id, workspace_id=dashboard.workspace_id, action="WIDGET_UPDATE", ip_address=request_ip
        )
        await db.commit()
        await db.refresh(widget)
        return widget

    @staticmethod
    async def delete_widget(
        db: AsyncSession,
        widget_id: uuid.UUID,
        user_id: uuid.UUID,
        request_ip: Optional[str] = None
    ) -> bool:
        query = select(DashboardWidget).where(DashboardWidget.id == widget_id)
        result = await db.execute(query)
        widget = result.scalar_one_or_none()
        if not widget:
            return False

        d_query = select(Dashboard).where(Dashboard.id == widget.dashboard_id)
        d_res = await db.execute(d_query)
        dashboard = d_res.scalar_one()

        await db.delete(widget)
        await AuditLogService.log_event(
            db, user_id=user_id, org_id=dashboard.organization_id, workspace_id=dashboard.workspace_id, action="WIDGET_DELETE", ip_address=request_ip
        )
        await db.commit()
        return True

    @staticmethod
    async def update_layout(
        db: AsyncSession,
        dashboard_id: uuid.UUID,
        schema: LayoutUpdate,
        user_id: uuid.UUID,
        request_ip: Optional[str] = None
    ) -> bool:
        dashboard = await DashboardService.get_dashboard(db, dashboard_id)
        if not dashboard:
            return False

        # Drop old layout items mappings
        from sqlalchemy import delete
        stmt = delete(DashboardLayout).where(DashboardLayout.dashboard_id == dashboard_id)
        await db.execute(stmt)

        # Insert new coordinate mapping objects
        for item in schema.layout_items:
            lay = DashboardLayout(
                dashboard_id=dashboard_id,
                widget_id=item.widget_id,
                pos_x=item.pos_x,
                pos_y=item.pos_y,
                width=item.width,
                height=item.height
            )
            db.add(lay)

        await AuditLogService.log_event(
            db, user_id=user_id, org_id=dashboard.organization_id, workspace_id=dashboard.workspace_id, action="LAYOUT_UPDATE", ip_address=request_ip
        )
        await db.commit()
        return True

    @staticmethod
    async def toggle_favorite(
        db: AsyncSession,
        dashboard_id: uuid.UUID,
        user_id: uuid.UUID,
        is_favorite: bool,
        request_ip: Optional[str] = None
    ) -> bool:
        dashboard = await DashboardService.get_dashboard(db, dashboard_id)
        if not dashboard:
            return False

        fav_query = select(DashboardFavorite).where(
            DashboardFavorite.dashboard_id == dashboard_id,
            DashboardFavorite.user_id == user_id
        )
        fav_res = await db.execute(fav_query)
        favorite = fav_res.scalar_one_or_none()

        if is_favorite:
            if not favorite:
                new_fav = DashboardFavorite(dashboard_id=dashboard_id, user_id=user_id)
                db.add(new_fav)
                await AuditLogService.log_event(
                    db, user_id=user_id, org_id=dashboard.organization_id, workspace_id=dashboard.workspace_id, action="FAVORITE_ADD", ip_address=request_ip
                )
        else:
            if favorite:
                await db.delete(favorite)
                await AuditLogService.log_event(
                    db, user_id=user_id, org_id=dashboard.organization_id, workspace_id=dashboard.workspace_id, action="FAVORITE_REMOVE", ip_address=request_ip
                )

        await db.commit()
        return True

    @staticmethod
    async def export_config(db: AsyncSession, dashboard_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        dashboard = await DashboardService.get_dashboard(db, dashboard_id)
        if not dashboard:
            return None

        # Build JSON config file configurations
        widgets_list = []
        for w in dashboard.widgets:
            widgets_list.append({
                "title": w.title,
                "description": w.description,
                "widget_type": w.widget_type,
                "x_axis_column": w.x_axis_column,
                "y_axis_column": w.y_axis_column,
                "aggregation": w.aggregation,
                "filters_json": w.filters_json,
                "sorting_column": w.sorting_column,
                "color_theme": w.color_theme,
                "refresh_interval": w.refresh_interval
            })

        return {
            "dashboard_name": dashboard.name,
            "description": dashboard.description,
            "category": dashboard.category,
            "widgets": widgets_list
        }

    @staticmethod
    async def list_templates(db: AsyncSession) -> List[Dashboard]:
        # Return built-in default dashboard templates or marked templates
        query = select(Dashboard).where(
            Dashboard.is_template == True,
            Dashboard.is_deleted == False
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def list_dashboards(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dashboard]:
        query = select(Dashboard).where(
            Dashboard.workspace_id == workspace_id,
            Dashboard.is_deleted == False
        ).order_by(Dashboard.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        return list(result.scalars().all())
