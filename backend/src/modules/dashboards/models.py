import datetime
import uuid
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UUID, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base


class Dashboard(Base):
    __tablename__ = "dashboards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Draft", nullable=False)  # Draft, Published, Archived
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    template_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Relationships
    widgets: Mapped[List["DashboardWidget"]] = relationship(
        "DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan"
    )
    layouts: Mapped[List["DashboardLayout"]] = relationship(
        "DashboardLayout", back_populates="dashboard", cascade="all, delete-orphan"
    )
    shares: Mapped[List["DashboardShare"]] = relationship(
        "DashboardShare", back_populates="dashboard", cascade="all, delete-orphan"
    )
    favorites: Mapped[List["DashboardFavorite"]] = relationship(
        "DashboardFavorite", back_populates="dashboard", cascade="all, delete-orphan"
    )


class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataset_version: Mapped[int] = mapped_column(Integer, nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    widget_type: Mapped[str] = mapped_column(String(50), nullable=False)  # KPI, Table, Line, Bar, Pie, Donut, Area, Scatter, Histogram, Heatmap, Box, Gauge, Funnel, Treemap
    
    x_axis_column: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    y_axis_column: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    aggregation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # COUNT, SUM, AVG, MEDIAN, MIN, MAX
    filters_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sorting_column: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    color_theme: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    refresh_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )

    dashboard: Mapped[Dashboard] = relationship(back_populates="widgets")
    layouts: Mapped[List["DashboardLayout"]] = relationship(
        "DashboardLayout", back_populates="widget", cascade="all, delete-orphan"
    )


class DashboardLayout(Base):
    __tablename__ = "dashboard_layouts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    widget_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dashboard_widgets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    pos_x: Mapped[int] = mapped_column(Integer, nullable=False)
    pos_y: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )

    dashboard: Mapped[Dashboard] = relationship(back_populates="layouts")
    widget: Mapped[DashboardWidget] = relationship(back_populates="layouts")


class DashboardShare(Base):
    __tablename__ = "dashboard_shares"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    share_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PRIVATE, WORKSPACE, ORGANIZATION, PUBLIC
    share_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )

    dashboard: Mapped[Dashboard] = relationship(back_populates="shares")


class DashboardFavorite(Base):
    __tablename__ = "dashboard_favorites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )

    dashboard: Mapped[Dashboard] = relationship(back_populates="favorites")
