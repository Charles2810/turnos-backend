# Backend Seguro y Base de Datos — Agenda de Turnos Centro de Salud Periurbano

Backend modular y seguro implementado con **Python / Flask**, **PostgreSQL / Supabase** con **Row Level Security (RLS)**, autenticación **JWT con RBAC**, documentación interactiva **Swagger/OpenAPI**, y mitigación exhaustiva de las vulnerabilidades **OWASP API Security Top 10**.

Desarrollado como complemento y soporte directo del frontend MVP ubicado en la carpeta `turnos-app/`.

---

## 🏛️ 1. Arquitectura de Software y Modularidad

La solución sigue el patrón **Application Factory** y **Flask Blueprints**, desacoplando responsabilidades en una arquitectura de 3 capas limpia:

```
backend/
├── app/
│   ├── blueprints/
│   │   ├── auth/           # Registro, Login, Refresh Token, Perfil (/api/v1/auth)
│   │   ├── pacientes/      # CU01: Registro y búsqueda de pacientes (/api/v1/pacientes)
│   │   ├── profesionales/  # Catálogo médico y especialidades (/api/v1/profesionales)
│   │   ├── disponibilidad/ # CU02: Cálculo dinámico de horas libres (/api/v1/disponibilidad)
│   │   └── turnos/         # CU03, CU04, CU05: Reservas, consultas y cancelaciones (/api/v1/turnos)
│   ├── middleware/
│   │   ├── auth.py         # JWT tokens, validación criptográfica y decorador RBAC
│   │   ├── error_handler.py# Ocultamiento de stacktraces y respuestas JSON sanitizadas
│   │   └── security_headers.py # Inyección de cabeceras HTTP (HSTS, CSP, X-Frame-Options)
│   ├── schemas/            # Validación estricta con Marshmallow y Regex bolivianas auditadas
│   ├── services/           # Capa de dominio, Repository relacional parametrizado anti-SQLi
│   ├── config.py           # Configuración para desarrollo, pruebas y producción
│   └── __init__.py         # Fábrica de aplicación, inicialización de Swagger, Limiter y CORS
├── database_schema/
│   ├── 01_schema.sql       # DDL: tablas, llaves foráneas, índices de alto rendimiento
│   ├── 02_rls_policies.sql # Políticas RLS con TO authenticated y predicados anti-BOLA
│   └── 03_seed_data.sql    # Datos iniciales (médicos de turnos-app, roles y usuarios)
├── tests/
│   ├── test_security.py    # Suite de auditoría contra OWASP (SQLi, BOLA, JWT, BFLA, Race Condition)
│   └── test_functional_usecases.py # Validación de los 5 casos de uso del frontend
├── requirements.txt        # Dependencias fijadas
├── .env.example            # Plantilla de variables de entorno
└── run.py                  # Entrypoint del servidor
```

---

## 🚀 2. Instalación y Ejecución Rápida

### Requisitos:
- Python 3.10 o superior

### Paso a paso:

```bash
# 1. Posicionarse en la carpeta backend
cd backend

# 2. Instalar dependencias
python -m pip install -r requirements.txt

# 3. Ejecutar las pruebas automatizadas (15 tests de seguridad y funcionalidad)
python -m pytest tests/ -v

# 4. Iniciar el servidor
python run.py
```

El servidor local estará activo en:
- **API Base Local:** `http://127.0.0.1:5000`
- **Documentación Interactiva Swagger UI Local:** `http://127.0.0.1:5000/api/docs`
- **Health Check Local:** `http://127.0.0.1:5000/api/health`

