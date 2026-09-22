-- =============================================================================
-- PROYECTO: Agenda de Turnos — Centro de Salud Periurbano
-- ARCHIVO: 01_schema.sql
-- DESCRIPCIÓN: Esquema Relacional de Base de Datos para PostgreSQL / Supabase
-- CUMPLE: Buenas prácticas de rendimiento e integridad referencial de Supabase
-- =============================================================================

-- Extensiones recomendadas
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------------------------
-- 1. Tabla de Roles (RBAC)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.roles IS 'Catálogo de roles del sistema (paciente, medico, recepcionista, admin).';

-- -----------------------------------------------------------------------------
-- 2. Tabla de Usuarios (Credenciales y control de acceso)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    id_rol INT NOT NULL REFERENCES public.roles(id) ON DELETE RESTRICT,
    activo BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.usuarios IS 'Cuentas de autenticación con hash bcrypt.';

-- -----------------------------------------------------------------------------
-- 3. Tabla de Pacientes (CU01)
-- Vinculada opcional o directamente con el usuario autenticado
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.pacientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_paciente_codigo VARCHAR(20) NOT NULL UNIQUE, -- Ej. PAC-12345
    id_usuario UUID UNIQUE REFERENCES public.usuarios(id) ON DELETE SET NULL,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    ci VARCHAR(20) NOT NULL UNIQUE,                -- Cédula de identidad boliviana
    telefono VARCHAR(15) NOT NULL,                 -- Celular boliviano 8 dígitos
    correo VARCHAR(120) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT chk_paciente_telefono CHECK (telefono ~ '^[67][0-9]{7}$'),
    CONSTRAINT chk_paciente_correo CHECK (correo ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

COMMENT ON TABLE public.pacientes IS 'Fichas de pacientes del centro de salud periurbano.';

-- -----------------------------------------------------------------------------
-- 4. Tabla de Profesionales Médicos
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profesionales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_profesional_codigo VARCHAR(20) NOT NULL UNIQUE, -- Ej. PRF-001
    id_usuario UUID UNIQUE REFERENCES public.usuarios(id) ON DELETE SET NULL,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    especialidad VARCHAR(80) NOT NULL,
    telefono VARCHAR(15) NOT NULL,
    activo BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.profesionales IS 'Plantel de médicos y especialistas del centro de salud.';

-- -----------------------------------------------------------------------------
-- 5. Tabla de Turnos (CU03, CU04, CU05)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.turnos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_turno_codigo VARCHAR(20) NOT NULL UNIQUE, -- Ej. TUR-A1B2C
    id_paciente UUID NOT NULL REFERENCES public.pacientes(id) ON DELETE RESTRICT,
    id_profesional UUID NOT NULL REFERENCES public.profesionales(id) ON DELETE RESTRICT,
    fecha DATE NOT NULL,
    hora VARCHAR(10) NOT NULL,                  -- '08:00', '09:00', etc.
    estado VARCHAR(20) DEFAULT 'reservado' NOT NULL,
    motivo_cancelacion TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT chk_turno_estado CHECK (estado IN ('reservado', 'cancelado', 'atendido'))
);

COMMENT ON TABLE public.turnos IS 'Reservas de atención médica con control de solapamiento.';

-- -----------------------------------------------------------------------------
-- 6. Índices de Alto Rendimiento y Restricción Anti-Solapamiento
-- (Según las guías de optimización de Supabase: indexar FKs y filtros frecuentes)
-- -----------------------------------------------------------------------------

-- Restricción única parcial: Impide que dos turnos activos tengan el mismo profesional, fecha y hora
CREATE UNIQUE INDEX IF NOT EXISTS uq_turno_profesional_fecha_hora_activo
ON public.turnos (id_profesional, fecha, hora)
WHERE estado = 'reservado';

-- Índices B-tree en Claves Foráneas para evitar sequential scans en JOINs
CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON public.usuarios(id_rol);
CREATE INDEX IF NOT EXISTS idx_pacientes_usuario ON public.pacientes(id_usuario);
CREATE INDEX IF NOT EXISTS idx_pacientes_ci ON public.pacientes(ci);
CREATE INDEX IF NOT EXISTS idx_profesionales_usuario ON public.profesionales(id_usuario);
CREATE INDEX IF NOT EXISTS idx_turnos_paciente ON public.turnos(id_paciente);
CREATE INDEX IF NOT EXISTS idx_turnos_profesional ON public.turnos(id_profesional);
CREATE INDEX IF NOT EXISTS idx_turnos_fecha_hora ON public.turnos(fecha, hora);
CREATE INDEX IF NOT EXISTS idx_turnos_estado ON public.turnos(estado);
