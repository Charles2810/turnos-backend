# INFORME TÉCNICO ACADÉMICO — ACTIVIDAD 03
## ARQUITECTURA DE BACKEND SEGURO, BASE DE DATOS RELACIONAL CON RLS Y AUDITORÍA DE SEGURIDAD OWASP

**Título del Proyecto:** Implementación de una API REST Segura con Flask, Blueprints y PostgreSQL/Supabase para la Gestión de Turnos en un Centro de Salud Periurbano  
**Asignatura:** Programación Web II  
**Estudiante / Equipo de Desarrollo:** Área de Ingeniería de Sistemas / Desarrollo de Software  
**Norma de Presentación:** American Psychological Association (APA), Séptima Edición (7.ª ed.)  
**Fecha:** Septiembre de 2026  

---

### Resumen

El presente informe documenta el diseño, desarrollo, aseguramiento y auditoría de la Capa de Backend para el sistema de agenda de turnos médicos de un centro de salud periurbano, concebido como contraparte robusta del Single Page Application (SPA) desarrollado previamente en React (`turnos-app`). La solución implementa una arquitectura modular de tres capas basada en el microframework Flask mediante el patrón *Application Factory* y *Blueprints*, desacoplando la lógica de negocio en cinco módulos funcionales (Autenticación, Pacientes, Profesionales, Disponibilidad y Turnos). En la capa de datos, se estructuró un modelo relacional en PostgreSQL/Supabase reforzado mediante directivas de *Row Level Security* (RLS) con granularidad basada en roles (RBAC). El control de acceso se fundamenta en tokens criptográficos JSON Web Tokens (JWT) con ciclo de vida corto y rotación mediante Refresh Tokens. La seguridad del sistema fue auditada y validada contra el estándar internacional *OWASP API Security Top 10 (2023)* y *OWASP ASVS v4.0*, neutralizando vectores críticos como Inyección SQL, Broken Object Level Authorization (BOLA/IDOR), Broken Function Level Authorization (BFLA), Mass Assignment y condiciones de carrera concurrentes. Los resultados se verifican mediante una suite automatizada de 15 pruebas unitarias y de resiliencia con 100% de efectividad.

*Palabras clave:* API REST, Flask Blueprints, PostgreSQL, Row Level Security, JSON Web Tokens, OWASP API Top 10, BOLA/IDOR, Centro de Salud Periurbano, APA 7.

---

### Abstract

This technical report details the design, engineering, hardening, and security auditing of the Backend layer for an outpatient medical appointment scheduling system in a peri-urban health center, designed to support the React SPA client (`turnos-app`). The solution implements a three-tier modular architecture using Flask via the *Application Factory* and *Blueprints* patterns, decoupling business logic into five functional domains (Authentication, Patients, Healthcare Professionals, Availability, and Appointments). In the persistence layer, a relational data model was deployed in PostgreSQL/Supabase strengthened by fine-grained *Row Level Security* (RLS) policies and Role-Based Access Control (RBAC). Identity and access management relies on JSON Web Tokens (JWT) signed with HMAC-SHA256, featuring short-lived access tokens and refresh rotation. System resilience was audited against the *OWASP API Security Top 10 (2023)* and *OWASP ASVS v4.0* benchmarks, effectively neutralizing high-severity attack vectors including SQL Injection, Broken Object Level Authorization (BOLA/IDOR), Broken Function Level Authorization (BFLA), Mass Assignment, and concurrent race conditions. Validation is demonstrated through an automated suite of 15 security and functional integration tests achieving full compliance.

*Keywords:* REST API, Flask Blueprints, PostgreSQL, Row Level Security, JSON Web Tokens, OWASP API Top 10, BOLA/IDOR, Healthcare Systems, APA 7.

---

## 1. Introducción y Planteamiento del Problema

Los centros de salud de primer nivel en contextos periurbanos enfrentan desafíos operacionales caracterizados por recursos de conectividad variables, alta afluencia de pacientes y la imperativa necesidad de resguardar información médica de carácter altamente confidencial (Ley N.º 3131 del Ejercicio Profesional Médico y normativas internacionales de protección de datos de salud). 

En las etapas previas del proyecto (Actividades 01 y 02), se diseñó y construyó un frontend interactivo en React 19 (`turnos-app`) que cubrió los cinco casos de uso primordiales:
1. **CU01:** Registro de paciente con validación de identidad boliviana (Cédula de Identidad y celular de 8 dígitos).
2. **CU02:** Consulta de disponibilidad horaria por profesional.
3. **CU03:** Reserva de turno médico previniendo solapamiento.
4. **CU04:** Consulta de turnos agendados.
5. **CU05:** Cancelación controlada de turnos.

