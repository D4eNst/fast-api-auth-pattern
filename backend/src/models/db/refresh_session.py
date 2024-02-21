import datetime
from uuid import UUID as _UUID, uuid4

import sqlalchemy
from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.repository.table import Base


class RefreshSession(Base):
    __tablename__ = "refresh_session"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement="auto")
    account: Mapped[int] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"), nullable=False)
    refresh_token: Mapped[_UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid4)
    ua: Mapped[str] = mapped_column(sqlalchemy.String(length=200), nullable=False)
    ip: Mapped[str] = mapped_column(sqlalchemy.String(length=45), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )
    expires_in: Mapped[int] = mapped_column(sqlalchemy.Integer, nullable=False)

    __mapper_args__ = {"eager_defaults": True}
