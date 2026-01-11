from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime


class ItineraryRow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    data_json: str


