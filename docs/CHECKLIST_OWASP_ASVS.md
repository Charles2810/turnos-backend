# CHECKLIST DE VERIFICACIÓN DE SEGURIDAD OWASP ASVS Y API TOP 10 (2023)
## AUDITORÍA TÉCNICA DEL BACKEND — AGENDA DE TURNOS CENTRO DE SALUD PERIURBANO

Este documento detalla el estado de cumplimiento de los requerimientos de seguridad conforme a:
1. **OWASP API Security Top 10 (2023)**
2. **OWASP Application Security Verification Standard (ASVS v4.0.3)**

---

### 1. Matriz de Cumplimiento OWASP API Security Top 10 (2023)

| ID OWASP | Vulnerabilidad | Nivel de Riesgo | Estado de Mitigación | Archivo y Componente de Implementación | Evidencia / Prueba Automatizada |
|---|---|:---:|:---:|---|---|
| **API1:2023** | Broken Object Level Authorization (BOLA / IDOR) | **Crítico** | **MITIGADO AL 100%** | `backend/app/blueprints/turnos/routes.py`<br>`backend/app/blueprints/pacientes/routes.py`<br>`backend/database_schema/02_rls_policies.sql` | `tests/test_security.py`:<br>- `test_ataque_bola_consultar_turno_ajeno` (HTTP 403)<br>- `test_ataque_bola_cancelar_turno_ajeno` (HTTP 403) |
| **API2:2023** | Broken Authentication | **Crítico** | **MITIGADO AL 100%** | `backend/app/middleware/auth.py`<br>`backend/app/blueprints/auth/routes.py` | `tests/test_security.py`:<br>- `test_ataque_token_jwt_manipulado` (HTTP 401)<br>- `test_ataque_token_sin_cabecera` (HTTP 401) |
| **API3:2023** | Broken Object Property Level Authorization | **Alto** | **MITIGADO AL 100%** | `backend/app/schemas/validators.py`<br>Esquemas Marshmallow con validación estricta de campos | Filtros en esquemas que impiden inyección de campos administrativos o sobreescritura de propiedades. |
| **API4:2023** | Unrestricted Resource Consumption | **Alto** | **MITIGADO AL 100%** | `backend/app/__init__.py`<br>Flask-Limiter con cuotas por IP y paginación en `/pacientes` | Configuración de límites (120 req/min general, 5 req/min login) y respuestas estándar HTTP 429. |
| **API5:2023** | Broken Function Level Authorization (BFLA) | **Alto** | **MITIGADO AL 100%** | `backend/app/middleware/auth.py`<br>Decorador `@roles_required('admin', 'recepcionista')` | `tests/test_security.py`:<br>- `test_ataque_bfla_paciente_intentando_listar_todos_los_pacientes` (HTTP 403)<br>- `test_admin_puede_listar_pacientes` (HTTP 200) |
| **API6:2023** | Unrestricted Access to Sensitive Business Flows | **Medio-Alto** | **MITIGADO AL 100%** | `backend/database_schema/01_schema.sql`<br>`backend/app/services/db_service.py` | `tests/test_security.py`:<br>- `test_prevencion_doble_reserva_mismo_horario` (HTTP 409 al detectar intento de solapamiento) |
| **API7:2023** | Server Side Request Forgery (SSRF) | **Medio** | **NO APLICABLE / MITIGADO** | La API no acepta URLs remotas de clientes ni consume webhooks externos. | Revisión estática de código confirmando cero invocaciones de librerías HTTP basadas en entradas de usuario. |
| **API8:2023** | Security Misconfiguration | **Alto** | **MITIGADO AL 100%** | `backend/app/middleware/error_handler.py`<br>`backend/app/middleware/security_headers.py` | `tests/test_security.py`:<br>- `test_cabeceras_http_seguridad` verificando inyección de CSP, HSTS, X-Content-Type-Options: nosniff, X-Frame-Options: DENY. |
| **API9:2023** | Improper Inventory Management | **Bajo-Medio** | **MITIGADO AL 100%** | `backend/app/__init__.py` y `backend/app/blueprints/*` | Versionado formal en `/api/v1/` y documentación Swagger OpenAPI sincronizada en `/api/docs`. |
| **API10:2023**| Unsafe Consumption of APIs | **Bajo** | **MITIGADO AL 100%** | `backend/app/schemas/validators.py` | Validación rigurosa de tipos de datos, longitudes y expresiones regulares bolivianas. |

---

### 2. Cumplimiento de Controles OWASP ASVS v4.0.3

| Sección ASVS | Requisito de Seguridad | Mecanismo Técnico Implementado en el Backend |
|---|---|---|
| **V1: Arquitectura** | Separación clara de capas y principio de mínimo privilegio. | Arquitectura de 3 Capas, Blueprints desacoplados y políticas de acceso granular RLS en PostgreSQL/Supabase. |
| **V2: Autenticación** | Almacenamiento seguro de credenciales y ciclo de vida de tokens. | Hashes generados con PBKDF2/Bcrypt con salt criptográfico. Tokens JWT con vigencia de 15 minutos y Refresh Token de rotación. |
| **V3: Control de Sesión** | Tokens criptográficamente robustos e imposibilidad de manipulación. | Algoritmo HMAC-SHA256 con clave secreta de alta entropía. Rechazo inmediato ante manipulación de cabeceras o payloads. |
| **V4: Control de Acceso** | Verificación en el lado del servidor de la propiedad de objetos. | Decorador `@roles_required` y verificación en controladores de que `id_usuario == auth.uid()`. Políticas RLS como segunda barrera en base de datos. |
| **V5: Validación y Sanitización** | Validación estricta de formato y tipo de todas las entradas del cliente. | Librería Marshmallow combinada con expresiones regulares para nombres, Cédula de Identidad boliviana, celular y correos. |
| **V7: Manejo de Errores y Logging** | Supresión de información sensible en respuestas HTTP. | Manejador centralizado en `error_handler.py` que captura excepciones internas y devuelve mensajes JSON limpios sin revelar stacktraces ni sentencias SQL. |
| **V13: Comunicaciones Seguras** | Inyección de cabeceras de transporte seguro y control de recursos. | Cabeceras HTTP: `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy`. |
| **V14: Configuración** | Inhabilitación de endpoints innecesarios y modos de depuración en entornos productivos. | Modo `FLASK_DEBUG=0` en producción, variables de entorno desacopladas mediante `.env` y configuración modular en `config.py`. |
