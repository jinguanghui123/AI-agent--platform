from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.team_service import TeamService
from app.schemas.team import (
    TeamCreate,
    TeamResponse,
    TeamDetailResponse,
    TeamMemberResponse,
    AddMemberRequest
)

router = APIRouter()


@router.post("/teams", response_model=TeamResponse)
def create_team(
    request: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建团队"""
    service = TeamService(db)
    team = service.create_team(current_user.id, request.name, request.description)
    return team


@router.get("/teams", response_model=List[TeamResponse])
def list_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出用户所在的所有团队"""
    service = TeamService(db)
    return service.get_user_teams(current_user.id)


@router.get("/teams/{team_id}", response_model=TeamDetailResponse)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取团队详情"""
    service = TeamService(db)

    # 检查是否是团队成员
    if not service.is_team_member(team_id, current_user.id):
        raise HTTPException(status_code=403, detail="不是团队成员")

    team = service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")

    members = service.get_team_members(team_id)

    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "owner_id": team.owner_id,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
        "members": members
    }


@router.delete("/teams/{team_id}")
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除团队（仅所有者）"""
    service = TeamService(db)

    if not service.is_team_owner(team_id, current_user.id):
        raise HTTPException(status_code=403, detail="只有团队所有者可以删除团队")

    team = service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")

    # 删除所有成员
    service.db.query(TeamMember).filter(TeamMember.team_id == team_id).delete()
    # 删除团队
    service.db.delete(team)
    service.db.commit()

    return {"message": "删除成功"}


@router.post("/teams/{team_id}/members", response_model=TeamMemberResponse)
def add_member(
    team_id: int,
    request: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加团队成员"""
    service = TeamService(db)

    # 检查权限（owner 或 admin）
    if not service.is_team_owner(team_id, current_user.id):
        raise HTTPException(status_code=403, detail="权限不足")

    try:
        member = service.add_member(team_id, request.user_id, request.role)
        user = service.db.query(User).filter(User.id == request.user_id).first()

        return {
            "id": member.id,
            "user_id": member.user_id,
            "username": user.username if user else "",
            "email": user.email if user else "",
            "role": member.role,
            "created_at": member.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/teams/{team_id}/members/{user_id}")
def remove_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除团队成员"""
    service = TeamService(db)

    # 检查权限（owner 或 admin）
    if not service.is_team_owner(team_id, current_user.id):
        raise HTTPException(status_code=403, detail="权限不足")

    try:
        service.remove_member(team_id, user_id)
        return {"message": "移除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/teams/{team_id}/members/{user_id}/role")
def update_member_role(
    team_id: int,
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新成员角色"""
    service = TeamService(db)

    if not service.is_team_owner(team_id, current_user.id):
        raise HTTPException(status_code=403, detail="权限不足")

    try:
        service.update_member_role(team_id, user_id, role)
        return {"message": "更新成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))