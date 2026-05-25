from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.session import Session as ChatSession, Message
from app.services.knowledge_service import KnowledgeService
from app.services.model_gateway import model_gateway
from app.schemas.knowledge import (
    DocumentResponse,
    SearchRequest,
    SearchResult,
    RAGChatRequest,
    RAGChatResponse
)
from sqlalchemy import func

router = APIRouter()


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    filename: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传并处理文档"""
    service = KnowledgeService(db)
    try:
        doc = await service.add_document(current_user.id, file, filename)
        return doc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")


@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出用户的所有文档"""
    service = KnowledgeService(db)
    return service.list_documents(current_user.id)


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除文档"""
    service = KnowledgeService(db)
    success = service.delete_document(doc_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"message": "删除成功"}


@router.post("/search", response_model=List[SearchResult])
async def search_knowledge(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """搜索知识库"""
    service = KnowledgeService(db)
    try:
        results = await service.search_chunks(current_user.id, request.query, request.top_k)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.post("/chat/rag", response_model=RAGChatResponse)
async def chat_with_rag(
    request: RAGChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """基于知识库的对话"""
    service = KnowledgeService(db)

    # 检索相关 chunks
    chunks = await service.search_chunks(current_user.id, request.message, request.top_k)

    # 构建 RAG 上下文
    rag_context = service.build_rag_context(chunks)

    # 构建消息
    if rag_context:
        system_message = f"""你是一个智能助手。请根据以下参考信息回答用户的问题。
如果参考信息中没有相关内容，请如实告知用户。

{rag_context}

请用中文回答。"""
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": request.message}
        ]
    else:
        messages = [{"role": "user", "content": request.message}]

    # 调用模型
    try:
        answer = await model_gateway.chat(request.model_id, messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成回答失败: {str(e)}")

    return RAGChatResponse(
        answer=answer,
        chunks=chunks
    )
