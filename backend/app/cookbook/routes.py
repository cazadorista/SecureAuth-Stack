from flask import Blueprint, request, jsonify, g
from app.core.db import db
from app.core.security import require_auth
from app.cookbook.models import Recipe

cookbook_bp = Blueprint("cookbook", __name__)

@cookbook_bp.route("/recipes", methods=["GET"])
@require_auth
def get_recipes():
    recipes = Recipe.query.filter_by(owner_id=g.user_id).all()
    return jsonify([r.to_dict() for r in recipes]), 200

@cookbook_bp.route("/recipes", methods=["POST"])
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

@cookbook_bp.route("/recipes/<int:recipe_id>", methods=["DELETE"])
@require_auth
def delete_recipe(recipe_id):
    recipe = Recipe.query.filter_by(id=recipe_id, owner_id=g.user_id).first()
    if not recipe:
        return jsonify({"error": "Nie znaleziono przepisu"}), 404

    db.session.delete(recipe)
    db.session.commit()
    return jsonify({"message": "Przepis usunięty"}), 200