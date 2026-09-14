import functools
import jwt
from flask import request, jsonify, g
from app.core.config import Config

def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Brak tokenu autoryzacyjnego"}), 401

        token = auth_header.split(" ")[1]

        try:
            jwks_client = jwt.PyJWKClient(f"{Config.KEYCLOAK_ISSUER_URL}/protocol/openid-connect/certs")
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