### 🌐 Despliegue en Producción (Render):
- **URL Base:** [https://turnos-backend-api-1gq9.onrender.com](https://turnos-backend-api-1gq9.onrender.com)
- **Documentación Interactiva Swagger UI en Vivo:** [https://turnos-backend-api-1gq9.onrender.com/api/docs](https://turnos-backend-api-1gq9.onrender.com/api/docs)
- **Health Check en Producción:** [https://turnos-backend-api-1gq9.onrender.com/api/health](https://turnos-backend-api-1gq9.onrender.com/api/health)

---

## 🗄️ 3. Base de Datos PostgreSQL / Supabase y Row Level Security (RLS)

Los scripts en `database_schema/` están optimizados para ejecutarse en el SQL Editor de Supabase o en cualquier base de datos PostgreSQL:

1. **`01_schema.sql`**:
   - Tablas `roles`, `usuarios`, `pacientes`, `profesionales`, `turnos`.
   - Índices B-tree en todas las claves foráneas para acelerar JOINs y evitar *sequential scans*.
   - **Índice único condicional anti-solapamiento**:
     ```sql
     CREATE UNIQUE INDEX uq_turno_profesional_fecha_hora_activo
     ON public.turnos (id_profesional, fecha, hora)
     WHERE estado = 'reservado';
     ```
     Garantiza a nivel de motor de base de datos que dos pacientes jamás puedan reservar el mismo horario con el mismo profesional.

2. **`02_rls_policies.sql`**:
   - Habilitación de RLS: `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`.
   - Sintaxis moderna recomendada por Supabase (`TO authenticated`, `USING (...) WITH CHECK (...)`).
   - **Prevención de BOLA/IDOR (OWASP API1:2023)**:
     - Un paciente **únicamente** puede ver y actualizar sus turnos asociados a su `id_usuario`.
     - Un médico **únicamente** visualiza los turnos agendados con su persona.
     - El personal administrativo (`admin`, `recepcionista`) cuenta con privilegios de gestión global.

3. **`03_seed_data.sql`**:
   - Carga de los 3 médicos coincidentes con el frontend (`PRF-001` Dra. Marcela Rojas, `PRF-002` Dr. Diego Fernández, `PRF-003` Dra. Ana Quispe).
   - Usuarios de prueba con contraseñas seguras hasheadas con bcrypt/pbkdf2:
     - **Admin:** `admin_salud` / `Admin123!`
     - **Médica:** `dra_rojas` / `Medico123!`
     - **Paciente:** `juan_paciente` / `Paciente123!`

---

## 🛡️ 4. Matriz de Mitigación OWASP API Security Top 10 (2023)

| Código OWASP | Vulnerabilidad | Medida de Protección Implementada en este Backend |
|---|---|---|
| **API1:2023** | Broken Object Level Authorization (BOLA/IDOR) | Doble anillo de control: validación de pertenencia en endpoint (`turnos/routes.py` y `pacientes/routes.py`) + Políticas RLS en Supabase (`02_rls_policies.sql`). |
| **API2:2023** | Broken Authentication | JWT con HMAC-SHA256, expiración estricta (15 min), Refresh Token para rotación segura, passwords hasheadas con PBKDF2/Bcrypt con salt dinámico. |
| **API3:2023** | Broken Object Property Level Authorization | Esquemas Marshmallow estrictos (`validators.py`) que impiden Mass Assignment y manipulación de campos de auditoría o roles. |
| **API4:2023** | Unrestricted Resource Consumption | Rate Limiter activo (`Flask-Limiter`) limitando ráfagas y previniendo ataques de fuerza bruta en autenticación. |
| **API5:2023** | Broken Function Level Authorization (BFLA) | Decorador `@roles_required('admin', 'recepcionista')` impidiendo que usuarios con rol `paciente` ejecuten funciones privilegiadas. |
| **API6:2023** | Unrestricted Access to Sensitive Flows | Transacción atómica e índice único para impedir el abuso de reserva masiva de turnos simultáneos. |
| **API8:2023** | Security Misconfiguration | Manejador centralizado de errores (`error_handler.py`) que enmascara stacktraces y excepciones SQL; inyección de cabeceras HTTP de seguridad (HSTS, CSP, nosniff, DENY). |

---

## 🧪 5. Suite de Pruebas Automatizadas

Se cuenta con 15 pruebas unitarias y de integración que comprueban la resiliencia técnica de la API:
- `test_ataque_sql_injection_en_busqueda_paciente`: Comprueba el bloqueo de payloads `' OR '1'='1'`.
- `test_ataque_sql_injection_en_turnos`: Comprueba el bloqueo de inyecciones `UNION SELECT`.
- `test_ataque_bola_consultar_turno_ajeno`: Comprueba que un paciente no pueda ver turnos de terceros (HTTP 403).
- `test_ataque_bola_cancelar_turno_ajeno`: Comprueba que un paciente no pueda cancelar turnos ajenos (HTTP 403).
- `test_ataque_token_jwt_manipulado`: Verifica el rechazo de tokens con firmas adulteradas (HTTP 401).
- `test_ataque_token_sin_cabecera`: Verifica la protección de rutas privadas (HTTP 401).
- `test_ataque_bfla_paciente_intentando_listar_todos_los_pacientes`: Bloquea acceso a listados globales a pacientes (HTTP 403).
- `test_admin_puede_listar_pacientes`: Comprueba el funcionamiento de roles administrativos (HTTP 200).
- `test_prevencion_doble_reserva_mismo_horario`: Comprueba el rechazo de reservas duplicadas (HTTP 409).
- `test_cabeceras_http_seguridad`: Comprueba cabeceras HTTP OWASP en respuestas de la API.
- `test_cu01_registrar_paciente`: Validación end-to-end de registro de paciente con CI y teléfono boliviano.
- `test_cu02_consultar_disponibilidad`: Cálculo correcto de franjas horarias libres.
- `test_cu03_reservar_turno`: Reserva efectiva y actualización de disponibilidad.
- `test_cu04_consultar_turno`: Búsqueda de turnos por CI.
- `test_cu05_cancelar_turno`: Cancelación e idempotencia.
