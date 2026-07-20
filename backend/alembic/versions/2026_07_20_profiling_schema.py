"""Create Profiling column profiles quality reports and recommendations tables

Revision ID: efd992a047bf
Revises: dfd992a047bf
Create Date: 2026-07-20 20:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efd992a047bf'
down_revision: Union[str, None] = 'dfd992a047bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Dataset Profiles Table
    op.create_table(
        'dataset_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('rows_count', sa.BigInteger(), nullable=False),
        sa.Column('columns_count', sa.Integer(), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('memory_usage', sa.BigInteger(), nullable=False),
        sa.Column('missing_values', sa.BigInteger(), nullable=False),
        sa.Column('duplicate_rows', sa.BigInteger(), nullable=False),
        sa.Column('correlation_matrix_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_profiles_dataset_id'), 'dataset_profiles', ['dataset_id'], unique=False)

    # 2. Create Column Profiles Table
    op.create_table(
        'column_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_profile_id', sa.UUID(), nullable=False),
        sa.Column('column_name', sa.String(length=255), nullable=False),
        sa.Column('data_type', sa.String(length=100), nullable=False),
        sa.Column('is_nullable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('unique_count', sa.BigInteger(), nullable=False),
        sa.Column('duplicate_count', sa.BigInteger(), nullable=False),
        sa.Column('missing_count', sa.BigInteger(), nullable=False),
        sa.Column('null_percentage', sa.Float(), nullable=False),
        sa.Column('cardinality', sa.Float(), nullable=False),
        sa.Column('min_val', sa.String(length=255), nullable=True),
        sa.Column('max_val', sa.String(length=255), nullable=True),
        sa.Column('mean_val', sa.Float(), nullable=True),
        sa.Column('median_val', sa.Float(), nullable=True),
        sa.Column('mode_val', sa.String(length=255), nullable=True),
        sa.Column('std_dev', sa.Float(), nullable=True),
        sa.Column('variance', sa.Float(), nullable=True),
        sa.Column('skewness', sa.Float(), nullable=True),
        sa.Column('kurtosis', sa.Float(), nullable=True),
        sa.Column('percentiles_json', sa.JSON(), nullable=True),
        sa.Column('avg_length', sa.Float(), nullable=True),
        sa.Column('max_length', sa.Integer(), nullable=True),
        sa.Column('min_length', sa.Integer(), nullable=True),
        sa.Column('empty_strings_count', sa.BigInteger(), nullable=True),
        sa.Column('earliest_date', sa.String(length=255), nullable=True),
        sa.Column('latest_date', sa.String(length=255), nullable=True),
        sa.Column('invalid_date_count', sa.BigInteger(), nullable=True),
        sa.Column('date_range', sa.String(length=255), nullable=True),
        sa.Column('sample_values_json', sa.JSON(), nullable=True),
        sa.Column('outliers_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('outliers_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.ForeignKeyConstraint(['dataset_profile_id'], ['dataset_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_column_profiles_dataset_profile_id'), 'column_profiles', ['dataset_profile_id'], unique=False)

    # 3. Create Quality Reports Table
    op.create_table(
        'quality_reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('completeness_score', sa.Float(), nullable=False),
        sa.Column('accuracy_score', sa.Float(), nullable=False),
        sa.Column('consistency_score', sa.Float(), nullable=False),
        sa.Column('validity_score', sa.Float(), nullable=False),
        sa.Column('uniqueness_score', sa.Float(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('previous_version_number', sa.Integer(), nullable=True),
        sa.Column('previous_quality_score', sa.Float(), nullable=True),
        sa.Column('quality_difference', sa.Float(), nullable=True),
        sa.Column('schema_changes_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quality_reports_dataset_id'), 'quality_reports', ['dataset_id'], unique=False)

    # 4. Create Recommendations Table
    op.create_table(
        'recommendations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('suggested_fix', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recommendations_dataset_id'), 'recommendations', ['dataset_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_recommendations_dataset_id'), table_name='recommendations')
    op.drop_table('recommendations')

    op.drop_index(op.f('ix_quality_reports_dataset_id'), table_name='quality_reports')
    op.drop_table('quality_reports')

    op.drop_index(op.f('ix_column_profiles_dataset_profile_id'), table_name='column_profiles')
    op.drop_table('column_profiles')

    op.drop_index(op.f('ix_dataset_profiles_dataset_id'), table_name='dataset_profiles')
    op.drop_table('dataset_profiles')
