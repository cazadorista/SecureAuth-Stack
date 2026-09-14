from app.core.db import db
from datetime import datetime, timezone

class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    keycloak_id = db.Column(db.String(36), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "keycloak_id": self.keycloak_id,
            "display_name": self.display_name,
        }