"""
Módulo de autenticación y gestión de usuarios
Sistema seguro con hashing de contraseñas y sesiones
"""

import sqlite3
import hashlib
import secrets
import os
from datetime import datetime
from functools import wraps
from flask import Blueprint, session, request, jsonify, redirect, url_for, render_template

auth_bp = Blueprint('auth', __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'taller.db')


def get_db():
    """Obtiene conexión a la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando SHA-256 con salt único
    Retorna: hash:salt
    """
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode('utf-8'))
    return f"{hash_obj.hexdigest()}:{salt}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifica si una contraseña coincide con el hash almacenado
    Formato del hash: hash:salt
    """
    try:
        stored_hash, salt = password_hash.split(':')
        hash_obj = hashlib.sha256((password + salt).encode('utf-8'))
        return hash_obj.hexdigest() == stored_hash
    except (ValueError, AttributeError):
        return False


def init_users_table():
    """
    Inicializa la tabla de usuarios y crea el usuario admin por defecto
    Si no existe
    """
    conn = get_db()
    cursor = conn.cursor()

    # Crear tabla de usuarios si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'editor',
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Verificar si existe el usuario admin
    cursor.execute('SELECT id FROM usuarios WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        # Crear usuario admin por defecto
        admin_hash = hash_password('admin123')
        cursor.execute('''
            INSERT INTO usuarios (username, password_hash, role, active)
            VALUES (?, ?, ?, ?)
        ''', ('admin', admin_hash, 'admin', 1))
        print("Usuario 'admin' creado por defecto")

    conn.commit()
    conn.close()


def get_user_by_username(username: str) -> dict:
    """Obtiene un usuario por su nombre de usuario"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict:
    """Obtiene un usuario por su ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users(active_only: bool = False) -> list:
    """Obtiene lista de todos los usuarios"""
    conn = get_db()
    cursor = conn.cursor()
    if active_only:
        cursor.execute('SELECT * FROM usuarios WHERE active = 1 ORDER BY username')
    else:
        cursor.execute('SELECT * FROM usuarios ORDER BY username')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_user(username: str, password: str, role: str = 'editor', active: bool = True) -> tuple:
    """
    Crea un nuevo usuario
    Retorna: (success: bool, message: str, user_id: int|None)
    """
    # Validaciones
    if not username or len(username) < 3:
        return False, "El nombre de usuario debe tener al menos 3 caracteres", None

    if not password or len(password) < 4:
        return False, "La contraseña debe tener al menos 4 caracteres", None

    if role not in ['admin', 'editor']:
        return False, "Rol inválido", None

    # Verificar si el usuario ya existe
    if get_user_by_username(username):
        return False, "El nombre de usuario ya existe", None

    # Crear usuario
    password_hash = hash_password(password)
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO usuarios (username, password_hash, role, active)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, role, 1 if active else 0))
        conn.commit()
        user_id = cursor.lastrowid
        return True, "Usuario creado exitosamente", user_id
    except sqlite3.IntegrityError:
        return False, "El nombre de usuario ya existe", None
    finally:
        conn.close()


def update_user(user_id: int, username: str = None, role: str = None,
                active: bool = None, new_password: str = None) -> tuple:
    """
    Actualiza un usuario existente
    Retorna: (success: bool, message: str)
    """
    user = get_user_by_id(user_id)
    if not user:
        return False, "Usuario no encontrado"

    # No permitir desactivar el último admin activo
    if active is False and user['role'] == 'admin':
        admins = [u for u in get_all_users() if u['role'] == 'admin' and u['active'] == 1]
        if len(admins) <= 1:
            return False, "No se puede desactivar el último administrador activo"

    conn = get_db()
    cursor = conn.cursor()

    try:
        if new_password:
            if len(new_password) < 4:
                return False, "La contraseña debe tener al menos 4 caracteres"
            password_hash = hash_password(new_password)
            cursor.execute('''
                UPDATE usuarios
                SET username = ?, role = ?, active = ?, password_hash = ?, updated_at = ?
                WHERE id = ?
            ''', (username or user['username'], role or user['role'],
                  1 if active is None else (1 if active else 0),
                  password_hash, datetime.now(), user_id))
        else:
            cursor.execute('''
                UPDATE usuarios
                SET username = ?, role = ?, active = ?, updated_at = ?
                WHERE id = ?
            ''', (username or user['username'], role or user['role'],
                  1 if active is None else (1 if active else 0),
                  datetime.now(), user_id))

        conn.commit()
        return True, "Usuario actualizado exitosamente"
    except sqlite3.IntegrityError:
        return False, "El nombre de usuario ya existe"
    finally:
        conn.close()


def delete_user(user_id: int) -> tuple:
    """
    Elimina un usuario
    Retorna: (success: bool, message: str)
    """
    user = get_user_by_id(user_id)
    if not user:
        return False, "Usuario no encontrado"

    # No permitir eliminar el último admin
    if user['role'] == 'admin':
        admins = [u for u in get_all_users() if u['role'] == 'admin']
        if len(admins) <= 1:
            return False, "No se puede eliminar el último administrador"

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
        conn.commit()
        return True, "Usuario eliminado exitosamente"
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> tuple:
    """
    Autentica un usuario
    Retorna: (success: bool, message: str, user: dict|None)
    """
    user = get_user_by_username(username)

    if not user:
        return False, "Usuario o contraseña incorrectos", None

    if not user['active']:
        return False, "Usuario desactivado. Contacte al administrador.", None

    if not verify_password(password, user['password_hash']):
        return False, "Usuario o contraseña incorrectos", None

    return True, "Autenticación exitosa", user


# ═══════════════════════════════════════════
#  DECORADORES DE SEGURIDAD
# ═══════════════════════════════════════════

def login_required(f):
    """Decorador para requerir inicio de sesión"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'No autorizado. Inicie sesión.', 'redirect': '/login'}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'No autorizado. Inicie sesión.', 'redirect': '/login'}), 401
            return redirect(url_for('login_page'))

        user = get_user_by_id(session['user_id'])
        if not user or user['role'] != 'admin':
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Acceso denegado. Se requiere rol de administrador.'}), 403
            return redirect(url_for('home'))

        return f(*args, **kwargs)
    return decorated_function


