import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.dashboards.models import Dashboard, DashboardWidget, DashboardLayout, DashboardFavorite
from src.modules.dashboards.services import DashboardService
from src.modules.dashboards.schemas import DashboardCreate, WidgetCreate, LayoutUpdate, LayoutItem


@pytest.mark.asyncio
async def test_dashboard_creation_and_widgets_crud(db_session: AsyncSession):
    """
    Test creation of dashboard and addition/modification of widgets.
    """
    org_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # 1. Create Dashboard
    schema = DashboardCreate(
        name="Sales Operations",
        description="SaaS key metrics visual analytics board",
        category="Sales"
    )
    dashboard = await DashboardService.create_dashboard(
        db=db_session,
        org_id=org_id,
        workspace_id=workspace_id,
        creator_id=user_id,
        schema=schema
    )
    assert dashboard.name == "Sales Operations"
    assert dashboard.version == 1

    # 2. Add Widget (Dummy Dataset ID mapping)
    dummy_dataset_id = uuid.uuid4()
    # Create fake dataset row to satisfy foreign key constraint
    from src.modules.datasets.models import Dataset
    fake_dataset = Dataset(
        id=dummy_dataset_id,
        organization_id=org_id,
        workspace_id=workspace_id,
        name="Fake Ingestion Source",
        format="CSV",
        storage_path="datasets/fake.csv"
    )
    db_session.add(fake_dataset)
    await db_session.commit()

    widget_schema = WidgetCreate(
        dataset_id=dummy_dataset_id,
        dataset_version=1,
        title="Monthly Revenue KPI",
        widget_type="KPI Card",
        aggregation="SUM",
        y_axis_column="revenue"
    )
    widget = await DashboardService.add_widget(
        db=db_session,
        dashboard_id=dashboard.id,
        schema=widget_schema,
        user_id=user_id
    )
    assert widget.title == "Monthly Revenue KPI"
    assert widget.widget_type == "KPI Card"

    # Verify default layout item created alongside widget
    lay_query = select(DashboardLayout).where(DashboardLayout.widget_id == widget.id)
    lay_res = await db_session.execute(lay_query)
    layout = lay_res.scalar_one()
    assert layout.width == 4
    assert layout.height == 3


@pytest.mark.asyncio
async def test_dashboard_cloning(db_session: AsyncSession):
    """
    Verify cloning duplicating widgets configurations and layouts mappings.
    """
    # Query the dashboard created in earlier test
    q = select(Dashboard).where(Dashboard.is_deleted == False)
    res = await db_session.execute(q)
    dashboard = res.scalars().first()
    if not dashboard:
        return

    cloned = await DashboardService.clone_dashboard(
        db=db_session,
        dashboard_id=dashboard.id,
        user_id=uuid.uuid4()
    )
    assert cloned is not None
    assert "Sales Operations - Copy" in cloned.name
    assert len(cloned.widgets) == len(dashboard.widgets)
    assert len(cloned.layouts) == len(dashboard.layouts)


@pytest.mark.asyncio
async def test_favorites_and_layout_coordinate_saves(db_session: AsyncSession):
    """
    Test coordinate maps updates and favorites logs toggling.
    """
    q = select(Dashboard).where(Dashboard.is_deleted == False).options(selectinload(Dashboard.widgets))
    res = await db_session.execute(q)
    dashboard = res.scalars().first()
    if not dashboard or len(dashboard.widgets) == 0:
        return

    # Toggle favorite
    user_id = uuid.uuid4()
    fav_success = await DashboardService.toggle_favorite(
        db=db_session,
        dashboard_id=dashboard.id,
        user_id=user_id,
        is_favorite=True
    )
    assert fav_success is True

    # Assert favorite saved
    fav_q = select(DashboardFavorite).where(
        DashboardFavorite.dashboard_id == dashboard.id,
        DashboardFavorite.user_id == user_id
    )
    fav_res = await db_session.execute(fav_q)
    assert fav_res.scalar_one_or_none() is not None

    # Save Layout Coordinates
    w_id = dashboard.widgets[0].id
    layout_update = LayoutUpdate(
        layout_items=[
            LayoutItem(widget_id=w_id, pos_x=2, pos_y=2, width=6, height=4)
        ]
    )
    lay_success = await DashboardService.update_layout(
        db=db_session,
        dashboard_id=dashboard.id,
        schema=layout_update,
        user_id=user_id
    )
    assert lay_success is True
