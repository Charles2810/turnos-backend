import logging
from flask import jsonify
from marshmallow import ValidationError

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """
    Registra manejadores de error globales para garantizar que ninguna
    excepción no controlada o traza de base de datos se filtre al cliente.
    Cumple con OWASP API8:2023 (Security Misconfiguration & Error Handling).
    """

    @app.errorhandler(ValidationError)
    def handle_marshmallow_validation(err):
        return jsonify({
            "error": "Error de validación en la solicitud",
            "detalles": err.messages
        }), 400

    @app.errorhandler(400)
    def bad_request(err):
        return jsonify({
            "error": "Petición incorrecta o malformada",
            "detalles": getattr(err, "description", str(err))
        }), 400

    @app.errorhandler(401)
    def unauthorized(err):
        return jsonify({
            "error": "No autorizado: credenciales inválidas o ausentes",
            "detalles": getattr(err, "description", str(err))
        }), 401

    @app.errorhandler(403)
    def forbidden(err):
        return jsonify({
            "error": "Prohibido: no cuenta con los permisos necesarios",
            "detalles": getattr(err, "description", str(err))
        }), 403

    @app.errorhandler(404)
    def not_found(err):
        return jsonify({
            "error": "Recurso no encontrado",
            "detalles": getattr(err, "description", str(err))
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(err):
        return jsonify({
            "error": "Método HTTP no permitido para este endpoint",
            "detalles": getattr(err, "description", str(err))
        }), 405

    @app.errorhandler(409)
    def conflict(err):
        return jsonify({
            "error": "Conflicto con el estado actual del recurso",
            "detalles": getattr(err, "description", str(err))
        }), 409

    @app.errorhandler(429)
    def ratelimit_handler(err):
        return jsonify({
            "error": "Límite de solicitudes excedido (Rate Limit). Por favor espera un momento.",
            "detalles": getattr(err, "description", str(err))
        }), 429

    @app.errorhandler(500)
    def internal_error(err):
        logger.error(f"Error interno del servidor: {err}", exc_info=True)
        # Sanitización estricta: nunca enviar el stacktrace o detalles SQL al cliente
        return jsonify({
            "error": "Ha ocurrido un error interno en el servidor. El incidente ha sido registrado."
        }), 500

    @app.errorhandler(Exception)
    def unhandled_exception(err):
        logger.critical(f"Excepción no manejada: {err}", exc_info=True)
        return jsonify({
            "error": "Error inesperado en el procesamiento de la solicitud."
        }), 500
