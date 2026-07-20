import uuid
import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations_json: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: str = Field("New Conversation", min_length=1)


class ConversationRename(BaseModel):
    title: str = Field(..., min_length=1)


class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    is_pinned: bool
    is_deleted: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class SQLQueryRequest(BaseModel):
    question: str = Field(..., min_length=5)
    dataset_id: uuid.UUID


class SQLQueryResponse(BaseModel):
    generated_sql: str
    explanation: str
    columns: List[str]
    results: List[Dict[str, Any]]
    execution_time_ms: int


class AIInsightsRequest(BaseModel):
    dataset_id: uuid.UUID


class AIInsightsResponse(BaseModel):
    structured_json: Dict[str, Any]
    formatted_text: str


class ChartRecommendationRequest(BaseModel):
    dataset_id: uuid.UUID


class ChartRecommendationResponse(BaseModel):
    recommended_chart_type: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    aggregation: Optional[str] = None
    confidence_score: float
    reasoning: str
