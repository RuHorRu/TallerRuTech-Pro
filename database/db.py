import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, 'taller.db')


def get_db():

    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')

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