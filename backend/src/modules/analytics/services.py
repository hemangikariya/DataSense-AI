import uuid
import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.analytics.models import Report, ReportSection, ScheduledReport, ReportHistory, PredictionJob, PredictionResult
from src.modules.analytics.schemas import ReportCreate, ScheduledReportCreate, PredictionJobCreate
from src.modules.auth.services import AuditLogService
from src.modules.analytics.tasks import generate_pdf_report_task, run_prediction_task


class AnalyticsService:
    @staticmethod
    async def create_report(
        db: AsyncSession,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID,
        creator_id: uuid.UUID,
        schema: ReportCreate,
        request_ip: Optional[str] = None
    ) -> Report:
        report = Report(
            organization_id=org_id,
            workspace_id=workspace_id,
            creator_id=creator_id,
            name=schema.name,
            description=schema.description,
            category=schema.category
        )
        db.add(report)
        await db.flush()

        for idx, sec in enumerate(schema.sections):
            section = ReportSection(
                report_id=report.id,
                section_type=sec.section_type,
                title=sec.title,
                content_text=sec.content_text,
                source_widget_id=sec.source_widget_id,
                source_dataset_id=sec.source_dataset_id,
                sort_order=sec.sort_order or idx
            )
            db.add(section)

        await AuditLogService.log_event(
            db, user_id=creator_id, org_id=org_id, workspace_id=workspace_id, action="REPORT_CREATE", ip_address=request_ip
        )
        await db.commit()
        
        # Load fully populated report response details
        return await AnalyticsService.get_report(db, report.id)

    @staticmethod
    async def get_report(db: AsyncSession, report_id: uuid.UUID) -> Optional[Report]:
        query = select(Report).where(
            Report.id == report_id, Report.is_deleted == False
        ).options(
            selectinload(Report.sections)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_report(
        db: AsyncSession,
        report_id: uuid.UUID,
        schema: ReportCreate,
        user_id: uuid.UUID,
        request_ip: Optional[str] = None
    ) -> Optional[Report]:
        report = await AnalyticsService.get_report(db, report_id)
        if not report:
            return None

        report.name = schema.name
        report.description = schema.description
        report.category = schema.category

        # Drop old sections
        stmt = delete(ReportSection).where(ReportSection.report_id == report_id)
        await db.execute(stmt)

        # Write new sections list
        for idx, sec in enumerate(schema.sections):
            section = ReportSection(
                report_id=report_id,
                section_type=sec.section_type,
                title=sec.title,
                content_text=sec.content_text,
                source_widget_id=sec.source_widget_id,
                source_dataset_id=sec.source_dataset_id,
                sort_order=sec.sort_order or idx
            )
            db.add(section)

        await AuditLogService.log_event(
            db, user_id=user_id, org_id=report.organization_id, workspace_id=report.workspace_id, action="REPORT_UPDATE", ip_address=request_ip
        )
        await db.commit()
        return await AnalyticsService.get_report(db, report_id)

    @staticmethod
    async def delete_report(
        db: AsyncSession, report_id: uuid.UUID, user_id: uuid.UUID, request_ip: Optional[str] = None
    ) -> bool:
        report = await AnalyticsService.get_report(db, report_id)
        if not report:
            return False

        report.is_deleted = True
        await AuditLogService.log_event(
            db, user_id=user_id, org_id=report.organization_id, workspace_id=report.workspace_id, action="REPORT_DELETE", ip_address=request_ip
        )
        await db.commit()
        return True

    @staticmethod
    async def list_reports(db: AsyncSession, workspace_id: uuid.UUID, page: int = 1, page_size: int = 20) -> List[Report]:
        query = select(Report).where(
            Report.workspace_id == workspace_id,
            Report.is_deleted == False
        ).order_by(Report.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def export_report(
        db: AsyncSession,
        report_id: uuid.UUID,
        export_format: str,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request_ip: Optional[str] = None
    ) -> ReportHistory:
        """
        Enqueues background Celery task for PDF compilation.
        """
        history = ReportHistory(
            report_id=report_id,
            workspace_id=workspace_id,
            export_format=export_format,
            status="Queued"
        )
        db.add(history)
        await db.flush()

        # Trigger background task asynchronously
        generate_pdf_report_task.delay(str(history.id), str(report_id))

        await AuditLogService.log_event(
            db, user_id=user_id, org_id=None, workspace_id=workspace_id, action="REPORT_EXPORT", ip_address=request_ip
        )
        await db.commit()
        return history

    @staticmethod
    async def schedule_report(
        db: AsyncSession,
        report_id: uuid.UUID,
        workspace_id: uuid.UUID,
        schema: ScheduledReportCreate,
        user_id: uuid.UUID,
        request_ip: Optional[str] = None
    ) -> ScheduledReport:
        schedule = ScheduledReport(
            report_id=report_id,
            workspace_id=workspace_id,
            schedule_type=schema.schedule_type,
            cron_expression=schema.cron_expression,
            timezone=schema.timezone,
            is_enabled=schema.is_enabled,
            recipients_emails_json=schema.recipients_emails_json
        )
        db.add(schedule)
        await AuditLogService.log_event(
            db, user_id=user_id, org_id=None, workspace_id=workspace_id, action="REPORT_SCHEDULE", ip_address=request_ip
        )
        await db.commit()
        return schedule

    @staticmethod
    async def list_exports_history(db: AsyncSession, workspace_id: uuid.UUID) -> List[ReportHistory]:
        query = select(ReportHistory).where(ReportHistory.workspace_id == workspace_id).order_by(ReportHistory.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def list_templates(db: AsyncSession) -> List[Report]:
        query = select(Report).where(Report.is_template == True, Report.is_deleted == False)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def run_prediction(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        creator_id: uuid.UUID,
        schema: PredictionJobCreate,
        request_ip: Optional[str] = None
    ) -> PredictionJob:
        job = PredictionJob(
            workspace_id=workspace_id,
            dataset_id=schema.dataset_id,
            creator_id=creator_id,
            algorithm=schema.algorithm,
            target_column=schema.target_column,
            parameters_json=schema.parameters_json,
            status="Queued"
        )
        db.add(job)
        await db.flush()

        # Trigger Celery forecast background execution
        run_prediction_task.delay(str(job.id))

        await AuditLogService.log_event(
            db, user_id=creator_id, org_id=None, workspace_id=workspace_id, action="PREDICTION_REQUEST", ip_address=request_ip
        )
        await db.commit()
        return job

    @staticmethod
    async def get_prediction(db: AsyncSession, job_id: uuid.UUID) -> Optional[PredictionJob]:
        query = select(PredictionJob).where(PredictionJob.id == job_id).options(selectinload(PredictionJob.results))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_predictions(db: AsyncSession, workspace_id: uuid.UUID) -> List[PredictionJob]:
        query = select(PredictionJob).where(PredictionJob.workspace_id == workspace_id).order_by(PredictionJob.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())
