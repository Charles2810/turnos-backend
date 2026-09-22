-- =============================================================================
-- PROYECTO: Agenda de Turnos — Centro de Salud Periurbano
-- ARCHIVO: 02_rls_policies.sql
-- DESCRIPCIÓN: Políticas de Row Level Security (RLS) para PostgreSQL / Supabase
-- CUMPLE: Estándar estricto de Supabase contra BOLA/IDOR (OWASP API1:2023)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Habilitación Obligatoria de RLS en todas las tablas expuestas
-- -----------------------------------------------------------------------------
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pacientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profesionales ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.turnos ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- Funciones Auxiliares Seguras (SECURITY INVOKER)
-- -----------------------------------------------------------------------------
-- Obtener el ID de usuario autenticado
CREATE OR REPLACE FUNCTION public.current_user_id()
RETURNS UUID
LANGUAGE sql STABLE
AS $$
  SELECT auth.uid();
$$;

-- Verificar si el usuario actual tiene rol de Administrador / Recepcionista
CREATE OR REPLACE FUNCTION public.is_admin_or_staff()
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 
    FROM public.usuarios u
    JOIN public.roles r ON u.id_rol = r.id
    WHERE u.id = auth.uid() 
      AND r.nombre IN ('admin', 'recepcionista')
  );
$$;

-- Verificar si el usuario actual es un profesional médico
CREATE OR REPLACE FUNCTION public.is_medico()
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 
    FROM public.usuarios u
    JOIN public.roles r ON u.id_rol = r.id
    WHERE u.id = auth.uid() 
      AND r.nombre = 'medico'
  );
$$;

-- -----------------------------------------------------------------------------
-- 2. Políticas RLS para la tabla ROLES
-- Lectura pública para usuarios autenticados; escritura solo administradores
-- -----------------------------------------------------------------------------
CREATE POLICY "Roles son visibles para usuarios autenticados"
ON public.roles
FOR SELECT
TO authenticated
USING (true);

-- -----------------------------------------------------------------------------
-- 3. Políticas RLS para la tabla USUARIOS
-- Los usuarios solo pueden ver y editar su propio perfil; el personal administrativo puede ver el listado
-- -----------------------------------------------------------------------------
CREATE POLICY "Usuarios pueden consultar su propio registro"
ON public.usuarios
FOR SELECT
TO authenticated
USING (
  (SELECT auth.uid()) = id OR public.is_admin_or_staff()
);

CREATE POLICY "Usuarios pueden actualizar su propio registro"
ON public.usuarios
FOR UPDATE
TO authenticated
USING ((SELECT auth.uid()) = id)
WITH CHECK ((SELECT auth.uid()) = id);

-- -----------------------------------------------------------------------------
-- 4. Políticas RLS para la tabla PROFESIONALES
-- El catálogo médico es de lectura libre para seleccionar profesional (CU02, CU03)
-- Modificación exclusiva para personal administrativo
-- -----------------------------------------------------------------------------
CREATE POLICY "Cualquier usuario autenticado o anónimo puede consultar profesionales"
ON public.profesionales
FOR SELECT
TO anon, authenticated
USING (activo = true);

CREATE POLICY "Solo administradores pueden crear o modificar profesionales"
ON public.profesionales
FOR ALL
TO authenticated
USING (public.is_admin_or_staff())
WITH CHECK (public.is_admin_or_staff());

-- -----------------------------------------------------------------------------
-- 5. Políticas RLS para la tabla PACIENTES (CU01)
-- - Pacientes ven su propia ficha.
-- - Personal de salud y recepción pueden ver fichas para coordinar turnos.
-- -----------------------------------------------------------------------------
CREATE POLICY "Pacientes ven su propia ficha médica y personal administrativo ve todas"
ON public.pacientes
FOR SELECT
TO authenticated
USING (
  id_usuario = (SELECT auth.uid()) OR public.is_admin_or_staff() OR public.is_medico()
);

CREATE POLICY "Registro de paciente por el propio usuario o recepción"
ON public.pacientes
FOR INSERT
TO authenticated
WITH CHECK (
  id_usuario = (SELECT auth.uid()) OR public.is_admin_or_staff()
);

CREATE POLICY "Actualización de ficha de paciente controlada"
ON public.pacientes
FOR UPDATE
TO authenticated
USING (
  id_usuario = (SELECT auth.uid()) OR public.is_admin_or_staff()
)
WITH CHECK (
  id_usuario = (SELECT auth.uid()) OR public.is_admin_or_staff()
);

-- -----------------------------------------------------------------------------
-- 6. Políticas RLS para la tabla TURNOS (CU03, CU04, CU05)
-- PROTECCIÓN DIRECTA CONTRA BOLA / IDOR (OWASP API1:2023):
-- - El paciente SOLO puede ver sus turnos propios.
-- - El médico SOLO puede ver turnos asignados a su persona.
-- - Administradores/recepcionistas pueden ver todos los turnos.
-- -----------------------------------------------------------------------------
CREATE POLICY "Control de acceso estricto a consulta de turnos"
ON public.turnos
FOR SELECT
TO authenticated
USING (
  -- El paciente solo ve los suyos
  id_paciente IN (
    SELECT p.id FROM public.pacientes p WHERE p.id_usuario = (SELECT auth.uid())
  )
  OR
  -- El médico solo ve turnos asignados a él
  id_profesional IN (
    SELECT pr.id FROM public.profesionales pr WHERE pr.id_usuario = (SELECT auth.uid())
  )
  OR
  -- Recepción y administración
  public.is_admin_or_staff()
);

-- Inserción de turnos: el paciente solo puede reservar turnos para sí mismo, o recepción
CREATE POLICY "Pacientes pueden crear reservas para su propio perfil"
ON public.turnos
FOR INSERT
TO authenticated
WITH CHECK (
  id_paciente IN (
    SELECT p.id FROM public.pacientes p WHERE p.id_usuario = (SELECT auth.uid())
  )
  OR
  public.is_admin_or_staff()
);

-- Cancelación de turnos (CU05):
-- El paciente solo puede cancelar sus propios turnos. Requiere USING y WITH CHECK
CREATE POLICY "Pacientes pueden cancelar sus propios turnos y recepción cualquiera"
ON public.turnos
FOR UPDATE
TO authenticated
USING (
  id_paciente IN (
    SELECT p.id FROM public.pacientes p WHERE p.id_usuario = (SELECT auth.uid())
  )
  OR
  public.is_admin_or_staff()
)
WITH CHECK (
  id_paciente IN (
    SELECT p.id FROM public.pacientes p WHERE p.id_usuario = (SELECT auth.uid())
  )
  OR
  public.is_admin_or_staff()
);
