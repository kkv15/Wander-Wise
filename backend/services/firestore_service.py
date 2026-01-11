import os
from typing import Dict, Any
from google.cloud import firestore


class FirestoreService:
    """
    Very small DAO for saving itineraries.
    Requires GOOGLE_APPLICATION_CREDENTIALS or default credentials in environment.
    """

    def __init__(self, project_id: str):
        self.client = firestore.Client(project=project_id)
        self.collection_name = "itineraries"

    def save_itinerary(self, itinerary: Dict[str, Any]) -> str:
        # Avoid persisting very large content; basic save
        col = self.client.collection(self.collection_name)
        doc_ref = col.add(itinerary)[1]
        return doc_ref.id


