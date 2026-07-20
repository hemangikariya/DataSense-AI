import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import (
    get_db,
    verify_workspace_access,
    get_authenticated_user_context,
    PermissionRequired
)
from src.modules.ai.schemas import (
    MessageCreate,
    MessageResponse,
    ConversationCreate,
    ConversationRename,
    ConversationResponse,
    SQLQueryRequest,
    SQLQueryResponse,
    AIInsightsRequest,
    AIInsightsResponse,
    ChartRecommendationRequest,
    ChartRecommendationResponse
)
from src.modules.ai.services import ChatService

router = APIRouter(prefix="/ai", tags=["Conversational BI & AI Insights"])


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(PermissionRequired("ai:chat"))])
async def create_conversation(
    schema: ConversationCreate,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new chat thread context.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    org_id = uuid.UUID(user_context.get("org_id"))
    ip_addr = request.client.host if request.client else None
    
    return await ChatService.create_conversation(
        db=db,
        org_id=org_id,
        workspace_id=workspace_id,
        user_id=user_id,
        title=schema.title,
        request_ip=ip_addr
    )


@router.get("/conversations", response_model=List[ConversationResponse], dependencies=[Depends(PermissionRequired("ai:chat"))])
async def list_conversations(
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists active chat thread conversations inside the workspace.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    return await ChatService.list_conversations(db, workspace_id, user_id)


@router.get("/conversations/{id}", response_model=ConversationResponse, dependencies=[Depends(PermissionRequired("ai:chat"))])
async def get_conversation_history(
    id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves full message logs of conversation.
    """
    conv = await ChatService.get_conversation(db, id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return conv


@router.put("/conversations/{id}", response_model=ConversationResponse, dependencies=[Depends(PermissionRequired("ai:chat"))])
async def rename_conversation(
    id: uuid.UUID,
    schema: ConversationRename,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates the title of the conversation.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    conv = await ChatService.rename_conversation(db, id, schema.title, user_id, ip_addr)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return conv


@router.delete("/conversations/{id}", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("ai:chat"))])
async def delete_conversation(
    id: uuid.UUID,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Performs soft delete of conversation.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    success = await ChatService.delete_conversation(db, id, user_id, ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return {"message": "Conversation deleted successfully."}


@router.post("/conversations/{id}/pin", status_code=status.HTTP_200_OK, dependencies=[Depends(PermissionRequired("ai:chat"))])
async def toggle_conversation_pin(
    id: uuid.UUID,
    is_pinned: bool = Query(..., description="Pin state flag indicator"),
    request: Request = None,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Pins or unpins the conversation thread.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    success = await ChatService.toggle_pin(db, id, is_pinned, user_id, ip_addr)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return {"message": f"Conversation pin state set to {is_pinned}."}


@router.post("/conversations/{id}/chat", dependencies=[Depends(PermissionRequired("ai:chat"))])
async def chat_message_exchange(
    id: uuid.UUID,
    schema: MessageCreate,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context)
):
    """
    Streams assistant tokens asynchronously using SSE (Server-Sent Events).
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    from src.core.database import AsyncSessionLocal
    return StreamingResponse(
        ChatService.stream_chat_response(
            db_session_factory=AsyncSessionLocal,
            conversation_id=id,
            user_message=schema.content,
            user_id=user_id,
            request_ip=ip_addr
        ),
        media_type="text/event-stream"
    )


@router.post("/sql", response_model=SQLQueryResponse, dependencies=[Depends(PermissionRequired("ai:query"))])
async def generate_and_execute_sql(
    schema: SQLQueryRequest,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Generates read-only SQL queries from questions and returns structured results.
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    try:
        return await ChatService.generate_sql(db, schema.question, schema.dataset_id, user_id, ip_addr)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/insights", response_model=AIInsightsResponse, dependencies=[Depends(PermissionRequired("ai:insights"))])
async def generate_ai_insights(
    schema: AIInsightsRequest,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Generates structured JSON insights (Executive summaries, findings, recommendations).
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    return await ChatService.generate_insights(db, schema.dataset_id, user_id, ip_addr)


@router.post("/chart-recommendation", response_model=ChartRecommendationResponse, dependencies=[Depends(PermissionRequired("ai:insights"))])
async def get_chart_recommendation(
    schema: ChartRecommendationRequest,
    request: Request,
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    user_context: Dict[str, Any] = Depends(get_authenticated_user_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves chart suggestions (axis columns, aggregations, confidence).
    """
    user_id = uuid.UUID(user_context.get("sub"))
    ip_addr = request.client.host if request.client else None
    
    return await ChatService.recommend_chart(db, schema.dataset_id, user_id, ip_addr)


@router.get("/conversations/{id}/export", dependencies=[Depends(PermissionRequired("ai:chat"))])
async def export_conversation(
    id: uuid.UUID,
    format: str = Query("json", pattern="^(json|markdown)$"),
    workspace_id: uuid.UUID = Depends(verify_workspace_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Exports conversation logs as JSON or Markdown.
    """
    conv = await ChatService.get_conversation(db, id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    if format == "json":
        export_data = {
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
            "messages": [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in conv.messages]
        }
        return Response(content=json.dumps(export_data, indent=2), media_type="application/json")
    else:
        # Markdown format
        md = f"# {conv.title}\n\n"
        md += f"**Thread Created:** {conv.created_at.isoformat()}\n\n---\n\n"
        for m in conv.messages:
            role_label = "Assistant" if m.role == "assistant" else "User"
            md += f"### {role_label}\n{m.content}\n\n"
        return Response(content=md, media_type="text/markdown")
