from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base
from datetime import datetime

class URLAnalyticsSummary(Base):
    __tablename__ = "url_analytics_summary"

    url_id: Mapped[int] = mapped_column(ForeignKey("urls.id", ondelete="CASCADE"), primary_key=True)
    total_clicks: Mapped[int] = mapped_column(Integer, default=0)
    unique_clicks: Mapped[int] = mapped_column(Integer, default=0)
    last_clicked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    url = relationship("URL", backref="analytics")
