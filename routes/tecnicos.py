from flask import Blueprint, request, jsonify
from database.db import get_db
from auth.auth import login_required, can_delete

tecnicos_bp = Blueprint('tecnicos', __name__)

@tecnicos_bp.route('/api/tecnicos', methods=['GET'])
def listar_tecnicos():
    conn = get_db()
    activo = request.args.get('activo', '1')

    # Manejar diferentes valores de activo
    if activo == 'all':
        tecnicos = conn.execute('SELECT * FROM tecnicos ORDER BY apellidos, nombres').fetchall()
    elif activo == 'true' or activo == '1':
        tecnicos = conn.execute('SELECT * FROM tecnicos WHERE activo = 1 ORDER BY apellidos, nombres').fetchall()
    else:
        tecnicos = conn.execute('SELECT * FROM tecnicos ORDER BY apellidos, nombres').fetchall()

    conn.close()
    return jsonify([dict(t) for t in tecnicos])

@tecnicos_bp.route('/api/tecnicos/<int:id>', methods=['GET'])
def obtener_tecnico(id):
    conn = get_db()
    tecnico = conn.execute('SELECT * FROM tecnicos WHERE id = ?', (id,)).fetchone()
    conn.close()

    if not tecnico:
        return jsonify({'error': 'Técnico no encontrado'}), 404

    return jsonify(dict(tecnico))

@tecnicos_bp.route('/api/tecnicos', methods=['POST'])
def crear_tecnico():
    data = request.json
    if not data or 'nombres' not in data or 'apellidos' not in data:
        return jsonify({'error': 'Nombres y apellidos son requeridos'}), 400

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tecnicos (dni, nombres, apellidos, especialidad, telefono, email, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('dni', ''),
            data['nombres'],
            data['apellidos'],
            data.get('especialidad', ''),
            data.get('telefono', ''),
            data.get('email', ''),
            data.get('activo', 1)
        ))
        conn.commit()
        tecnico_id = cursor.lastrowid
        conn.close()
        return jsonify({'mensaje': 'Técnico creado correctamente', 'id': tecnico_id}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@tecnicos_bp.route('/api/tecnicos/<int:id>', methods=['PUT'])
def actualizar_tecnico(id):
    data = request.json
    if not data:
        return jsonify({'error': 'Datos incompletos'}), 400

    conn = get_db()
    try:
        conn.execute('''
            UPDATE tecnicos
            SET dni=?, nombres=?, apellidos=?, especialidad=?, telefono=?, email=?, activo=?
            WHERE id=?
        ''', (
            data.get('dni', ''),
            data.get('nombres', ''),
            data.get('apellidos', ''),
            data.get('especialidad', ''),
            data.get('telefono', ''),
            data.get('email', ''),
            data.get('activo', 1),
            id
        ))
        conn.commit()
        conn.close()
        return jsonify({'mensaje': 'Técnico actualizado correctamente'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@tecnicos_bp.route('/api/tecnicos/<int:id>', methods=['DELETE'])
@login_required
@can_delete
def eliminar_tecnico(id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM tecnicos WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'mensaje': 'Técnico eliminado correctamente'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@tecnicos_bp.route('/api/tecnicos/stats', methods=['GET'])
def stats_tecnicos():
    conn = get_db()

    # Órdenes por técnico
    ordenes_por_tecnico = conn.execute('''
        SELECT tecnico, COUNT(*) as total
        FROM ordenes
        WHERE tecnico IS NOT NULL AND tecnico != ''
        GROUP BY tecnico
        ORDER BY total DESC
    ''').fetchall()

    # Técnicos disponibles
    tecnicos_activos = conn.execute('SELECT COUNT(*) FROM tecnicos WHERE activo = 1').fetchone()[0]

    conn.close()

    return jsonify({
        'ordenes_por_tecnico': [dict(t) for t in ordenes_por_tecnico],
        'tecnicos_activos': tecnicos_activos
    })