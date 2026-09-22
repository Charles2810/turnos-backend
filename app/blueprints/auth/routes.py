from flask import Blueprint, request, jsonify, g
from werkzeug.security import check_password_hash
from app.schemas.validators import RegistroUsuarioSchema, LoginSchema
from app.middleware.auth import create_access_token, create_refresh_token, decode_token, jwt_required_custom
from app.services.db_service import DatabaseService

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
db = DatabaseService.get_instance()

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Registro de nuevos usuarios en el sistema.
    ---
    tags:
      - Autenticación
    summary: Registra un nuevo usuario con credenciales seguras
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [username, email, password]
          properties:
            username:
              type: string
              example: juan_paciente
            email:
              type: string
              example: juan.perez@correo.bo
            password:
              type: string
              example: Paciente123!
            rol:
              type: string
              enum: [paciente, medico, recepcionista, admin]
              default: paciente
    responses:
      201:
        description: Usuario creado exitosamente
      400:
        description: Datos inválidos o usuario ya existente
    """
    data = request.get_json() or {}
    schema = RegistroUsuarioSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify({"error": "Validación fallida", "detalles": errors}), 400

    user, err = db.create_user(
        username=data["username"].strip(),
        email=data["email"].strip().lower(),
        password=data["password"],
        rol_nombre=data.get("rol", "paciente")
    )
    if err:
        return jsonify({"error": err}), 400

    return jsonify({
        "mensaje": "Usuario registrado exitosamente",
        "usuario": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "rol": user["rol_nombre"]
        }
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Autenticación y generación de tokens JWT (Access y Refresh).
    ---
    tags:
      - Autenticación
    summary: Inicia sesión y retorna Access Token y Refresh Token
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [username, password]
          properties:
            username:
              type: string
              example: juan_paciente
            password:
              type: string
              example: Paciente123!
    responses:
      200:
        description: Autenticación exitosa
      401:
        description: Credenciales incorrectas
    """
    data = request.get_json() or {}
    schema = LoginSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify({"error": "Validación fallida", "detalles": errors}), 400

    user = db.get_user_by_username_or_email(data["username"].strip())
    if not user or not check_password_hash(user["password_hash"], data["password"]):
        return jsonify({"error": "Credenciales inválidas. Verifique su usuario y contraseña."}), 401

    # Obtener IDs vinculados si es paciente o profesional médico
    paciente = db.get_paciente_by_user_id(user["id"])
    profesional = db.get_profesional_by_id_or_code(user["id"])

    paciente_id = paciente["id"] if paciente else None
    profesional_id = profesional["id"] if profesional else None

    access_token = create_access_token(
        user_id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["rol_nombre"],
        paciente_id=paciente_id,
        profesional_id=profesional_id
    )
    refresh_token = create_refresh_token(user["id"])

    return jsonify({
        "mensaje": "Autenticación satisfactoria",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "usuario": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "rol": user["rol_nombre"],
            "paciente": paciente,
            "profesional": profesional
        }
    }), 200

@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """
    Renueva el Access Token utilizando un Refresh Token válido.
    ---
    tags:
      - Autenticación
    summary: Rotación de Access Token
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [refresh_token]
          properties:
            refresh_token:
              type: string
    responses:
      200:
        description: Nuevo Access Token emitido
      401:
        description: Refresh token inválido o expirado
    """
    data = request.get_json() or {}
    token = data.get("refresh_token")
    if not token:
        return jsonify({"error": "El campo refresh_token es obligatorio"}), 400

    payload, err = decode_token(token, expected_type="refresh")
    if err:
        return jsonify({"error": err}), 401

    user = db.get_user_by_id(payload["sub"])
    if not user:
        return jsonify({"error": "Usuario ya no existe o está inactivo"}), 401

    paciente = db.get_paciente_by_user_id(user["id"])
    profesional = db.get_profesional_by_id_or_code(user["id"])

    new_access_token = create_access_token(
        user_id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["rol_nombre"],
        paciente_id=paciente["id"] if paciente else None,
        profesional_id=profesional["id"] if profesional else None
    )

    return jsonify({
        "access_token": new_access_token,
        "token_type": "Bearer"
    }), 200

@auth_bp.route("/me", methods=["GET"])
@jwt_required_custom()
def me():
    """
    Retorna la información del usuario autenticado desde el JWT claim.
    ---
    tags:
      - Autenticación
    summary: Consulta el perfil del usuario actual
    security:
      - BearerAuth: []
    responses:
      200:
        description: Perfil del usuario
      401:
        description: Token ausente o inválido
    """
    user_id = g.current_user["sub"]
    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    paciente = db.get_paciente_by_user_id(user_id)
    return jsonify({
        "usuario": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "rol": user["rol_nombre"],
            "paciente": paciente
        }
    }), 200