def editor_or_admin_required(f):
    """Decorador para requerir rol de editor o admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'No autorizado. Inicie sesión.', 'redirect': '/login'}), 401
            return redirect(url_for('login_page'))

        user = get_user_by_id(session['user_id'])
        if not user or user['role'] not in ['admin', 'editor']:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Acceso denegado.'}), 403
            return redirect(url_for('home'))

        return f(*args, **kwargs)
    return decorated_function


def can_delete(f):
    """Decorador para verificar permiso de eliminación (solo admin)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401

        user = get_user_by_id(session['user_id'])
        if not user or user['role'] != 'admin':
            return jsonify({'error': 'Permiso denegado. Solo administradores pueden eliminar.'}), 403

        return f(*args, **kwargs)
    return decorated_function


def get_current_user() -> dict:
    """Obtiene el usuario actual de la sesión"""
    if 'user_id' not in session:
        return None
    return get_user_by_id(session['user_id'])


def get_current_user_role() -> str:
    """Obtiene el rol del usuario actual"""
    user = get_current_user()
    return user['role'] if user else None


def is_admin() -> bool:
    """Verifica si el usuario actual es admin"""
    return get_current_user_role() == 'admin'


def can_access_feature(feature: str) -> bool:
    """
    Verifica si el usuario actual puede acceder a una característica
    Features: 'users', 'settings', 'delete', 'edit', 'create', 'view'
    """
    user = get_current_user()
    if not user:
        return False

    if user['role'] == 'admin':
        return True

    # Permisos para editor
    editor_permissions = ['view', 'create', 'edit']
    return feature in editor_permissions


# ═══════════════════════════════════════════
#  RUTAS DE AUTENTICACIÓN
# ═══════════════════════════════════════════

@auth_bp.route('/login')
def login_page():
    """Página de login"""
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('login.html')


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API de login"""
    from auth.auth import authenticate_user

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos inválidos'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña son requeridos'}), 400

    success, message, user = authenticate_user(username, password)

    if success:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session.permanent = True
        return jsonify({'ok': True, 'message': message, 'user': {'username': user['username'], 'role': user['role']}})
    else:
        return jsonify({'error': message}), 401 if 'incorrectos' in message else 403


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """API de logout"""
    session.clear()
    return jsonify({'ok': True, 'message': 'Sesión cerrada correctamente'})


@auth_bp.route('/logout')
def logout():
    """Logout redirigiendo a login"""
    session.clear()
    return redirect(url_for('login_page'))


@auth_bp.route('/api/auth/check')
@login_required
def check_auth():
    """Verificar estado de autenticación"""
    user = get_current_user()
    if user:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
        })
    return jsonify({'authenticated': False}), 401