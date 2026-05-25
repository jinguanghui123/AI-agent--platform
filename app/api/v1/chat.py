from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.session import Session as ChatSession, Message
from app.schemas.chat import ChatRequest, ChatResponse, SessionCreate, SessionResponse, MessageResponse
from app.services.model_gateway import model_gateway
from app.services.file_storage import save_upload_file

router = APIRouter()


@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传图片"""
    try:
        result = await save_upload_file(file, sub_dir="images")
        return {"ok": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get("/sessions", response_model=List[SessionResponse])
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)\
        .order_by(ChatSession.updated_at.desc()).all()
    return sessions

@router.post("/sessions", response_model=SessionResponse)
def create_session(
    session: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_session = ChatSession(
        user_id=current_user.id,
        title=session.title or "新对话",
        model_id=session.model_id
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    if not session:
        return {"error": "会话不存在"}
    db.query(Message).filter(Message.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"message": "删除成功"}

@router.get("/history/{session_id}", response_model=List[MessageResponse])
def get_history(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    messages = db.query(Message).filter(
        Message.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).join(ChatSession).filter(ChatSession.user_id == current_user.id)\
        .order_by(Message.created_at.asc()).all()
    return messages

@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if request.session_id:
        db_session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id,
            ChatSession.user_id == current_user.id
        ).first()
        if not db_session:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        db_session = ChatSession(
            user_id=current_user.id,
            title=request.message[:50] if len(request.message) > 50 else request.message,
            model_id=request.model_id
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

    # 构建用户消息内容
    has_images = request.images and len(request.images) > 0
    image_url = request.images[0] if has_images else None
    content_type = "image" if has_images else "text"

    user_message = Message(
        session_id=db_session.id,
        role="user",
        content=request.message,
        content_type=content_type,
        image_url=image_url,
        model_id=request.model_id
    )
    db.add(user_message)
    db.commit()

    history = db.query(Message).filter(
        Message.session_id == db_session.id
    ).order_by(Message.created_at.asc()).all()

    # 构建发给模型的消息
    messages_for_model = []
    for m in history:
        if m.content_type == "image" and m.image_url:
            # 转换为完整 URL（MiniMax API 需要可访问的图片 URL）
            image_url = m.image_url
            if image_url.startswith("/"):
                image_url = f"http://localhost:8000{image_url}"
            # 多模态消息格式
            messages_for_model.append({
                "role": m.role,
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": m.content}
                ]
            })
        else:
            messages_for_model.append({"role": m.role, "content": m.content})

    try:
        assistant_content = await model_gateway.chat(request.model_id, messages_for_model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    assistant_message = Message(
        session_id=db_session.id,
        role="assistant",
        content=assistant_content,
        model_id=request.model_id
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    db_session.updated_at = func.now()
    db.commit()

    return ChatResponse(session_id=db_session.id, message=assistant_message)