Sin embargo, en dicha etapa la persistencia residía de manera temporal en el almacenamiento local del navegador (`localStorage`), lo que conllevaba riesgos intrínsecos de manipulación de estado, ausencia de integridad referencial, falta de sincronización concurrente entre múltiples terminales de admisión y una exposición total de los datos si el dispositivo era compartido.

El objetivo de esta **Actividad 03** es erradicar estas limitaciones mediante el desarrollo de una **API REST empresarial, altamente modular, documentada interactivamente mediante OpenAPI/Swagger, respaldada en PostgreSQL/Supabase y blindada mediante Row Level Security (RLS) y controles estrictos de seguridad OWASP**.

---

## 2. Marco Arquitectónico y Modularidad (Flask Blueprints)

### 2.1. Arquitectura de Tres Capas
El sistema se organiza bajo el paradigma de separación de intereses (*Separation of Concerns*):
- **Capa de Presentación (Frontend SPA):** Aplicación React 19 (`turnos-app`) alojada en cliente, consumiendo recursos asíncronos mediante HTTP Fetch/Axios.
- **Capa de Lógica de Negocio y Aplicación (Backend REST):** Microframework Python Flask con *Application Factory* (`create_app`), middlewares interceptores de seguridad, esquemas de validación declarativa (Marshmallow) y servicios de dominio.
- **Capa de Datos y Persistencia:** Motor relacional PostgreSQL / Supabase con tipos de datos estructurados, índices optimizados y RLS a nivel de kernel de base de datos.

```
+-------------------------------------------------------------------------+
|                  CAPA DE PRESENTACIÓN (React 19 SPA)                     |
|  - CU01 Registro  - CU02 Disponibilidad  - CU03 Reserva                 |
|  - CU04 Consulta  - CU05 Cancelación     - Tailwind v4                  |
+------------------------------------+------------------------------------+
                                     | HTTPS / JSON / Bearer JWT
                                     v
+-------------------------------------------------------------------------+
|              CAPA DE NEGOCIO Y API REST (Flask + Blueprints)            |
|  [Security Headers] [Rate Limiter] [JWT RBAC] [Central Error Handler]    |
|  +----------------+  +----------------+  +---------------------------+  |
|  | auth_bp        |  | pacientes_bp   |  | profesionales_bp          |  |
|  +----------------+  +----------------+  +---------------------------+  |
|  | disponibilidad |  | turnos_bp      |  | OpenAPI / Swagger (/docs) |  |
|  +----------------+  +----------------+  +---------------------------+  |
|                         [Repository Pattern]                             |
+------------------------------------+------------------------------------+
                                     | Consultas Parametrizadas / SQL
                                     v
+-------------------------------------------------------------------------+
|            CAPA DE DATOS (PostgreSQL / Supabase + RLS Habilitado)       |
|  - Tablas: usuarios, roles, pacientes, profesionales, turnos            |
|  - Row Level Security (RLS): TO authenticated USING (auth.uid() = ...)  |
|  - Constraint Anti-Solapamiento: UNIQUE(id_prof, fecha, hora) WHERE res |
+-------------------------------------------------------------------------+
```

### 2.2. Justificación de Modularidad y Blueprints
Para evitar la formación de un "God Object" o archivo monolítico desorganizado (`app.py`), el backend se descompone en módulos autónomos:
- **`app/blueprints/auth`:** Gestiona el ciclo de vida de credenciales (registro, login, rotación de tokens mediante `/refresh`, y consulta de identidad en `/me`).
- **`app/blueprints/pacientes`:** Implementa el CU01, aislando las reglas de unicidad de Cédula de Identidad (CI) y previniendo la fuga no autorizada del padrón médico.
- **`app/blueprints/profesionales`:** Expone el catálogo de especialidades médicas (Medicina General, Pediatría, Odontología) para alimentar los selectores dinámicos del frontend.
- **`app/blueprints/disponibilidad`:** Implementa el CU02 calculando por sustracción matemática de conjuntos las franjas horarias libres entre la jornada oficial (`08:00` a `16:00`) y los turnos en estado `'reservado'`.
- **`app/blueprints/turnos`:** Centraliza las operaciones transaccionales de los CU03, CU04 y CU05, aplicando validaciones atómicas para impedir dobles reservas.

---

## 3. Modelo de Base de Datos Relacional y Row Level Security (RLS)

