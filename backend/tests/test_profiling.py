import pytest
import io
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.datasets.models import Dataset
from src.modules.profiling.models import DatasetProfile, ColumnProfile, QualityReport, Recommendation
from src.modules.profiling.services import ProfilingService
from src.modules.profiling.tasks import async_profile_dataset as async_profile_dataset_task


@pytest.fixture
def mock_storage_get_profiling():
    with patch("src.core.storage.storage_manager.client.get_object") as mock:
        mock_response = MagicMock()
        mock_response.read.return_value = (
            b"id,email,age,bio,created\n"
            b"1,user1@datasense.ai,25,Analyst,2026-01-01\n"
            b"2,user2@datasense.ai,30,Scientist,2026-01-02\n"
            b"3,user3@datasense.ai,35,Lead,2026-01-03\n"
            b"4,invalid_email,40,,2026-01-04\n"
            b"5,user5@datasense.ai,200,Director,2026-01-05\n"  # 200 is Z-Score & IQR outlier
        )
        mock.return_value = mock_response
        yield mock


@pytest.mark.asyncio
async def test_dataset_profiling_calculations(
    db_session: AsyncSession,
    mock_storage_get_profiling
):
    """
    Test direct execution of profiling calculations, checking IQR and numeric/text stats.
    """
    # 1. Create organization and workspace mapping
    org_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    
    dataset = Dataset(
        id=uuid.uuid4(),
        organization_id=org_id,
        workspace_id=workspace_id,
        name="User Cohort Dataset",
        format="CSV",
        storage_path="datasets/dummy_users.csv"
    )
    db_session.add(dataset)
    await db_session.commit()
    await db_session.refresh(dataset)

    # 2. Trigger async profiling job directly
    await async_profile_dataset_task(
        dataset_id=dataset.id,
        version_number=1,
        user_id=None
    )

    # 3. Query DatasetProfile details
    q = select(DatasetProfile).where(
        DatasetProfile.dataset_id == dataset.id,
        DatasetProfile.version_number == 1
    ).options(selectinload(DatasetProfile.column_profiles))
    res = await db_session.execute(q)
    profile = res.scalar_one()

    assert profile.rows_count == 5
    assert profile.columns_count == 5
    assert profile.missing_values == 1  # empty bio string in row 4

    # 4. Assert Column stats (Numeric check)
    age_col = next(c for c in profile.column_profiles if c.column_name == "age")
    assert age_col.mean_val == 66.0  # (25 + 30 + 35 + 40 + 200) / 5
    assert age_col.min_val == "20"  # sorted string min or numeric representation checks
    assert age_col.percentiles_json is not None
    assert age_col.percentiles_json["50"] == 35.0  # Median
    assert age_col.outliers_count == 1  # 200 age is outlier

    # 5. Assert Column stats (Text check)
    bio_col = next(c for c in profile.column_profiles if c.column_name == "bio")
    assert bio_col.avg_length is not None
    assert bio_col.avg_length > 0
    assert bio_col.missing_count == 1

    # 6. Verify Quality Report overall scores mapping
    q_rep = select(QualityReport).where(
        QualityReport.dataset_id == dataset.id,
        QualityReport.version_number == 1
    )
    q_res = await db_session.execute(q_rep)
    report = q_res.scalar_one()
    assert report.completeness_score == 96.0  # 24 cells / 25 cells * 100
    assert report.overall_score > 0.0

    # 7. Verify recommendations seeded
    rec_q = select(Recommendation).where(
        Recommendation.dataset_id == dataset.id,
        Recommendation.version_number == 1
    )
    rec_res = await db_session.execute(rec_q)
    recs = list(rec_res.scalars().all())
    assert len(recs) > 0
    # Check outlier warning category
    assert any(r.category == "Outliers" for r in recs)


@pytest.mark.asyncio
async def test_drift_calculations(
    db_session: AsyncSession,
    mock_storage_get_profiling
):
    """
    Test version quality difference drift assertions.
    """
    # Grab previous test context dataset
    query = select(Dataset)
    result = await db_session.execute(query)
    dataset = result.scalars().first()
    if not dataset:
        return

    # Trigger second version ingestion simulation
    await async_profile_dataset_task(
        dataset_id=dataset.id,
        version_number=2,
        user_id=None
    )

    q = select(QualityReport).where(
        QualityReport.dataset_id == dataset.id,
        QualityReport.version_number == 2
    )
    res = await db_session.execute(q)
    report = res.scalar_one()
    # Since the file did not change, quality_difference should be 0.0
    assert report.quality_difference == 0.0
    assert report.previous_version_number == 1
