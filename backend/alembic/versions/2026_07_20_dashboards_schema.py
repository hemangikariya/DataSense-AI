"""Create Dashboards widgets layouts shares and favorites tables

Revision ID: ffd992a047bf
Revises: efd992a047bf
Create Date: 2026-07-20 20:20:00.000000

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffd992a047bf'
down_revision: Union[str, None] = 'efd992a047bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Dashboards Table
    op.create_table(
        'dashboards',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('creator_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Draft'),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('is_template', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('template_name', sa.String(length=255), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboards_creator_id'), 'dashboards', ['creator_id'], unique=False)
    op.create_index(op.f('ix_dashboards_organization_id'), 'dashboards', ['organization_id'], unique=False)
    op.create_index(op.f('ix_dashboards_workspace_id'), 'dashboards', ['workspace_id'], unique=False)

    # 2. Create Dashboard Widgets Table
    op.create_table(
        'dashboard_widgets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dashboard_id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('dataset_version', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('widget_type', sa.String(length=50), nullable=False),
        sa.Column('x_axis_column', sa.String(length=255), nullable=True),
        sa.Column('y_axis_column', sa.String(length=255), nullable=True),
        sa.Column('aggregation', sa.String(length=50), nullable=True),
        sa.Column('filters_json', sa.JSON(), nullable=True),
        sa.Column('sorting_column', sa.String(length=255), nullable=True),
        sa.Column('color_theme', sa.String(length=50), nullable=True),
        sa.Column('refresh_interval', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['dashboard_id'], ['dashboards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_widgets_dashboard_id'), 'dashboard_widgets', ['dashboard_id'], unique=False)

    # 3. Create Dashboard Layouts Table
    op.create_table(
        'dashboard_layouts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dashboard_id', sa.UUID(), nullable=False),
        sa.Column('widget_id', sa.UUID(), nullable=False),
        sa.Column('pos_x', sa.Integer(), nullable=False),
        sa.Column('pos_y', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['dashboard_id'], ['dashboards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['widget_id'], ['dashboard_widgets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_layouts_dashboard_id'), 'dashboard_layouts', ['dashboard_id'], unique=False)

    # 4. Create Dashboard Shares Table
    op.create_table(
        'dashboard_shares',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dashboard_id', sa.UUID(), nullable=False),
        sa.Column('share_type', sa.String(length=50), nullable=False),
        sa.Column('share_token', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['dashboard_id'], ['dashboards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_shares_dashboard_id'), 'dashboard_shares', ['dashboard_id'], unique=False)
    op.create_index(op.f('ix_dashboard_shares_share_token'), 'dashboard_shares', ['share_token'], unique=True)

    # 5. Create Dashboard Favorites Table
    op.create_table(
        'dashboard_favorites',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dashboard_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['dashboard_id'], ['dashboards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Seed Default built-in templates
    seed_templates()


def seed_templates() -> None:
    templates = [
        ("Sales Dashboard", "Sales and transaction key KPI targets tracker", "Sales"),
        ("Marketing Dashboard", "Campaign reach and lead generation trends analysis", "Marketing"),
        ("Finance Dashboard", "P&L tracking and cost breakdown sheets", "Finance"),
        ("HR Dashboard", "Employee retention rate and onboarding logs", "HR"),
        ("Operations Dashboard", "Logistics pipelines and delivery throughput analytics", "Operations"),
        ("Blank Dashboard", "Custom canvas dashboard configuration layout", "Blank")
    ]
    # In postgres context we can seed with UUID values (organization_id and workspace_id can be dummy zeros for global templates)
    dummy_org = "00000000-0000-0000-0000-000000000000"
    dummy_ws = "00000000-0000-0000-0000-000000000000"
    
    # We bypass foreign keys on global templates by seeding them on actual application run,
    # or creating them without organization check constraints if nullable. But since organization_id
    # is NOT NULL, let's keep them as user templates, or the service will insert them dynamically.
    # To keep it completely standard and crash-proof, we don't insert invalid FK uuids here.
    # The application initialization or migrations should run when actual ORG exists,
    # so we will seed blank templates inside the database or service dynamically when workspace creates,
    # which is 100% safe.
    pass


def downgrade() -> None:
    op.drop_table('dashboard_favorites')
    op.drop_index(op.f('ix_dashboard_shares_share_token'), table_name='dashboard_shares')
    op.drop_index(op.f('ix_dashboard_shares_dashboard_id'), table_name='dashboard_shares')
    op.drop_table('dashboard_shares')

    op.drop_index(op.f('ix_dashboard_layouts_dashboard_id'), table_name='dashboard_layouts')
    op.drop_table('dashboard_layouts')

    op.drop_index(op.f('ix_dashboard_widgets_dashboard_id'), table_name='dashboard_widgets')
    op.drop_table('dashboard_widgets')

    op.drop_index(op.f('ix_dashboards_workspace_id'), table_name='dashboards')
    op.drop_index(op.f('ix_dashboards_organization_id'), table_name='dashboards')
    op.drop_index(op.f('ix_dashboards_creator_id'), table_name='dashboards')
    op.drop_table('dashboards')
