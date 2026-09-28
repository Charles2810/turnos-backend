# ESTRUCTURA Y GUION DE DIAPOSITIVAS PARA LA PRESENTACIÓN
## ACTIVIDAD 03: BACKEND SEGURO Y BASE DE DATOS (AGENDA DE TURNOS)

Este documento contiene la estructura lista diapositiva por diapositiva para tu presentación (PowerPoint, Canva o Google Slides), junto con lo que debes decir oralmente en cada lámina.

---

### Diapositiva 1: Portada
* **Título:** Agenda de Turnos — Centro de Salud Periurbano
* **Subtítulo:** Actividad 03: Arquitectura Backend Seguro, Base de Datos PostgreSQL/Supabase con RLS y Auditoría OWASP
* **Integrantes:** [Nombres y Apellidos]
* **Asignatura:** Programación Web II
* **Docente:** [Nombre del Docente]
* **Fecha:** Septiembre de 2026

> **Qué decir:** *"Buenos días/tardes. Hoy presentamos el desarrollo de la Capa de Backend y Base de Datos para el sistema de turnos de un centro de salud periurbano, pasando del frontend MVP previo a una arquitectura empresarial segura y auditada bajo normas OWASP."*

---

### Diapositiva 2: Planteamiento del Problema y Objetivos
* **Contexto:** Centro de salud periurbano con alta demanda de citas y datos médicos sensibles (Ley N.º 3131).
* **Limitación del MVP previo:** Persistencia simulada en `localStorage` (sin concurrencia, sin seguridad de datos).
* **Objetivo Actividad 03:**
  1. API REST modular en Flask con Blueprints.
  2. Base de datos relacional PostgreSQL en Supabase con Row Level Security (RLS).
  3. Autenticación robusta con JWT y control de acceso por roles (RBAC).
  4. Mitigación demostrable del catálogo OWASP API Security Top 10 (2023).

> **Qué decir:** *"En la fase anterior teníamos el frontend en React pero los datos vivían en el navegador. Nuestro objetivo fue crear una API REST profesional que garantice integridad referencial, evite dobles reservas y blinde la privacidad de los pacientes."*

---

### Diapositiva 3: Arquitectura de 3 Capas y Modularidad (Flask Blueprints)
* **Diagrama visual:**
  * Capa 1: Frontend React 19 (`turnos-app`).
  * Capa 2: Backend Flask + Blueprints (`auth`, `pacientes`, `profesionales`, `disponibilidad`, `turnos`).
  * Capa 3: Persistencia PostgreSQL en Supabase.
* **Patrón Application Factory:** Desacoplamiento de configuración (dev, test, prod) y registro limpio de extensiones (CORS, Limiter, Swagger).

> **Qué decir:** *"Estructuramos el backend con Flask Blueprints dividiéndolo en 5 módulos independientes. Esto evita el código monolítico y facilita el mantenimiento y la auditoría de cada caso de uso."*

---

### Diapositiva 4: Base de Datos Relacional y Prevención de Concurrencia
* **Modelo Entidad-Relación:** Tablas `roles`, `usuarios`, `pacientes`, `profesionales` y `turnos`.
* **Claves foráneas e Índices B-Tree:** Optimizados según las guías de Supabase para evitar escaneos secuenciales lentos.
* **El problema del solapamiento:** Si dos pacientes reservan el mismo horario al mismo segundo, la lógica simple falla.
* **Nuestra solución técnica:** **Índice único condicional en PostgreSQL**:
  ```sql
  CREATE UNIQUE INDEX uq_turno_profesional_fecha_hora_activo
  ON public.turnos (id_profesional, fecha, hora)
  WHERE estado = 'reservado';
  ```

> **Qué decir:** *"Para resolver las colisiones de citas concurrentes, no nos fiamos solo del código de la aplicación: creamos un índice único condicional a nivel de motor en PostgreSQL. Si dos pacientes intentan reservar el mismo horario simultáneamente, la base de datos lo rechaza atómicamente y la API devuelve HTTP 409 Conflict."*

---

### Diapositiva 5: Row Level Security (RLS) en Supabase (Defensa anti-BOLA/IDOR)
* **¿Qué es BOLA/IDOR?** Vulnerabilidad crítica (OWASP API1:2023) donde un paciente cambia el ID en la URL y ve citas ajenas.
* **RLS habilitado en el 100% de tablas públicas.**
* **Políticas granulares basadas en roles:**
  * `TO authenticated USING (id_paciente IN (SELECT id FROM pacientes WHERE id_usuario = auth.uid()))`
  * Personal médico solo ve sus consultas asignadas.
  * Personal administrativo gestiona la operación global.

