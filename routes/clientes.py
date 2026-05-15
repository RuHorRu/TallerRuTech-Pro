from flask import Blueprint, request, jsonify
from database.db import get_db

clientes_bp = Blueprint('clientes', __name__)


@clientes_bp.route('/api/clientes')
def api_clientes():
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    conn = get_db()

    # Construir consulta base
    base_query = "SELECT * FROM clientes"
    count_query = "SELECT COUNT(*) as total FROM clientes"

    if q:
        where_clause = " WHERE dni LIKE ? OR nombres LIKE ? OR apellidos LIKE ?"
        params = [f'%{q}%'] * 3
        rows = conn.execute(
            base_query + where_clause + " ORDER BY apellidos LIMIT ? OFFSET ?",
            params + [per_page, (page - 1) * per_page]
        ).fetchall()

        total = conn.execute(
            count_query + where_clause,
            params
        ).fetchone()['total']
    else:
        rows = conn.execute(
            base_query + " ORDER BY apellidos LIMIT ? OFFSET ?",
            [per_page, (page - 1) * per_page]
        ).fetchall()

        total = conn.execute(count_query).fetchone()['total']

    conn.close()

    return jsonify({
        'data': [dict(r) for r in rows],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


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