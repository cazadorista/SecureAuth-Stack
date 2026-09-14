from flask import Blueprint, jsonify, g
from app.core.security import require_auth

portal_bp = Blueprint("portal", __name__)

@portal_bp.route("/dashboard", methods=["GET"])
@require_auth
def dashboard_info():
    return jsonify({
        "message": "Witaj w panelu głównym!",
        "user_id": g.user_id,
        "available_apps": ["cookbook", "forms", "blog"]
    }), 200