from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base
import enum
from datetime import datetime

class RoleEnum(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    editor = "editor"
    viewer = "viewer"

class PlanEnum(str, enum.Enum):
    free = "free"
    premium = "premium"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.owner)
    plan: Mapped[PlanEnum] = mapped_column(Enum(PlanEnum), default=PlanEnum.free)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # OAuth fields
    google_id: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    oauth_provider: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g., 'google', 'github'
    oauth_avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    workspaces = relationship("Workspace", back_populates="owner", cascade="all, delete-orphan")
    workspace_memberships = relationship("WorkspaceMember", back_populates="user", cascade="all, delete-orphan")
