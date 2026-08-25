from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    language: Mapped[str] = mapped_column(String(50))
    filename: Mapped[str] = mapped_column(String(255), default="submission")
    source_code: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    user = relationship("User", back_populates="reviews")
    findings = relationship("Finding", back_populates="review", cascade="all, delete-orphan")

class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), index=True)
    category: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review = relationship("Review", back_populates="findings")

class HistoricalRule(Base):
    __tablename__ = "historical_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_type: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(Text)
