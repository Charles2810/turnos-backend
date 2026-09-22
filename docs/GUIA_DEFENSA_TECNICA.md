# GUIA PARA LA DEFENSA TÉCNICA MAGISTRAL
## SUSTENTACIÓN ORAL DEL BACKEND SEGURO Y BASE DE DATOS (ACTIVIDAD 03)

**Proyecto:** Agenda de Turnos — Centro de Salud Periurbano  
**Objetivo de esta Guía:** Dotar al estudiante de argumentos técnicos sólidos, justificaciones arquitectónicas y un guion paso a paso para la demostración práctica ante el docente o tribunal examinador, alcanzando la máxima calificación (5/5).

---

### 1. Discurso de Apertura (Elevator Pitch Técnico - 2 minutos)

> *"Estimado docente / tribunal: En esta Actividad 03 hemos transformado el prototipo de frontend React (`turnos-app`) en un ecosistema de grado empresarial con una arquitectura de 3 capas. Desarrollamos una API REST en Python con Flask y Blueprints, desacoplando la lógica de negocio en cinco dominios funcionales. En la capa de persistencia, implementamos una base de datos relacional PostgreSQL con Supabase, blindada mediante directivas Row Level Security (RLS) a nivel de kernel para erradicar cualquier posibilidad de vulnerabilidades BOLA/IDOR.*
>
> *Nuestra autenticación opera con JWT firmados criptográficamente y control de acceso basado en roles (RBAC). Además, sometimos el sistema a una auditoría estricta contra el estándar internacional OWASP API Security Top 10 (2023), neutralizando inyecciones SQL, condiciones de carrera en reservas y fugas de información interna. Respaldamos todo esto con documentación interactiva en Swagger OpenAPI y una suite de pruebas automatizadas con 100% de efectividad."*

---

### 2. Batería de Preguntas Difíciles del Docente y Respuestas Maestras

#### Pregunta 1: ¿Por qué eligieron modularizar con Flask Blueprints en lugar de colocar todos los endpoints en un único archivo `app.py`?
- **Respuesta Maestra:**
  *"Un archivo monolítico `app.py` viola el Principio de Responsabilidad Única (SRP) y genera acoplamiento severo, dificultando las pruebas unitarias y el trabajo colaborativo. Mediante **Flask Blueprints** y el patrón **Application Factory** (`create_app`), desacoplamos la aplicación en submódulos independientes (`auth`, `pacientes`, `profesionales`, `disponibilidad`, `turnos`). Esto nos permite registrar middlewares específicos, versionar la API (ej. `/api/v1/`), aislar los manejadores de errores y facilitar que cada módulo mantenga sus propios esquemas de validación y pruebas de integración sin interferir en los demás."*

#### Pregunta 2: Si el frontend en React ya valida el CI boliviano y el formato de celular, ¿por qué vuelven a validarlo en el backend con Marshmallow?
- **Respuesta Maestra:**
  *"Porque la validación en el cliente (Frontend) responde a un principio de **Experiencia de Usuario (UX)**, no de **Seguridad**. Cualquier usuario malicioso o atacante puede eludir el frontend utilizando herramientas como Postman, cURL o Burp Suite y enviar payloads malformados directamente a la API REST. Aplicamos el principio de **'Defensa en Profundidad' (Defense in Depth)** y de **'Nunca confiar en la entrada del cliente' (Zero Trust Input)**: los esquemas Marshmallow en el backend sanitizan y validan estrictamente las expresiones regulares del CI y celular, y adicionalmente definimos restricciones `CHECK` a nivel de base de datos en PostgreSQL."*