### 3.1. Esquema Relacional e Integridad
El modelo relacional fue diseñado en cumplimiento de la Tercera Forma Normal (3FN), garantizando consistencia semántica y eliminando redundancias:
- **`roles`:** Catálogo cerrado de privilegios (`admin`, `recepcionista`, `medico`, `paciente`).
- **`usuarios`:** Identidades de acceso con identificadores UUID v4 (`gen_random_uuid()`), correos normalizados y hashes de contraseña generados mediante PBKDF2/Bcrypt con factor de costo configurable y salt dinámico por registro.
- **`pacientes`:** Almacena la ficha sociodemográfica, vinculada de forma opcional o directa al usuario (`id_usuario UUID UNIQUE`), con expresiones regulares a nivel de base de datos (`CHECK (telefono ~ '^[67][0-9]{7}$')`).
- **`profesionales`:** Registra a los profesionales de la salud, su código institucional (`PRF-001`), especialidad y vigencia operativa.
- **`turnos`:** Registra las reservas de atención médica.

### 3.2. Prevención a Nivel de Motor de Condiciones de Carrera (Race Conditions)
Una vulnerabilidad común en sistemas de salud es el solapamiento de citas médicas cuando dos usuarios seleccionan la misma franja horaria simultáneamente. Para solucionar esto de raíz, se implementó un **índice único parcial** en PostgreSQL:

```sql
CREATE UNIQUE INDEX uq_turno_profesional_fecha_hora_activo
ON public.turnos (id_profesional, fecha, hora)
WHERE estado = 'reservado';
```

Esta directiva instruye al motor PostgreSQL a rechazar con una excepción de violación de unicidad cualquier intento de inserción que colisione con un turno activo, permitiendo al mismo tiempo que turnos cancelados en ese mismo horario sí puedan coexistir en el historial de auditoría.

### 3.3. Políticas Row Level Security (RLS) en Supabase/PostgreSQL
Siguiendo las recomendaciones oficiales de Supabase y las directrices contra *Broken Object Level Authorization (BOLA / IDOR)*, se habilitó RLS de forma obligatoria en la totalidad de tablas públicas:

```sql
ALTER TABLE public.turnos ENABLE ROW LEVEL SECURITY;
```

#### Implementación Segura vs. Implementación Naive
Una falla habitual consiste en declarar directivas genéricas como `TO authenticated USING (true)`, lo cual permite que cualquier usuario autenticado lea o modifique los registros de otros pacientes. La política implementada aplica el principio de mínimo privilegio enlazando la identidad criptográfica del token (`auth.uid()`) con el registro:

```sql
CREATE POLICY "Control de acceso estricto a turnos"
ON public.turnos
FOR SELECT
TO authenticated
USING (
  -- El paciente solo visualiza sus propios turnos
  id_paciente IN (
    SELECT p.id FROM public.pacientes p WHERE p.id_usuario = (SELECT auth.uid())
  )
  OR
  -- El médico solo visualiza los turnos agendados con su persona
  id_profesional IN (
    SELECT pr.id FROM public.profesionales pr WHERE pr.id_usuario = (SELECT auth.uid())
  )
  OR
  -- Recepción y jefatura médica disponen de visibilidad operativa
  public.is_admin_or_staff()
);
```

Para la cancelación de turnos (CU05), la política exige tanto la cláusula `USING` como `WITH CHECK`, impidiendo que un atacante reasigne el turno a otro usuario durante una operación de actualización (OWASP API3:2023).

---

## 4. Seguridad, Autenticación y Matriz OWASP API Security Top 10

### 4.1. Mecanismo de Autenticación JWT y RBAC
El sistema emplea tokens JSON Web Tokens (RFC 7519) firmados con el algoritmo simétrico HMAC-SHA256. Para mitigar los riesgos de secuestro de sesión y garantizar la frescura de permisos:
- **Access Token:** Posee una vigencia estricta de 15 minutos, conteniendo en su payload los claims `sub` (UUID del usuario), `role` (rol RBAC), `paciente_id` y `exp`.
- **Refresh Token:** Posee una vigencia de 7 días y tipo delimitado (`"type": "refresh"`), utilizado exclusivamente en la ruta `/api/v1/auth/refresh` para emitir nuevos Access Tokens sin obligar al usuario a reingresar credenciales.
- **Middleware RBAC (`@roles_required`):** Intercepta la petición antes de su resolución en el controlador, verificando si el claim `role` satisface los privilegios requeridos, emitiendo un código de estado `403 Forbidden` en caso de discrepancia.

### 4.2. Mapeo y Mitigación del Checklist OWASP API Security Top 10 (2023)

