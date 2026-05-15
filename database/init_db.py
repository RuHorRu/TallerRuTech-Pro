import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'taller.db')


def ensure_columns(cursor, table, columns):
    existing = {row[1] for row in cursor.execute(f'PRAGMA table_info({table})')}
    for name, definition in columns.items():
        if name not in existing:
            cursor.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dni TEXT UNIQUE NOT NULL,
        nombres TEXT NOT NULL,
        apellidos TEXT NOT NULL,
        tel TEXT,
        email TEXT,
        ciudad TEXT,
        dir TEXT,
        creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ordenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        num TEXT UNIQUE NOT NULL,
        cliente_id INTEGER REFERENCES clientes(id),
        fecha_rec TEXT,
        fecha_ent TEXT,
        tecnico TEXT,
        prioridad TEXT DEFAULT 'Normal',
        estado TEXT DEFAULT 'revision',
        precio REAL,
        creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS equipo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER UNIQUE REFERENCES ordenes(id) ON DELETE CASCADE,
        tipo TEXT, marca TEXT, modelo TEXT, serie TEXT, so TEXT,
        condicion TEXT, accesorios TEXT, falla TEXT,
        procesador TEXT, tarjeta_video TEXT, tarjeta_pcie TEXT,
        ram_total TEXT, almacenamiento_total TEXT, version_bios TEXT
    )
    ''')
    ensure_columns(cursor, 'equipo', {
        'tarjeta_pcie': 'TEXT',
        'version_bios': 'TEXT',
    })

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS visual (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER UNIQUE REFERENCES ordenes(id) ON DELETE CASCADE,
        carcasa TEXT, pantalla TEXT, teclado_vis TEXT, puertos TEXT,
        bisagras TEXT, cargador_inc TEXT, cargador_est TEXT, voltaje TEXT, obs TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS funcional (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER UNIQUE REFERENCES ordenes(id) ON DELETE CASCADE,
        enc_bat TEXT, enc_car TEXT, carga_so TEXT, teclado TEXT, audio TEXT,
        display TEXT, touchpad TEXT, wifi TEXT, usb TEXT, camara TEXT, obs TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bateria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER UNIQUE REFERENCES ordenes(id) ON DELETE CASCADE,
        tool TEXT, disenio TEXT, actual TEXT, salud TEXT, duracion TEXT,
        estado TEXT, obs TEXT, serie TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ram_modulos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER REFERENCES ordenes(id) ON DELETE CASCADE,
        num_modulo INTEGER, capacidad TEXT, tipo_ram TEXT,
        velocidad TEXT, resultado TEXT, pases TEXT, duracion_test TEXT, serie TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS discos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER REFERENCES ordenes(id) ON DELETE CASCADE,
        num_disco INTEGER, marca TEXT, tipo TEXT, capacidad TEXT,
        smart TEXT, horas TEXT, apagados TEXT, sectores TEXT, rendimiento TEXT,
        lectura_max TEXT, lectura_media TEXT, lectura_baja TEXT, serie TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS termica (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER UNIQUE REFERENCES ordenes(id) ON DELETE CASCADE,
        cpu_rep TEXT, cpu_carga TEXT, gpu_rep TEXT, gpu_carga TEXT,
        disco TEXT, ventilacion TEXT, obs TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS diagnostico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER UNIQUE REFERENCES ordenes(id) ON DELETE CASCADE,
        estado_general TEXT, servicio TEXT, diagnostico TEXT,
        trabajos TEXT, repuestos TEXT, obs TEXT, bios_estado TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS diag_fabricante (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER UNIQUE REFERENCES ordenes(id) ON DELETE CASCADE,
        software TEXT, resultado TEXT, obs TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fallas_identificadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER REFERENCES ordenes(id) ON DELETE CASCADE,
        num_falla INTEGER, falla TEXT, componente TEXT, severidad TEXT, prioridad TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS presupuesto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER UNIQUE REFERENCES ordenes(id) ON DELETE CASCADE,
        moneda TEXT DEFAULT 'USD', notas TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS presupuesto_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER REFERENCES ordenes(id) ON DELETE CASCADE,
        num_item INTEGER, descripcion TEXT, tipo TEXT, precio REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS imagenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER REFERENCES ordenes(id) ON DELETE CASCADE,
        seccion TEXT,
        ruta TEXT,
        descripcion TEXT,
        creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')


    # Tabla de Configuración del Taller
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracion_taller (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            nombre_taller TEXT NOT NULL,
            direccion TEXT,
            telefono TEXT,
            tipo_documento TEXT DEFAULT 'RUT',
            numero_documento TEXT
        )
    ''')
    
    # Insertar por defecto si no existe
    cursor.execute('''
        INSERT OR IGNORE INTO configuracion_taller (id, nombre_taller, tipo_documento) 
        VALUES (1, 'Mi Taller', 'RUT')
    ''')


    # Tabla de Técnicos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tecnicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dni TEXT UNIQUE,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            especialidad TEXT,
            telefono TEXT,
            email TEXT,
            activo INTEGER DEFAULT 1,
            creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print('Base de datos verificada correctamente')


if __name__ == '__main__':
    init_db()
