import uuid
import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WidgetCreate(BaseModel):
    dataset_id: uuid.UUID
    dataset_version: int = 1
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    widget_type: str = Field(..., pattern="^(KPI|Table|Line Chart|Bar Chart|Pie Chart|Donut Chart|Area Chart|Scatter Plot|Histogram|Heatmap|Box Plot|Gauge|Funnel|Treemap)$")
    x_axis_column: Optional[str] = None
    y_axis_column: Optional[str] = None
    aggregation: Optional[str] = Field(None, pattern="^(COUNT|SUM|AVG|MEDIAN|MIN|MAX)$")
    filters_json: Optional[Dict[str, Any]] = None
    sorting_column: Optional[str] = None
    color_theme: Optional[str] = None
    refresh_interval: Optional[int] = Field(None, ge=10)  # Min 10s


class WidgetUpdate(BaseModel):
    dataset_id: Optional[uuid.UUID] = None
    dataset_version: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    widget_type: Optional[str] = None
    x_axis_column: Optional[str] = None
    y_axis_column: Optional[str] = None
    aggregation: Optional[str] = None
    filters_json: Optional[Dict[str, Any]] = None
    sorting_column: Optional[str] = None
    color_theme: Optional[str] = None
    refresh_interval: Optional[int] = None


class WidgetResponse(BaseModel):
    id: uuid.UUID
    dashboard_id: uuid.UUID
    dataset_id: uuid.UUID
    dataset_version: int
    title: str
    description: Optional[str] = None
    widget_type: str
    x_axis_column: Optional[str] = None
    y_axis_column: Optional[str] = None
    aggregation: Optional[str] = None
    filters_json: Optional[Dict[str, Any]] = None
    sorting_column: Optional[str] = None
    color_theme: Optional[str] = None
    refresh_interval: Optional[int] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class LayoutItem(BaseModel):
    widget_id: uuid.UUID
    pos_x: int = Field(..., ge=0)
    pos_y: int = Field(..., ge=0)
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)


class LayoutUpdate(BaseModel):
    layout_items: List[LayoutItem]


class LayoutItemResponse(BaseModel):
    id: uuid.UUID
    widget_id: uuid.UUID
    pos_x: int
    pos_y: int
    width: int
    height: int

    class Config:
        from_attributes = True


class DashboardCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    category: Optional[str] = None
    is_template: bool = False
    template_name: Optional[str] = None


class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(Draft|Published|Archived)$")
    category: Optional[str] = None
    is_template: Optional[bool] = None


class DashboardResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    creator_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    status: str
    category: Optional[str] = None
    is_template: bool
    template_name: Optional[str] = None
    version: int
    is_deleted: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    widgets: List[WidgetResponse] = []
    layouts: List[LayoutItemResponse] = []

    class Config:
        from_attributes = True


class DashboardShareResponse(BaseModel):
    id: uuid.UUID
    dashboard_id: uuid.UUID
    share_type: str
    share_token: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class DashboardTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    template_name: str
    category: Optional[str] = None
