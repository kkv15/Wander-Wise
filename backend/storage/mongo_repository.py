from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import MongoClient, ASCENDING
from bson import ObjectId


class MongoRepository:
    """
    Minimal MongoDB repository for itineraries and users.
    Uses sync PyMongo for simplicity to match existing sync repository interface.
    """

    def __init__(self, uri: str, db_name: str):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        # Ensure indexes
        self.db.users.create_index([("email", ASCENDING)], unique=True)
        self.db.itineraries.create_index([("userId", ASCENDING), ("createdAt", ASCENDING)])

    # ---- Users ----
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        doc = self.db.users.find_one({"email": email})
        return self._normalize(doc)

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None
        doc = self.db.users.find_one({"_id": oid})
        return self._normalize(doc)

    def create_user(self, email: str, password_hash: str) -> Dict[str, Any]:
        now = datetime.utcnow()
        res = self.db.users.insert_one({"email": email, "passwordHash": password_hash, "createdAt": now})
        return {"id": str(res.inserted_id), "email": email, "createdAt": now}

    # ---- Itineraries ----
    def save_itinerary(self, itinerary: Dict[str, Any], user_id: Optional[str] = None) -> str:
        doc = dict(itinerary)
        # Convert integer keys to strings for MongoDB compatibility
        doc = self._convert_keys_to_strings(doc)
        doc["createdAt"] = datetime.utcnow()
        if user_id:
            try:
                doc["userId"] = ObjectId(user_id)
            except Exception:
                doc["userId"] = user_id
        res = self.db.itineraries.insert_one(doc)
        return str(res.inserted_id)
    
    @staticmethod
    def _convert_keys_to_strings(obj: Any) -> Any:
        """
        Recursively convert integer keys to strings for MongoDB compatibility.
        MongoDB requires all dictionary keys to be strings.
        """
        if isinstance(obj, dict):
            return {str(k): MongoRepository._convert_keys_to_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [MongoRepository._convert_keys_to_strings(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(MongoRepository._convert_keys_to_strings(item) for item in obj)
        else:
            return obj

    def list_itineraries_for_user(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return []
        cur = self.db.itineraries.find({"userId": oid}).sort("createdAt", -1).limit(limit)
        return [self._normalize(doc) for doc in cur]

    # ---- helpers ----
    @staticmethod
    def _normalize(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not doc:
            return None
        d = dict(doc)
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
        if "userId" in d and isinstance(d["userId"], ObjectId):
            d["userId"] = str(d["userId"])
        return d


