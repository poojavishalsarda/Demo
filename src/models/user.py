"""User and customer profile models."""
from sqlalchemy import Column, Integer, String, Text
from src.database import Base


class User(Base):
    """Registered customer or user profile."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    preferences = Column(Text, nullable=True, default="")  # e.g. "Sci-Fi, AI, Architecture"

    def to_dict(self) -> dict:
        """Convert user instance to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "preferences": [p.strip() for p in self.preferences.split(",") if p.strip()] if self.preferences else [],
        }
