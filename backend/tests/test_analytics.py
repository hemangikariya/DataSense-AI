import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.analytics.models import Report, ReportSection, ScheduledReport, ReportHistory, PredictionJob, PredictionResult
from src.modules.analytics.services import AnalyticsService
from src.modules.analytics.schemas import ReportCreate, ReportSectionCreate, ScheduledReportCreate, PredictionJobCreate


@pytest.mark.asyncio
async def test_report_creation_and_layout_sections(db_session: AsyncSession):
    """
    Test registering multi-section reports layouts.
    """
    org_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()

    schema = ReportCreate(
        name="Q3 Executive Board Report",
        description="Comprehensive summary metrics with prediction forecast lines",
        category="Executive",
        sections=[
            ReportSectionCreate(
                section_type="TEXT",
                title="Executive Summary Overview",
                content_text="Detailed financial throughput overview of current quarter transactions.",
                sort_order=1
            ),
            ReportSectionCreate(
                section_type="KPI",
                title="Total Projected revenue",
                sort_order=2
            )
        ]
    )

    report = await AnalyticsService.create_report(
        db=db_session,
        org_id=org_id,
        workspace_id=workspace_id,
        creator_id=user_id,
        schema=schema
    )
    assert report.name == "Q3 Executive Board Report"
    assert len(report.sections) == 2
    assert report.sections[0].section_type == "TEXT"


@pytest.mark.asyncio
async def test_report_export_trigger(db_session: AsyncSession):
    """
    Test triggering reports export task and registering audit logs histories.
    """
    # Query report created in previous test
    q = select(Report).where(Report.is_deleted == False)
    res = await db_session.execute(q)
    report = res.scalars().first()
    if not report:
        return

    user_id = uuid.uuid4()
    history = await AnalyticsService.export_report(
        db=db_session,
        report_id=report.id,
        export_format="PDF",
        user_id=user_id,
        workspace_id=report.workspace_id
    )
    assert history.status == "Queued"
    assert history.export_format == "PDF"


@pytest.mark.asyncio
async def test_run_ml_prediction_forecasting(db_session: AsyncSession):
    """
    Test registering linear time series trends forecast jobs.
    """
    org_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    # Create dummy dataset to link prediction
    from src.modules.datasets.models import Dataset
    dataset = Dataset(
        id=uuid.uuid4(),
        organization_id=org_id,
        workspace_id=workspace_id,
        name="Predictive Metrics Dataset",
        format="CSV",
        storage_path="datasets/dummy_predict.csv"
    )
    db_session.add(dataset)
    await db_session.commit()

    schema = PredictionJobCreate(
        dataset_id=dataset.id,
        algorithm="Linear Regression",
        target_column="sales"
    )

    job = await AnalyticsService.run_prediction(
        db=db_session,
        workspace_id=workspace_id,
        creator_id=uuid.uuid4(),
        schema=schema
    )
    assert job.status == "Queued"
    assert job.algorithm == "Linear Regression"
