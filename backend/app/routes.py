import os
import functools
import jwt
from flask import Blueprint, request, jsonify, g
from app import db
from app.models import Recipe

api_bp = Blueprint("api", __name__)

KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER_URL")

def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Brak tokenu autoryzacyjnego"}), 401

        token = auth_header.split(" ")[1]
        
        try:
            jwks_client = jwt.PyJWKClient(f"{KEYCLOAK_ISSUER}/protocol/openid-connect/certs")
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False}
            )
            g.user_id = payload.get("sub")
            g.user_email = payload.get("email")
        except Exception as e:
            return jsonify({"error": f"Nieprawidłowy token: {str(e)}"}), 401

        return f(*args, **kwargs)
    return decorated

@api_bp.route("/recipes", methods=["GET"])
@require_auth
def get_recipes():
    recipes = Recipe.query.filter_by(owner_id=g.user_id).all()
    return jsonify([r.to_dict() for r in recipes]), 200

@api_bp.route("/recipes", methods=["POST"])
@require_auth
def create_recipe():
    data = request.get_json() or {}
    if not data.get("title"):
        return jsonify({"error": "Tytuł jest wymagany"}), 400

    recipe = Recipe(
        title=data.get("title"),
        description=data.get("description", ""),
        ingredients=data.get("ingredients", []),
        instructions=data.get("instructions", ""),
        owner_id=g.user_id
    )
    db.session.add(recipe)
    db.session.commit()

    return jsonify(recipe.to_dict()), 201