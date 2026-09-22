import pytest
from app import create_app
from app.services.db_service import DatabaseService

@pytest.fixture
def app():
    return create_app("testing")

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db():
    return DatabaseService.get_instance()

def test_cu01_registrar_paciente(client):
    """
    CU01 — Registrar paciente con validaciones de negocio bolivianas.
    """
    payload = {
        "nombre": "Carlos",
        "apellido": "Alvarez",
        "CI": "6123456 LP",
        "telefono": "78899001",
        "correo": "carlos.alvarez@salud.bo"
    }
    res = client.post("/api/v1/pacientes", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert "paciente" in data
    assert data["paciente"]["nombre"] == "Carlos"
    assert data["paciente"]["ci"] == "6123456 LP"

def test_cu02_consultar_disponibilidad(client):
    """
    CU02 — Consultar franjas horarias disponibles para un profesional en una fecha.
    """
    res = client.get("/api/v1/disponibilidad?id_profesional=PRF-001&fecha=2026-11-20")
    assert res.status_code == 200
    data = res.get_json()
    assert "horarios_disponibles" in data
    assert len(data["horarios_disponibles"]) > 0
    assert "08:00" in data["horarios_disponibles"]

def test_cu03_reservar_turno(client):
    """
    CU03 — Reservar turno exitosamente para un paciente registrado.
    """
    payload = {
        "ci": "8452136 SC",
        "id_profesional": "PRF-003",
        "fecha": "2026-11-20",
        "hora": "14:00"
    }
    res = client.post("/api/v1/turnos", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert "turno" in data
    assert data["turno"]["fecha"] == "2026-11-20"
    assert data["turno"]["hora"] == "14:00"

    # Verificar que el horario 14:00 ya no figure en la disponibilidad (CU02)
    disp_res = client.get("/api/v1/disponibilidad?id_profesional=PRF-003&fecha=2026-11-20")
    disp_data = disp_res.get_json()
    assert "14:00" not in disp_data["horarios_disponibles"]

def test_cu04_consultar_turno(client):
    """
    CU04 — Consultar turnos por CI del paciente.
    """
    res = client.get("/api/v1/turnos?ci=8452136 SC")
    assert res.status_code == 200
    data = res.get_json()
    assert "turnos" in data
    assert len(data["turnos"]) > 0

def test_cu05_cancelar_turno(client):
    """
    CU05 — Cancelar turno existente y verificar liberación de horario o actualización de estado.
    """
    # 1. Crear turno a cancelar
    payload = {
        "ci": "8452136 SC",
        "id_profesional": "PRF-001",
        "fecha": "2026-11-25",
        "hora": "11:00"
    }
    create_res = client.post("/api/v1/turnos", json=payload)
    assert create_res.status_code == 201
    turno_creado = create_res.get_json()["turno"]

    # 2. Cancelar turno
    cancel_res = client.patch(f"/api/v1/turnos/{turno_creado['idTurno']}/cancelar", json={"motivo": "Urgencia personal"})
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()["turno"]["estado"] == "cancelado"
