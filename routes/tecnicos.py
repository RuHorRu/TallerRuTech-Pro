from flask import Blueprint, request, jsonify
from database.db import get_db

tecnicos_bp = Blueprint('tecnicos', __name__)

@tecnicos_bp.route('/api/tecnicos', methods=['GET'])
def listar_tecnicos():
    conn = get_db()
    activo = request.args.get('activo', '1')
    if activo == 'all':
        tecnicos = conn.execute('SELECT * FROM tecnicos ORDER BY nombre').fetchall()
    else:
        tecnicos = conn.execute('SELECT * FROM tecnicos WHERE activo = ? ORDER BY nombre', (activo,)).fetchall()
    conn.close()
    return jsonify([dict(t) for t in tecnicos])

@tecnicos_bp.route('/api/tecnicos', methods=['POST'])
def crear_tecnico():
    data = request.json
    if not data or 'nombre' not in data:
        return jsonify({'error': 'El nombre es requerido'}), 400

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tecnicos (nombre, email, telefono, especialidad, activo)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['nombre'],
            data.get('email', ''),
            data.get('telefono', ''),
            data.get('especialidad', ''),
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
            SET nombre=?, email=?, telefono=?, especialidad=?, activo=?
            WHERE id=?
        ''', (
            data.get('nombre', ''),
            data.get('email', ''),
            data.get('telefono', ''),
            data.get('especialidad', ''),
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