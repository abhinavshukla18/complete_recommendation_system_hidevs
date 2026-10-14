"""Database tables, written as Python classes (SQLAlchemy models)."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from data.database import Base


def _now():
    """Current time, used as the default for created_at columns."""
    return datetime.now(timezone.utc)


class User(Base):
    """A person who receives recommendations."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # comma-separated, e.g. "python,sql"
    interests = Column(String, default="")
    created_at = Column(DateTime, default=_now)


class Content(Base):
    """A course, article or video that can be recommended."""
    __tablename__ = "content"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    category = Column(String, default="")
    # 1 = beginner, 2 = intermediate, 3 = advanced
    difficulty = Column(Integer, default=1)
    popularity = Column(Float, default=0.0)     # 0.0 to 1.0


class Skill(Base):
    """A skill such as 'python' or 'sql'."""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class UserSkill(Base):
    """Links a user to a skill they have, with a proficiency level."""
    __tablename__ = "user_skills"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)
    proficiency = Column(Integer, default=1)    # 1 (new) to 5 (expert)


class ContentSkill(Base):
    """Links a piece of content to a skill it teaches."""
    __tablename__ = "content_skills"

    content_id = Column(Integer, ForeignKey("content.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)


class Interaction(Base):
    """Something a user did with a piece of content (view, like, rating...)."""
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False)
    # "view", "like", "complete" or "rating"
    type = Column(String, nullable=False)
    rating = Column(Integer, nullable=True)     # 1 to 5, only for ratings
    created_at = Column(DateTime, default=_now)
