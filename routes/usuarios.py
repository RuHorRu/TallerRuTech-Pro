"""
Módulo de gestión de usuarios (API REST)
Solo accesible para administradores
"""

import os
from flask import Blueprint, request, jsonify
from auth.auth import login_required, admin_required, get_current_user
from routes.auth import (
    get_all_users, create_user, update_user, delete_user,
    hash_password, get_user_by_id
)

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/api')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'taller.db')


@usuarios_bp.route('/usuarios', methods=['GET'])
@login_required
def api_get_usuarios():
    """Obtener lista de usuarios (solo admin)"""
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Acceso denegado. Solo administradores.'}), 403

    users = get_all_users()
    # No enviar hashes de contraseña
    for u in users:
        u.pop('password_hash', None)

    return jsonify(users)


@usuarios_bp.route('/usuarios', methods=['POST'])
@login_required
@admin_required
def api_create_usuario():
    """Crear nuevo usuario (solo admin)"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos inválidos'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'editor')
    active = data.get('active', True)

    success, message, user_id = create_user(username, password, role, active)

    if success:
        return jsonify({'ok': True, 'message': message, 'user_id': user_id}), 201
    else:
        return jsonify({'error': message}), 400


@usuarios_bp.route('/usuarios/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def api_update_usuario(user_id):
    """Actualizar usuario existente (solo admin)"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos inválidos'}), 400

    username = data.get('username')
    role = data.get('role')
    active = data.get('active')
    new_password = data.get('password')

    success, message = update_user(
        user_id=user_id,
        username=username,
        role=role,
        active=active,
        new_password=new_password
    )

    if success:
        return jsonify({'ok': True, 'message': message})
    else:
        return jsonify({'error': message}), 400


@usuarios_bp.route('/usuarios/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_usuario(user_id):
    """Eliminar usuario (solo admin)"""
    success, message = delete_user(user_id)

    if success:
        return jsonify({'ok': True, 'message': message})
    else:
        return jsonify({'error': message}), 400


@usuarios_bp.route('/usuarios/<int:user_id>/cambiar-password', methods=['POST'])
@login_required
@admin_required
def api_change_password(user_id):
    """Cambiar contraseña de usuario (solo admin)"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos inválidos'}), 400

    new_password = data.get('new_password', '')

    if not new_password or len(new_password) < 4:
        return jsonify({'error': 'La contraseña debe tener al menos 4 caracteres'}), 400

    success, message = update_user(user_id=user_id, new_password=new_password)

    if success:
        return jsonify({'ok': True, 'message': message})
    else:
        return jsonify({'error': message}), 400