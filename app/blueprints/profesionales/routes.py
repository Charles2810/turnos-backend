from flask import Blueprint, jsonify
from app.services.db_service import DatabaseService

profesionales_bp = Blueprint("profesionales", __name__, url_prefix="/api/v1/profesionales")
db = DatabaseService.get_instance()

@profesionales_bp.route("", methods=["GET"])
def get_all():
    """
    Lista el plantel de profesionales médicos activos del centro de salud.
    ---
    tags:
      - Profesionales
    summary: Obtiene el catálogo de profesionales médicos disponibles
    responses:
      200:
        description: Listado de médicos y especialidades
    """
    profesionales = db.get_profesionales()
    return jsonify({
        "total": len(profesionales),
        "profesionales": profesionales
    }), 200

@profesionales_bp.route("/<identifier>", methods=["GET"])
def get_by_id(identifier):
    """
    Obtiene la ficha de un profesional por UUID o por código PRF-XXX.
    ---
    tags:
      - Profesionales
    summary: Consulta un profesional por ID o código
    parameters:
      - in: path
        name: identifier
        required: true
        type: string
        example: PRF-001
    responses:
      200:
        description: Detalle del profesional
      404:
        description: Profesional no encontrado
    """
    prof = db.get_profesional_by_id_or_code(identifier)
    if not prof:
        return jsonify({"error": "Profesional médico no encontrado"}), 404
    return jsonify({"profesional": prof}), 200
