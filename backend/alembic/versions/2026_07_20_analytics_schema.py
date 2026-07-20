"""Create Reports sections scheduled exports predictions and model metadata tables

Revision ID: 9fd992a047bf
Revises: afd992a047bf
Create Date: 2026-07-20 20:40:00.000000

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fd992a047bf'
down_revision: Union[str, None] = 'afd992a047bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Reports Table
    op.create_table(
        'reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('creator_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('is_template', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('template_name', sa.String(length=255), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_creator_id'), 'reports', ['creator_id'], unique=False)
    op.create_index(op.f('ix_reports_organization_id'), 'reports', ['organization_id'], unique=False)
    op.create_index(op.f('ix_reports_workspace_id'), 'reports', ['workspace_id'], unique=False)

    # 2. Create Report Sections Table
    op.create_table(
        'report_sections',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('report_id', sa.UUID(), nullable=False),
        sa.Column('section_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('source_widget_id', sa.UUID(), nullable=True),
        sa.Column('source_dataset_id', sa.UUID(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_dataset_id'], ['datasets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_sections_report_id'), 'report_sections', ['report_id'], unique=False)

    # 3. Create Scheduled Reports Table
    op.create_table(
        'scheduled_reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('report_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('schedule_type', sa.String(length=50), nullable=False),
        sa.Column('cron_expression', sa.String(length=100), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('recipients_emails_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduled_reports_report_id'), 'scheduled_reports', ['report_id'], unique=False)

    # 4. Create Report History Table
    op.create_table(
        'report_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('report_id', sa.UUID(), nullable=True),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('export_format', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Queued'),
        sa.Column('storage_path', sa.String(length=512), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_history_report_id'), 'report_history', ['report_id'], unique=False)
    op.create_index(op.f('ix_report_history_workspace_id'), 'report_history', ['workspace_id'], unique=False)

    # 5. Create Prediction Jobs Table
    op.create_table(
        'prediction_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('creator_id', sa.UUID(), nullable=True),
        sa.Column('algorithm', sa.String(length=100), nullable=False),
        sa.Column('target_column', sa.String(length=255), nullable=False),
        sa.Column('parameters_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Queued'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prediction_jobs_workspace_id'), 'prediction_jobs', ['workspace_id'], unique=False)

    # 6. Create Prediction Results Table
    op.create_table(
        'prediction_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prediction_job_id', sa.UUID(), nullable=False),
        sa.Column('predictions_json', sa.JSON(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('metrics_json', sa.JSON(), nullable=True),
        sa.Column('feature_importance_json', sa.JSON(), nullable=True),
        sa.Column('plain_explanation', sa.Text(), nullable=False),
        sa.Column('limitations', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['prediction_job_id'], ['prediction_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prediction_results_prediction_job_id'), 'prediction_results', ['prediction_job_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_prediction_results_prediction_job_id'), table_name='prediction_results')
    op.drop_table('prediction_results')

    op.drop_index(op.f('ix_prediction_jobs_workspace_id'), table_name='prediction_jobs')
    op.drop_table('prediction_jobs')

    op.drop_index(op.f('ix_report_history_workspace_id'), table_name='report_history')
    op.drop_index(op.f('ix_report_history_report_id'), table_name='report_history')
    op.drop_table('report_history')

    op.drop_index(op.f('ix_scheduled_reports_report_id'), table_name='scheduled_reports')
    op.drop_table('scheduled_reports')

    op.drop_index(op.f('ix_report_sections_report_id'), table_name='report_sections')
    op.drop_table('report_sections')

    op.drop_index(op.f('ix_reports_workspace_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_organization_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_creator_id'), table_name='reports')
    op.drop_table('reports')