| Identificador | Nombre de la Vulnerabilidad | Riesgo en el Contexto de Salud | Medida Técnica Implementada en la API |
|---|---|---|---|
| **API1:2023** | Broken Object Level Authorization (BOLA/IDOR) | Un paciente malicioso modifica el ID del turno en la URL y visualiza o cancela consultas de otros ciudadanos. | **Validación en Doble Capa:** En backend, verificación explícita de `id_usuario == g.current_user['sub']`. En base de datos, políticas RLS con predicados de propiedad. |
| **API2:2023** | Broken Authentication | Fuerza bruta contra credenciales o manipulación de algoritmos en JWT (`alg=none`). | Rate limiting con `Flask-Limiter` (5 intentos/min en login); validación estricta de firma HMAC-SHA256 con rechazo de tokens adulterados o sin claims obligatorios. |
| **API3:2023** | Broken Object Property Level Authorization | Un atacante envía campos adicionales en el JSON (ej. `rol: "admin"` o `estado: "atendido"`) en el registro. | Esquemas **Marshmallow** con modo de carga restringido; los campos desconocidos o privilegios no son aceptados (*Mass Assignment protection*). |
| **API4:2023** | Unrestricted Resource Consumption | Ataques de denegación de servicio (DoS) por peticiones masivas o consultas sin paginación. | Rate limiting global (60-120 req/min por IP) y paginación obligatoria con límites máximos (`limit <= 100`) en listados de pacientes. |
| **API5:2023** | Broken Function Level Authorization (BFLA) | Un usuario con rol paciente invoca endpoints administrativos para extraer listados generales. | Decorador `@roles_required('admin', 'recepcionista')` en endpoints sensibles, respondiendo `403 Forbidden`. |
| **API6:2023** | Unrestricted Access to Sensitive Business Flows | Un bot reserva automáticamente todos los turnos disponibles de un médico impidiendo la atención ciudadana. | Verificación de Cédula de Identidad registrada previa en el centro de salud, límite de rate limiting por usuario y transacción atómica con constraint anti-solapamiento. |
| **API7:2023** | Server Side Request Forgery (SSRF) | La API realiza peticiones HTTP arbitrarias hacia recursos internos. | La API no acepta URLs remotas de clientes ni consume webhooks de orígenes no autenticados. |
| **API8:2023** | Security Misconfiguration | Servidor exponiendo stacktraces con consultas SQL, versiones de software o cabeceras inseguras. | Desactivación de modo debug en producción; manejador centralizado de errores (`error_handler.py`) que enmascara fallos; inyección de cabeceras HTTP (`nosniff`, `DENY`, HSTS, CSP). |
| **API9:2023** | Improper Inventory Management | Endpoints zombies o versiones deprecadas sin autenticación. | Versionado formal en URI (`/api/v1/`), especificación viva OpenAPI 3.0 documentada y sincronizada en Swagger UI (`/api/docs`). |
| **API10:2023**| Unsafe Consumption of APIs | Ingesta no confiable de datos de terceros. | Validación de tipos de datos, sanitización de caracteres especiales y longitud acotada en todas las entradas de usuarios y servicios externos. |

---

## 5. Metodología de Pruebas Automatizadas y Evidencias de Resiliencia

Para comprobar la defensa del backend contra ataques de forma científica y reproducible, se implementó una suite automatizada basada en `pytest` compuesta por 15 pruebas clasificadas en dos grupos:

