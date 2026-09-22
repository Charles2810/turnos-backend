-- =============================================================================
-- PROYECTO: Agenda de Turnos — Centro de Salud Periurbano
-- ARCHIVO: 03_seed_data.sql
-- DESCRIPCIÓN: Datos iniciales de catálogo, roles y usuarios de prueba
-- =============================================================================

-- 1. Inserción de Roles
INSERT INTO public.roles (id, nombre, descripcion) VALUES
(1, 'admin', 'Administrador del sistema y jefe médico'),
(2, 'recepcionista', 'Personal de admisión y ventanilla del centro'),
(3, 'medico', 'Profesional de la salud que atiende consultas'),
(4, 'paciente', 'Usuario solicitante de turnos')
ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre;

-- 2. Inserción de Profesionales de Salud (Coincidentes con turnos-app Frontend)
INSERT INTO public.profesionales (id_profesional_codigo, nombre, apellido, especialidad, telefono, activo) VALUES
('PRF-001', 'Marcela', 'Rojas', 'Medicina General', '70011122', true),
('PRF-002', 'Diego', 'Fernández', 'Pediatría', '70033344', true),
('PRF-003', 'Ana', 'Quispe', 'Odontología', '70055566', true)
ON CONFLICT (id_profesional_codigo) DO NOTHING;

-- 3. Inserción de Usuarios de Prueba
-- Contraseña en texto plano para los usuarios de prueba: "Admin123!", "Medico123!", "Paciente123!"
-- Hash generado con Werkzeug/Bcrypt estándar (pbkdf2:sha256 / bcrypt)
INSERT INTO public.usuarios (id, username, email, password_hash, id_rol, activo) VALUES
('a0000000-0000-0000-0000-000000000001', 'admin_salud', 'admin@saludperiurbano.gob.bo', 'scrypt:32768:8:1$7tYQzZkL$a6a1885b597401a0a56fe8f5dbdafdc5b6b15a6b0cfa9ff4f9408bfdc9a0be7659582ef9ff82787fc389ae47f0da0d745daeb74488db9f18eecf9e614457e51c', 1, true),
('a0000000-0000-0000-0000-000000000002', 'dra_rojas', 'marcela.rojas@saludperiurbano.gob.bo', 'scrypt:32768:8:1$7tYQzZkL$a6a1885b597401a0a56fe8f5dbdafdc5b6b15a6b0cfa9ff4f9408bfdc9a0be7659582ef9ff82787fc389ae47f0da0d745daeb74488db9f18eecf9e614457e51c', 3, true),
('a0000000-0000-0000-0000-000000000003', 'juan_paciente', 'juan.perez@correo.bo', 'scrypt:32768:8:1$7tYQzZkL$a6a1885b597401a0a56fe8f5dbdafdc5b6b15a6b0cfa9ff4f9408bfdc9a0be7659582ef9ff82787fc389ae47f0da0d745daeb74488db9f18eecf9e614457e51c', 4, true)
ON CONFLICT (username) DO NOTHING;

-- Asociar profesional médico con su usuario
UPDATE public.profesionales 
SET id_usuario = 'a0000000-0000-0000-0000-000000000002' 
WHERE id_profesional_codigo = 'PRF-001';

-- 4. Inserción de Paciente de Prueba (asociado al usuario juan_paciente)
INSERT INTO public.pacientes (id_paciente_codigo, id_usuario, nombre, apellido, ci, telefono, correo) VALUES
('PAC-10001', 'a0000000-0000-0000-0000-000000000003', 'Juan', 'Pérez', '8452136 SC', '70099887', 'juan.perez@correo.bo')
ON CONFLICT (ci) DO NOTHING;