> **Qué decir:** *"Activamos Row Level Security en todas las tablas de Supabase. A diferencia de las políticas ingenuas que solo verifican si el usuario está logueado, nuestras directivas comparan la identidad del token criptográfico con el propietario del registro. Un paciente jamás podrá ver o cancelar turnos de otros."*

---

### Diapositiva 6: Seguridad, Autenticación JWT y RBAC
* **Ciclo de vida de tokens:**
  * **Access Token:** Corta duración (15 minutos) firmado con HMAC-SHA256.
  * **Refresh Token:** 7 días para rotación controlada sin exponer credenciales.
* **Decorador RBAC:** `@roles_required('admin', 'recepcionista')` para blindar funciones privilegiadas (anti-BFLA).
* **Hashes seguros:** Contraseñas encriptadas con PBKDF2/Bcrypt con salt dinámico.

> **Qué decir:** *"Implementamos una arquitectura de doble token. El token de acceso solo dura 15 minutos, lo que minimiza la ventana de ataque ante robos de sesión, mientras que las contraseñas se resguardan con algoritmos de hashing modernos."*

---

### Diapositiva 7: Auditoría de Seguridad OWASP API Security Top 10
* **Tabla resumen de mitigaciones:**
  * **API1 (BOLA):** Resuelto con validación en controlador y políticas RLS.
  * **API2 (Broken Auth):** Tokens seguros y rate limiting en login.
  * **API3 (Mass Assignment):** Esquemas Marshmallow con regex estrictas.
  * **API4 (Resource Consumption):** Rate Limiter (60 req/min) y paginación.
  * **API8 (Security Misconfiguration):** Manejador centralizado de errores que nunca expone trazas SQL ni stack traces; inyección de cabeceras CSP y HSTS.

> **Qué decir:** *"Auditamos todo el código contra el top 10 de OWASP para APIs, asegurando que ninguna excepción interna filtre nombres de tablas o versiones del sistema."*

---

### Diapositiva 8: Matriz de Auditoría de Inteligencia Artificial (Aporte Humano vs. IA)
* **¿Qué generó la IA inicialmente?**
  * Endpoints sin control de pertenencia (vulnerables a BOLA).
  * Políticas RLS permisivas (`USING (true)`).
  * Consultas con strings concatenados (riesgo de inyección SQL).
  * Esquemas sin restricciones de concurrencia.
* **¿Qué corrigió y añadió el desarrollador humano?**
  * Refactorización a DTOs con Marshmallow.
  * Consultas 100% parametrizadas.
  * Índice condicional único anti-solapamiento.
  * Doble factor de autorización y Rate Limiting.

> **Qué decir:** *"En la matriz de auditoría de IA demostramos cómo la IA genera prototipos funcionales pero inseguros. Nuestra intervención humana experta identificó y corrigió 10 vulnerabilidades críticas para elevar la solución a nivel empresarial."*

---

### Diapositiva 9: Pruebas Automatizadas y Demostración en Vivo
* **Resultados de Pytest:** 15 pruebas automatizadas (10 de seguridad contra OWASP + 5 funcionales de los casos de uso).
* **Efectividad:** 100% de tests aprobados en ~0.5 segundos.
* **Documentación viva:** Swagger UI en `/api/docs` con botón Authorize para probar la API interactivamente.
* **Despliegue en la Nube:** API REST y Swagger en vivo en Render: `https://turnos-backend-api-1gq9.onrender.com/api/docs`.
* *(Aquí se da paso a la demostración en vivo de 2 minutos).*

> **Qué decir:** *"Todo lo afirmado en esta presentación no es teórico: está validado mediante una suite de 15 pruebas automatizadas y la API ya se encuentra desplegada en la nube en Render con Swagger UI interactivo y conectada a PostgreSQL en Supabase."*

---

### Diapositiva 10: Conclusiones
1. Cumplimiento integral de los 5 casos de uso del centro de salud periurbano.
2. Persistencia en la nube segura con PostgreSQL/Supabase y RLS activo.
3. Arquitectura backend altamente modular, escalable y resistente a ciberataques.
4. Documentación formal en APA 7 y matriz de auditoría de IA completas.

> **Qué decir:** *"Concluimos con un sistema completamente listo para producción, seguro por diseño y defendible ante cualquier tribunal de evaluación. Muchas gracias, quedamos atentos a sus preguntas."*
