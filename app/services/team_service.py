from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.team import Team, TeamMember
from app.models.user import User


class TeamService:
    def __init__(self, db: Session):
        self.db = db

    def create_team(self, owner_id: int, name: str, description: str = None) -> Team:
        """创建团队"""
        team = Team(
            name=name,
            description=description,
            owner_id=owner_id
        )
        self.db.add(team)
        self.db.flush()

        # 添加创建者为 owner
        member = TeamMember(
            team_id=team.id,
            user_id=owner_id,
            role="owner"
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(team)
        return team

    def get_team(self, team_id: int) -> Optional[Team]:
        """获取团队详情"""
        return self.db.query(Team).filter(Team.id == team_id).first()

    def get_user_teams(self, user_id: int) -> List[Team]:
        """获取用户所在的所有团队"""
        team_ids = self.db.query(TeamMember.team_id).filter(
            TeamMember.user_id == user_id
        ).all()
        team_ids = [t[0] for t in team_ids]
        return self.db.query(Team).filter(Team.id.in_(team_ids)).all()

    def add_member(self, team_id: int, user_id: int, role: str = "member") -> TeamMember:
        """添加团队成员"""
        # 检查是否已存在
        existing = self.db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()

        if existing:
            return existing

        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member(self, team_id: int, user_id: int) -> bool:
        """移除团队成员"""
        member = self.db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()

        if not member:
            return False

        # 不能移除 owner
        if member.role == "owner":
            raise ValueError("不能移除团队所有者")

        self.db.delete(member)
        self.db.commit()
        return True

    def get_team_members(self, team_id: int) -> List[dict]:
        """获取团队成员列表"""
        members = self.db.query(TeamMember, User).join(
            User, TeamMember.user_id == User.id
        ).filter(TeamMember.team_id == team_id).all()

        return [
            {
                "id": m.TeamMember.id,
                "user_id": m.User.id,
                "username": m.User.username,
                "email": m.User.email,
                "role": m.TeamMember.role,
                "created_at": m.TeamMember.created_at
            }
            for m in members
        ]

    def update_member_role(self, team_id: int, user_id: int, role: str) -> bool:
        """更新成员角色"""
        member = self.db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()

        if not member:
            return False

        if member.role == "owner":
            raise ValueError("不能修改团队所有者角色")

        member.role = role
        self.db.commit()
        return True

    def is_team_member(self, team_id: int, user_id: int) -> bool:
        """检查用户是否是团队成员"""
        return self.db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first() is not None

    def is_team_owner(self, team_id: int, user_id: int) -> bool:
        """检查用户是否是团队所有者"""
        member = self.db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
            TeamMember.role == "owner"
        ).first()
        return member is not None