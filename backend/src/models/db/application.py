from typing import List

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.repository.table import Base


class Application(Base):
    __tablename__ = 'application'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement="auto")
    user: Mapped[int] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    website: Mapped[str] = mapped_column(String(200), nullable=False)
    redirect_uris: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    mode: Mapped[str] = mapped_column(String(3), default="dev", nullable=False)
    client_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    client_secret: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    allowed_users: Mapped[List["ApplicationUser"]] = relationship(back_populates="application")


class ApplicationUser(Base):
    __tablename__ = 'application_user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement="auto")
    application_id: Mapped[int] = mapped_column(ForeignKey("application.id", ondelete="CASCADE"), nullable=False)
    fullname: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    email: Mapped[str] = mapped_column(String(length=64), nullable=False, unique=False)

    application: Mapped["Application"] = relationship(back_populates="allowed_users")
