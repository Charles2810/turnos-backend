import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify, g, current_app

def create_access_token(user_id, username, email, role, paciente_id=None, profesional_id=None):
    """
    Genera un Access Token JWT firmado criptográficamente con HMAC-SHA256.
    Incluye claims estándar (sub, exp, iat, jti) y claims de autorización estrictos.
    """
    secret = current_app.config["JWT_SECRET_KEY"]
    expires_delta = current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    now = datetime.now(timezone.utc)
    
    payload = {
        "sub": str(user_id),
        "username": username,
        "email": email,
        "role": role,
        "paciente_id": str(paciente_id) if paciente_id else None,
        "profesional_id": str(profesional_id) if profesional_id else None,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "type": "access"
    }
    
    return jwt.encode(payload, secret, algorithm="HS256")

def create_refresh_token(user_id):
    """
    Genera un Refresh Token para rotación segura de credenciales.
    """
    secret = current_app.config["JWT_SECRET_KEY"]
    expires_delta = current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]
    now = datetime.now(timezone.utc)
    
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "type": "refresh"
    }
    
    return jwt.encode(payload, secret, algorithm="HS256")

def decode_token(token, expected_type="access"):
    """
    Decodifica y valida rigurosamente un token JWT.
    Protege contra manipulación de algoritmos (alg=none) y expiración.
    """
    secret = current_app.config["JWT_SECRET_KEY"]
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "sub"]}
        )
        if payload.get("type") != expected_type:
            return None, "Tipo de token inválido"
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "El token ha expirado. Por favor inicia sesión nuevamente."
    except jwt.InvalidTokenError as e:
        return None, f"Token inválido o manipulado: {str(e)}"

def jwt_required_custom(optional=False):
    """
    Middleware / Decorador para autenticación obligatoria u opcional.
    Inserta el usuario en el contexto Flask 'g.current_user'.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                if optional:
                    g.current_user = None
                    return fn(*args, **kwargs)
                return jsonify({"error": "Cabecera Authorization Bearer requerida"}), 401
            
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return jsonify({"error": "Formato de cabecera inválido. Use 'Bearer <token>'"}), 401
            
            token = parts[1]
            payload, err = decode_token(token, expected_type="access")
            if err:
                return jsonify({"error": err}), 401
            
            g.current_user = payload
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def roles_required(*allowed_roles):
    """
    Middleware / Decorador para Control de Acceso Basado en Roles (RBAC).
    Defensa comprobable contra Broken Function Level Authorization (OWASP API5:2023).
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if not user:
                return jsonify({"error": "Autenticación requerida para acceder a este recurso"}), 401
            
            user_role = user.get("role")
            if user_role not in allowed_roles:
                return jsonify({
                    "error": "Acceso denegado: permisos insuficientes para realizar esta operación",
                    "rol_requerido": list(allowed_roles),
                    "rol_actual": user_role
                }), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator
