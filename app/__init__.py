from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger

from app.config import config_by_name
from app.middleware.security_headers import setup_security_headers
from app.middleware.error_handler import register_error_handlers

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120 per minute"]
)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "API REST - Agenda de Turnos Centro de Salud Periurbano",
        "description": (
            "API REST modular y segura desarrollada con Flask y PostgreSQL/Supabase. "
            "Implementa autenticación JWT con control de acceso basado en roles (RBAC), "
            "políticas Row Level Security (RLS) y mitigación exhaustiva de OWASP API Security Top 10."
        ),
        "contact": {
            "name": "Equipo de Desarrollo - Programación Web 2",
            "email": "salud.periurbano@salud.gob.bo"
        },
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "BearerAuth": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header usando el esquema Bearer. Ejemplo: 'Bearer {token}'"
        }
    },
    "security": [
        {
            "BearerAuth": []
        }
    ]
}

def create_app(config_name="development"):
    """
    Application Factory Pattern para inicialización modular de la API.
    """
    app = Flask(__name__)
    config_obj = config_by_name.get(config_name, config_by_name["development"])
    app.config.from_object(config_obj)

    # 1. Configuración de CORS segura
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}},
        supports_credentials=True
    )

    # 2. Inicialización de Rate Limiting
    limiter.init_app(app)

    # 3. Swagger OpenAPI
    Swagger(app, config=swagger_config, template=swagger_template)

    # 4. Middlewares de seguridad y manejo de errores
    setup_security_headers(app)
    register_error_handlers(app)

    # 5. Registro de Blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.pacientes import pacientes_bp
    from app.blueprints.profesionales import profesionales_bp
    from app.blueprints.disponibilidad import disponibilidad_bp
    from app.blueprints.turnos import turnos_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pacientes_bp)
    app.register_blueprint(profesionales_bp)
    app.register_blueprint(disponibilidad_bp)
    app.register_blueprint(turnos_bp)

    # 6. Endpoint de verificación de salud
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "entorno": config_name,
            "version": "1.0.0",
            "proyecto": "Agenda de Turnos — Centro de Salud Periurbano"
        }), 200

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({
            "mensaje": "Bienvenido a la API REST de Gestión de Turnos Médicos",
            "documentacion_swagger": "/api/docs",
            "health_check": "/api/health"
        }), 200

    return app