### 5.1. Pruebas de Ataque y Resiliencia (`test_security.py`)
1. **Inyección SQL en búsqueda de pacientes (`test_ataque_sql_injection_en_busqueda_paciente`):** Se inyecta el payload malicioso `' OR '1'='1' --` en el parámetro `?ci=`. Resultado: el motor parametriza la entrada y responde con `404 Not Found`, sin filtrar registros de terceros.
2. **Inyección SQL en ruta de turnos (`test_ataque_sql_injection_en_turnos`):** Se inyecta `TUR-00000' UNION SELECT * FROM usuarios --`. Resultado: denegado limpiamente con `404 Not Found`.
3. **Ataque BOLA en consulta de turnos (`test_ataque_bola_consultar_turno_ajeno`):** El Paciente 2 (autenticado) solicita el turno privado perteneciente al Paciente 1. Resultado: `403 Forbidden` con mensaje `"Acceso denegado"`.
4. **Ataque BOLA en cancelación de turnos (`test_ataque_bola_cancelar_turno_ajeno`):** El Paciente 2 intenta cancelar el turno del Paciente 1. Resultado: `403 Forbidden` inmediato.
5. **Token manipulado (`test_ataque_token_jwt_manipulado`):** Se envía un token con la firma alterada. Resultado: `401 Unauthorized`.
6. **Acceso no autenticado (`test_ataque_token_sin_cabecera`):** Acceso sin cabecera Bearer a `/api/v1/auth/me`. Resultado: `401 Unauthorized`.
7. **Escalamiento BFLA (`test_ataque_bfla_paciente_intentando_listar_todos_los_pacientes`):** Paciente intenta consultar `/api/v1/pacientes`. Resultado: `403 Forbidden`.
8. **Permisos de administrador (`test_admin_puede_listar_pacientes`):** Administrador consulta `/api/v1/pacientes`. Resultado: `200 OK`.
9. **Condición de carrera / Doble reserva (`test_prevencion_doble_reserva_mismo_horario`):** Se disparan dos reservas sucesivas sobre el mismo profesional, fecha y hora. Resultado: primera reserva `201 Created`, segunda reserva `409 Conflict` con mensaje `"no está disponible"`.
10. **Cabeceras HTTP de seguridad (`test_cabeceras_http_seguridad`):** Comprobación de cabeceras `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security` y `Content-Security-Policy`.

### 5.2. Pruebas Funcionales de Integración (`test_functional_usecases.py`)
- `test_cu01_registrar_paciente`: Validación de inserción con CI y teléfono bolivianos.
- `test_cu02_consultar_disponibilidad`: Cálculo dinámico de franjas horarias libres.
- `test_cu03_reservar_turno`: Reserva efectiva y actualización de franjas libres.
- `test_cu04_consultar_turno`: Búsqueda de turnos por CI.
- `test_cu05_cancelar_turno`: Cancelación exitosa e idempotencia de estado.

**Resultado de ejecución de la suite:**
```
============================= 15 passed in 0.50s ==============================
Status: SUCCESS (100% aprobado)
```

---

## 6. Conclusiones

1. La implementación de la arquitectura modular mediante **Flask Blueprints** y **Application Factory** permitió desacoplar limpiamente los casos de uso del centro de salud periurbano, facilitando una integración armónica con el frontend `turnos-app` y asegurando una alta mantenibilidad y testeabilidad.
2. El uso de **Row Level Security (RLS)** en PostgreSQL/Supabase, combinado con la validación a nivel de controlador, constituye una defensa en profundidad (*Defense in Depth*) que erradica de raíz las vulnerabilidades de tipo BOLA/IDOR, garantizando que el expediente médico de cada paciente permanezca inaccesible para terceros.
3. La parametrización estricta de consultas en el repositorio de datos, sumada al uso de esquemas de validación **Marshmallow**, proporciona inmunidad total frente a inyecciones SQL y ataques de asignación masiva (*Mass Assignment*).
4. La incorporación de un índice único condicional para turnos activos en base de datos resuelve definitivamente el problema crítico de condiciones de carrera y colisiones de horarios concurrentes.

---

## 7. Referencias Bibliográficas (Normas APA 7)

- American Psychological Association. (2020). *Publication manual of the American Psychological Association* (7th ed.). https://doi.org/10.1037/0000165-000
- Fielding, R. T. (2000). *Architectural styles and the design of network-based software architectures* (Doctoral dissertation, University of California, Irvine). Information and Computer Science.
- Grinberg, M. (2018). *Flask web development: Developing web applications with Python* (2nd ed.). O'Reilly Media.
- Jones, M., Bradley, J., & Sakimura, N. (2015). *JSON Web Token (JWT)* (RFC No. 7519). Internet Engineering Task Force (IETF). https://doi.org/10.17487/RFC7519
- National Institute of Standards and Technology. (2020). *Digital identity guidelines: Authentication and lifecycle management* (NIST Special Publication 800-63B). U.S. Department of Commerce. https://doi.org/10.6028/NIST.SP.800-63b
- OWASP Foundation. (2023). *OWASP API Security Top 10 2023*. Open Web Application Security Project. https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- OWASP Foundation. (2021). *OWASP Application Security Verification Standard (ASVS) version 4.0.3*. Open Web Application Security Project. https://owasp.org/www-project-application-security-verification-standard/
- PostgreSQL Global Development Group. (2024). *PostgreSQL 16.2 documentation: Row Security Policies*. PostgreSQL Documentation. https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- Supabase Inc. (2024). *Row Level Security (RLS) best practices and security hardening*. Supabase Documentation. https://supabase.com/docs/guides/database/postgres/row-level-security
