"""Create Datasets versions metadata and tags tables

Revision ID: dfd992a047bf
Revises: cfd992a047bf
Create Date: 2026-07-20 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfd992a047bf'
down_revision: Union[str, None] = 'cfd992a047bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Datasets Table
    op.create_table(
        'datasets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('creator_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Uploading'),
        sa.Column('format', sa.String(length=10), nullable=False),
        sa.Column('storage_path', sa.String(length=512), nullable=False),
        sa.Column('hash', sa.String(length=64), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('parent_dataset_id', sa.UUID(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='UPLOAD'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_dataset_id'], ['datasets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_datasets_creator_id'), 'datasets', ['creator_id'], unique=False)
    op.create_index(op.f('ix_datasets_organization_id'), 'datasets', ['organization_id'], unique=False)
    op.create_index(op.f('ix_datasets_workspace_id'), 'datasets', ['workspace_id'], unique=False)

    # 2. Create Dataset Versions Table
    op.create_table(
        'dataset_versions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('storage_path', sa.String(length=512), nullable=False),
        sa.Column('hash', sa.String(length=64), nullable=False),
        sa.Column('change_log', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_versions_dataset_id'), 'dataset_versions', ['dataset_id'], unique=False)

    # 3. Create Dataset Metadata Table
    op.create_table(
        'dataset_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('rows_count', sa.BigInteger(), nullable=True),
        sa.Column('columns_count', sa.Integer(), nullable=True),
        sa.Column('schema_json', sa.JSON(), nullable=True),
        sa.Column('summary_stats_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dataset_id')
    )
    op.create_index(op.f('ix_dataset_metadata_dataset_id'), 'dataset_metadata', ['dataset_id'], unique=True)

    # 4. Create Dataset Tags Table
    op.create_table(
        'dataset_tags',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('tag_name', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_tags_dataset_id'), 'dataset_tags', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_dataset_tags_tag_name'), 'dataset_tags', ['tag_name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_dataset_tags_tag_name'), table_name='dataset_tags')
    op.drop_index(op.f('ix_dataset_tags_dataset_id'), table_name='dataset_tags')
    op.drop_table('dataset_tags')

    op.drop_index(op.f('ix_dataset_metadata_dataset_id'), table_name='dataset_metadata')
    op.drop_table('dataset_metadata')

    op.drop_index(op.f('ix_dataset_versions_dataset_id'), table_name='dataset_versions')
    op.drop_table('dataset_versions')

    op.drop_index(op.f('ix_datasets_workspace_id'), table_name='datasets')
    op.drop_index(op.f('ix_datasets_organization_id'), table_name='datasets')
    op.drop_index(op.f('ix_datasets_creator_id'), table_name='datasets')
    op.drop_table('datasets')
