from flask import Blueprint, request, jsonify
from database.db import get_db

clientes_bp = Blueprint('clientes', __name__)


@clientes_bp.route('/api/clientes')
def api_clientes():
    q = request.args.get('q', '')

    conn = get_db()

    if q:
        rows = conn.execute(
            """
            SELECT * FROM clientes
            WHERE dni LIKE ?
            OR nombres LIKE ?
            OR apellidos LIKE ?
            ORDER BY apellidos
            """,
            [f'%{q}%'] * 3
        ).fetchall()
    else:
        rows = conn.execute(
            'SELECT * FROM clientes ORDER BY apellidos'
        ).fetchall()

    conn.close()

    return jsonify([dict(r) for r in rows])


@clientes_bp.route('/api/clientes', methods=['POST'])
def create_cliente():
    data = request.get_json() or {}

    conn = get_db()

    try:
        conn.execute(
            """
            INSERT INTO clientes(dni, nombres, apellidos, tel, email, ciudad, dir)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                data['dni'],
                data['nombres'],
                data['apellidos'],
                data.get('tel'),
                data.get('email'),
                data.get('ciudad'),
                data.get('dir')
            )
        )
        conn.commit()
        return jsonify({'ok': True})
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 400
    finally:
        conn.close()


@clientes_bp.route('/api/clientes/<int:cliente_id>', methods=['PUT'])
def update_cliente(cliente_id):
    data = request.get_json() or {}
    conn = get_db()

    try:
        conn.execute(
            """
            UPDATE clientes
            SET dni = ?, nombres = ?, apellidos = ?, tel = ?, email = ?, ciudad = ?, dir = ?
            WHERE id = ?
            """,
            (
                data.get('dni'),
                data.get('nombres'),
                data.get('apellidos'),
                data.get('tel'),
                data.get('email'),
                data.get('ciudad'),
                data.get('dir'),
                cliente_id
            )
        )
        conn.commit()
        return jsonify({'ok': True})
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 400
    finally:
        conn.close()


@clientes_bp.route('/api/clientes/<int:cliente_id>', methods=['DELETE'])
def delete_cliente(cliente_id):
    conn = get_db()

    try:
        conn.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
        conn.commit()
        return jsonify({'ok': True})
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 400
    finally:
        conn.close()
