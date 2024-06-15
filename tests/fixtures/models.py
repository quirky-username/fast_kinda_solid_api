import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, Index, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fast_kinda_solid_api.data.models import BaseTable

from .db import database

Base: DeclarativeBase = database.get_declarative_base()


class KeysetPaginatableObject(Base, BaseTable):
    __tablename__ = "test_keyset_paginatable"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    order: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("idx_keyset_id_order", "id", "order"),)


class SampleModel(Base, BaseTable):
    __tablename__ = "sample"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class TestBase(Base, BaseTable):
    __tablename__ = "test_base"

    not_nullable_no_default: Mapped[str]
    nullable_with_default_none_set: Mapped[str] = mapped_column(String, default="-1", nullable=True)
    nullable_with_default: Mapped[str] = mapped_column(String, default="3", nullable=True)
    nullable_with_default_none: Mapped[str] = mapped_column(String, default=None, nullable=True)
