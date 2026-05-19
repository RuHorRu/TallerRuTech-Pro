import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, 'taller.db')


def get_db():

    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = WAL')
    conn.row_factory = sqlite3.Row

    return conn

def guardar_configuracion_taller(datos):
    """Actualiza los datos del taller"""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE configuracion_taller 
        SET nombre_taller=?, direccion=?, telefono=?, tipo_documento=?, numero_documento=?
        WHERE id = 1
    ''', (datos['nombre'], datos['direccion'], datos['telefono'], datos['tipo_doc'], datos['num_doc']))
    conn.commit()
    conn.close()

def obtener_configuracion_taller():
    """Lee los datos del taller"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM configuracion_taller WHERE id = 1')
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


# ===========================
#  FUNCIONES DE TECNICOS
# ===========================

def obtener_tecnicos(filtro_activo=None):
    """Obtiene lista de técnicos, opcionalmente filtrados por estado activo"""
    conn = get_db()
    c = conn.cursor()
    if filtro_activo is not None:
        c.execute('SELECT * FROM tecnicos WHERE activo = ? ORDER BY apellidos, nombres', (1 if filtro_activo else 0,))
    else:
        c.execute('SELECT * FROM tecnicos ORDER BY apellidos, nombres')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def obtener_tecnico(id_tecnico):
    """Obtiene un técnico por ID"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM tecnicos WHERE id = ?', (id_tecnico,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def guardar_tecnico(datos):
    """Crea o actualiza un técnico"""
    conn = get_db()
    c = conn.cursor()

    tecnico_id = datos.get('id')

    if tecnico_id:
        # Actualizar
        c.execute('''
            UPDATE tecnicos
            SET dni=?, nombres=?, apellidos=?, especialidad=?, telefono=?, email=?, activo=?
            WHERE id=?
        ''', (
            datos.get('dni'),
            datos.get('nombres'),
            datos.get('apellidos'),
            datos.get('especialidad'),
            datos.get('telefono'),
            datos.get('email'),
            1 if datos.get('activo', True) else 0,
            tecnico_id
        ))
    else:
        # Crear nuevo
        c.execute('''
            INSERT INTO tecnicos (dni, nombres, apellidos, especialidad, telefono, email, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datos.get('dni'),
            datos.get('nombres'),
            datos.get('apellidos'),
            datos.get('especialidad'),
            datos.get('telefono'),
            datos.get('email'),
            1 if datos.get('activo', True) else 0
        ))
        tecnico_id = c.lastrowid

    conn.commit()
    conn.close()
    return tecnico_id

def eliminar_tecnico(id_tecnico):
    """Elimina un técnico por ID"""
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM tecnicos WHERE id = ?', (id_tecnico,))
    conn.commit()
    conn.close()
    return True