#### Pregunta 3: ¿Cómo garantiza el sistema que dos pacientes no reserven el mismo médico y horario simultáneamente (Condición de Carrera / Race Condition)?
- **Respuesta Maestra:**
  *"Resolver el solapamiento únicamente con lógica de aplicación (un `SELECT` y luego un `INSERT`) es vulnerable a condiciones de carrera bajo concurrencia real, ya que dos solicitudes simultáneas pueden pasar la comprobación antes de que la primera termine de escribir. Para resolverlo definitivamente, implementamos una solución en dos niveles:*
  1. *A nivel de API, una comprobación atómica previa en la capa de servicios.*
  2. *A nivel de motor relacional en PostgreSQL/Supabase, creamos un **índice único condicional**:*
     ```sql
     CREATE UNIQUE INDEX uq_turno_profesional_fecha_hora_activo
     ON public.turnos (id_profesional, fecha, hora)
     WHERE estado = 'reservado';
     ```
     *Si dos solicitudes intentan insertarse en el mismo milisegundo, el kernel de PostgreSQL rechaza atómicamente la segunda con una violación de unicidad, que nuestra API captura limpiamente y devuelve como un **HTTP 409 Conflict**."*

#### Pregunta 4: ¿Qué es la vulnerabilidad BOLA / IDOR (OWASP API1:2023) y cómo la neutralizaron en su código y en la base de datos?
- **Respuesta Maestra:**
  *"BOLA (Broken Object Level Authorization), antes conocido como IDOR, ocurre cuando la API expone un identificador de objeto (ej. `/api/v1/turnos/TUR-12345`) y no valida si el usuario que solicita el recurso es el legítimo propietario, permitiendo que un paciente acceda al historial médico de otro.*
  *Nosotros la neutralizamos con un **doble anillo de seguridad**:*
  1. *En el controlador de la API (`turnos/routes.py`), extraemos la identidad del usuario desde el JWT (`g.current_user['sub']`) y comprobamos que coincida con el titular del turno; si no coincide y no es médico/administrador, respondemos con **HTTP 403 Forbidden**.*
  2. *En la base de datos (PostgreSQL/Supabase), activamos **Row Level Security (RLS)** con la política:*
     ```sql
     CREATE POLICY "Control de acceso a turnos" ON public.turnos
     TO authenticated
     USING (id_paciente IN (SELECT id FROM pacientes WHERE id_usuario = auth.uid()) OR is_admin_or_staff());
     ```
     *Incluso si la API fuera vulnerada o existiera una omisión en el código Python, el motor de base de datos jamás devolverá los registros a un usuario no autorizado."*

#### Pregunta 5: ¿Por qué es una mala práctica en Supabase definir una política RLS con `TO authenticated USING (true)`?
- **Respuesta Maestra:**
  *"Porque `TO authenticated` solo comprueba que la petición incluya un token JWT válido (autenticación), pero `USING (true)` anula el control de acceso (autorización). Esto genera una falsa sensación de seguridad, ya que cualquier usuario autenticado de la plataforma —incluso un paciente recién registrado— podría leer o alterar la totalidad de las filas de la tabla de turnos o pacientes de cualquier otro ciudadano. El estándar de Supabase exige siempre combinar `TO authenticated` con un predicado de pertenencia: `USING (id_usuario = auth.uid())`."*

#### Pregunta 6: ¿Por qué utilizan un Access Token con tiempo de expiración corto (15 min) y un Refresh Token separado?
- **Respuesta Maestra:**
  *"Los tokens JWT son 'stateless': una vez emitidos y firmados, son válidos hasta que expiran y no pueden ser invalidados individualmente sin mantener una lista negra en memoria o base de datos. Si un atacante intercepta un token con expiración de 24 horas o un mes, tendrá acceso irrestricto durante todo ese tiempo. Al otorgar al **Access Token una vigencia de 15 minutos**, reducimos drásticamente la ventana de ataque. El **Refresh Token (7 días)** vive de forma segura y solo se intercambia contra el endpoint `/api/v1/auth/refresh` para rotar credenciales y actualizar claims de roles cuando sea estrictamente necesario (OWASP API2:2023)."*

