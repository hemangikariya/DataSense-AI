"""Create RBAC roles permissions and audit logs tables and seed defaults

Revision ID: cfd992a047bf
Revises: bfd992a047bf
Create Date: 2026-07-20 19:35:00.000000

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cfd992a047bf'
down_revision: Union[str, None] = 'bfd992a047bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Permissions Table
    op.create_table(
        'permissions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)

    # 2. Create Roles Table
    op.create_table(
        'roles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('role_type', sa.String(length=50), nullable=False, server_default='WORKSPACE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)

    # 3. Create Role Permissions Association Table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.UUID(), nullable=False),
        sa.Column('permission_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # 4. Alter Users Table to add Profile Fields
    op.add_column('users', sa.Column('username', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('avatar_url', sa.String(length=512), nullable=True))
    op.add_column('users', sa.Column('bio', sa.String(length=1000), nullable=True))
    op.add_column('users', sa.Column('company', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('designation', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('timezone', sa.String(length=100), nullable=False, server_default='UTC'))
    op.add_column('users', sa.Column('language', sa.String(length=10), nullable=False, server_default='en'))
    op.add_column('users', sa.Column('theme_preference', sa.String(length=20), nullable=False, server_default='dark'))
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # 5. Create Audit Logs Table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('workspace_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_organization_id'), 'audit_logs', ['organization_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_workspace_id'), 'audit_logs', ['workspace_id'], unique=False)

    # 6. Seed Default Permissions & Roles Data
    seed_defaults()


def seed_defaults() -> None:
    # Build list of permissions
    permissions_list = [
        ("organization:create", "Create new organizations"),
        ("organization:update", "Update organization configurations"),
        ("organization:delete", "Delete organization settings"),
        ("workspace:create", "Create workspaces"),
        ("workspace:update", "Update workspace layouts"),
        ("workspace:delete", "Delete workspaces"),
        ("dataset:create", "Ingest and process datasets"),
        ("dataset:read", "Read dataset metadata profiles"),
        ("dataset:update", "Modify or clean dataset records"),
        ("dataset:delete", "Delete dataset targets"),
        ("dashboard:create", "Build dashboard canvases"),
        ("dashboard:update", "Update dashboard grids"),
        ("dashboard:delete", "Remove dashboard records"),
        ("dashboard:read", "Read dashboards layout configurations"),
        ("report:create", "Generate dynamic PDF/Excel exports"),
        ("report:download", "Download report archives"),
        ("user:invite", "Invite users to organization workspaces"),
        ("user:update", "Update user roles mapping"),
        ("user:remove", "Revoke workspace members permissions"),
        ("profile:update", "Update profile configurations"),
        ("ai:chat", "Interact with Conversational BI"),
        ("roles:read", "List configured roles"),
        ("roles:write", "CRUD custom system roles"),
        ("permissions:read", "List available permissions")
    ]

    permission_id_map = {}
    for name, desc in permissions_list:
        p_id = str(uuid.uuid4())
        permission_id_map[name] = p_id
        op.execute(
            f"INSERT INTO permissions (id, name, description) VALUES ('{p_id}', '{name}', '{desc}')"
        )

    # Build default roles configuration matrix mapping
    roles_matrix = {
        "SUPER_ADMIN": ("SYSTEM", list(permission_id_map.keys())),
        "ORG_OWNER": ("ORGANIZATION", [
            "organization:update", "organization:delete", "workspace:create", "workspace:update",
            "workspace:delete", "user:invite", "user:remove", "user:update", "profile:update", "ai:chat"
        ]),
        "ORG_ADMIN": ("ORGANIZATION", [
            "organization:update", "workspace:create", "workspace:update", "workspace:delete",
            "user:invite", "user:remove", "user:update", "profile:update", "ai:chat"
        ]),
        "ORG_MEMBER": ("ORGANIZATION", [
            "profile:update", "ai:chat"
        ]),
        "WS_ADMIN": ("WORKSPACE", [
            "workspace:update", "dataset:create", "dataset:read", "dataset:update", "dataset:delete",
            "dashboard:create", "dashboard:update", "dashboard:delete", "report:create", "report:download", "ai:chat"
        ]),
        "WS_ANALYST": ("WORKSPACE", [
            "dataset:read", "dataset:update", "dashboard:create", "dashboard:update", "report:create",
            "report:download", "ai:chat"
        ]),
        "WS_VIEWER": ("WORKSPACE", [
            "dataset:read", "dashboard:read", "report:download"
        ])
    }

    for role_name, (role_type, permissions_names) in roles_matrix.items():
        role_id = str(uuid.uuid4())
        op.execute(
            f"INSERT INTO roles (id, name, description, role_type) VALUES ('{role_id}', '{role_name}', 'Default {role_name} Role', '{role_type}')"
        )
        for name in permissions_names:
            p_id = permission_id_map[name]
            op.execute(
                f"INSERT INTO role_permissions (role_id, permission_id) VALUES ('{role_id}', '{p_id}')"
            )


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_workspace_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_organization_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'theme_preference')
    op.drop_column('users', 'language')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'designation')
    op.drop_column('users', 'company')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'username')

    op.drop_table('role_permissions')
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_table('roles')
    op.drop_index(op.f('ix_permissions_name'), table_name='permissions')
    op.drop_table('permissions')
