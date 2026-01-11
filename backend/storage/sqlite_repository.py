import os
import json
from typing import Dict, Any
from sqlmodel import SQLModel, Session, create_engine
from models.db_models import ItineraryRow


class SQLiteRepository:
    def __init__(self, db_path: str = "./data.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        SQLModel.metadata.create_all(self.engine)

    def save_itinerary(self, itinerary: Dict[str, Any]) -> str:
        doc = ItineraryRow(data_json=json.dumps(itinerary))
        with Session(self.engine) as session:
            session.add(doc)
            session.commit()
            session.refresh(doc)
            return str(doc.id)