#### Pregunta 7: ¿Cómo aseguran que las respuestas de la API no filtren información técnica ante fallos imprevistos?
- **Respuesta Maestra:**
  *"Cumpliendo con el estándar **OWASP API8:2023 (Security Misconfiguration)**, desarrollamos el módulo `error_handler.py`. Registramos manejadores globales para excepciones HTTP (400, 401, 403, 404, 409, 429) y errores no controlados (500). En entorno de producción, las excepciones internas y errores de sintaxis SQL se envían a logs auditables en el servidor y al cliente se le retorna únicamente una respuesta JSON limpia y sanitizada como: `{"error": "Ha ocurrido un error interno en el servidor"}`. Nunca exponemos trazas de pila (stack traces), versiones de librerías ni sentencias SQL."*

---

### 3. Guion de Demostración Práctica en Vivo (Paso a Paso)

Durante la presentación frente al docente, sigue esta secuencia exacta:

#### Paso 1: Ejecutar la Suite de Pruebas Automatizadas
Abre una terminal en la carpeta `backend` y ejecuta:
```bash
python -m pytest tests/ -v
```
**Lo que debes señalarle al docente:**
- *"Observe, profesor, cómo se ejecutan 15 pruebas de resiliencia y funcionalidad en medio segundo."*
- Señala en la pantalla los tests de seguridad específicos:
  - `test_ataque_sql_injection_en_busqueda_paciente` (Aprobado: neutralización de SQLi).
  - `test_ataque_bola_consultar_turno_ajeno` (Aprobado: devuelve HTTP 403 cuando un paciente intenta espiar a otro).
  - `test_prevencion_doble_reserva_mismo_horario` (Aprobado: devuelve HTTP 409 ante colisión de turnos).
  - `test_cabeceras_http_seguridad` (Aprobado: inyección de CSP, HSTS y X-Content-Type-Options).

#### Paso 2: Iniciar el Servidor y Mostrar la Documentación Swagger
Ejecuta en la terminal:
```bash
python run.py
```
Abre el navegador en `http://127.0.0.1:5000/api/docs`.  
**Lo que debes señalarle al docente:**
- Muestra la consola interactiva Swagger UI con todos los Blueprints agrupados (`Autenticación`, `Pacientes`, `Profesionales`, `Disponibilidad`, `Turnos`).
- Muestra el botón **Authorize** en la esquina superior derecha donde se ingresa el token Bearer JWT.
- Ejecuta una consulta en vivo en `GET /api/v1/profesionales` pulsando **"Try it out" -> "Execute"**, demostrando la respuesta JSON inmediata con los tres médicos del frontend.
- Ejecuta una consulta en `GET /api/v1/disponibilidad` enviando `id_profesional: PRF-001` y fecha de hoy para mostrar cómo se calculan las horas libres.

#### Paso 3: Explicar los Scripts SQL de Supabase y las Políticas RLS
Abre en el editor el archivo `database_schema/02_rls_policies.sql`.  
**Lo que debes señalarle al docente:**
- *"Aquí puede ver la activación explícita de Row Level Security con `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`."*
- Explica la política de turnos mostrando cómo se protege al paciente con `id_usuario = auth.uid()` y cómo se habilita a los médicos y administradores mediante la función de seguridad `is_admin_or_staff()`.*

#### Paso 4: Mostrar la Matriz de Auditoría de IA
Abre el archivo `docs/MATRIZ_AUDITORIA_IA.md`.  
**Lo que debes señalarle al docente:**
- *"En cumplimiento estricto de la rúbrica de evaluación, no nos quedamos con el código generado por IA. En esta matriz evidenciamos 10 vulnerabilidades críticas generadas inicialmente por la IA (como BOLA, RLS permisivo, falta de índices y sentencias SQL no parametrizadas) y cómo aplicamos correcciones humanas fundamentadas en OWASP para garantizar la máxima seguridad."*
