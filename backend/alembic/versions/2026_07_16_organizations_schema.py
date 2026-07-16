"""Create organizations workspaces and membership tables

Revision ID: bfd992a047bf
Revises: 9a8b7c6d5e4f
Create Date: 2026-07-16 16:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfd992a047bf'
down_revision: Union[str, None] = '9a8b7c6d5e4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Organizations Table
    op.create_table(
        'organizations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # 2. Create Workspaces Table
    op.create_table(
        'workspaces',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'slug', name='uq_workspace_org_slug')
    )
    op.create_index(op.f('ix_workspaces_organization_id'), 'workspaces', ['organization_id'], unique=False)

    # 3. Create Workspace Members Table
    op.create_table(
        'workspace_members',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('workspace_role', sa.String(length=50), nullable=False, server_default='WS_VIEWER'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_user_member')
    )
    op.create_index(op.f('ix_workspace_members_user_id'), 'workspace_members', ['user_id'], unique=False)
    op.create_index(op.f('ix_workspace_members_workspace_id'), 'workspace_members', ['workspace_id'], unique=False)

    # 4. Alter Users Table to add organization_id Foreign Key
    op.create_foreign_key(
        'fk_users_organization',
        'users',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Remove FK from users table
    op.drop_constraint('fk_users_organization', 'users', type_='foreignkey')

    op.drop_index(op.f('ix_workspace_members_workspace_id'), table_name='workspace_members')
    op.drop_index(op.f('ix_workspace_members_user_id'), table_name='workspace_members')
    op.drop_table('workspace_members')

    op.drop_index(op.f('ix_workspaces_organization_id'), table_name='workspaces')
    op.drop_table('workspaces')

    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_table('organizations')
