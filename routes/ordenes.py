import time

from flask import Blueprint, jsonify, request, send_file

from database.db import get_db

ordenes_bp = Blueprint('ordenes', __name__)


def _dict(row):
    return dict(row) if row else None


def _insert_one(conn, table, orden_id, data):
    if not data:
        return
    cols = [c for c in data.keys() if c != 'id']
    if not cols:
        return
    fields = ['orden_id'] + cols
    values = [orden_id] + [data.get(c) for c in cols]
    marks = ','.join(['?'] * len(fields))
    conn.execute(
        f"INSERT INTO {table} ({','.join(fields)}) VALUES ({marks})",
        values
    )


def _replace_one(conn, table, orden_id, data):
    conn.execute(f'DELETE FROM {table} WHERE orden_id = ?', (orden_id,))
    _insert_one(conn, table, orden_id, data or {})


def _replace_many(conn, table, orden_id, rows, num_field):
    conn.execute(f'DELETE FROM {table} WHERE orden_id = ?', (orden_id,))
    for index, row in enumerate(rows or [], 1):
        clean = {k: v for k, v in row.items() if k != 'id'}
        clean[num_field] = index
        _insert_one(conn, table, orden_id, clean)


def _get_or_create_cliente(conn, data):
    cli = data.get('cliente') or {}
    dni = (cli.get('dni') or '').strip()

    row = conn.execute('SELECT id FROM clientes WHERE dni = ?', (dni,)).fetchone() if dni else None
    if row:
        cliente_id = row['id']
        conn.execute(
            """
            UPDATE clientes
            SET nombres = ?, apellidos = ?, tel = ?, email = ?, ciudad = ?, dir = ?
            WHERE id = ?
            """,
            (
                cli.get('nombres'),
                cli.get('apellidos'),
                cli.get('tel'),
                cli.get('email'),
                cli.get('ciudad'),
                cli.get('dir'),
                cliente_id
            )
        )
        return cliente_id

    if not dni:
        dni = f'SIN-DNI-{int(time.time() * 1000)}'

    cur = conn.execute(
        """
        INSERT INTO clientes (dni, nombres, apellidos, tel, email, ciudad, dir)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            dni,
            cli.get('nombres') or '',
            cli.get('apellidos') or '',
            cli.get('tel'),
            cli.get('email'),
            cli.get('ciudad'),
            cli.get('dir')
        )
    )
    return cur.lastrowid


def _save_order_details(conn, orden_id, data):
    _replace_one(conn, 'equipo', orden_id, data.get('equipo'))
    _replace_one(conn, 'visual', orden_id, data.get('visual'))
    _replace_one(conn, 'funcional', orden_id, data.get('funcional'))
    _replace_one(conn, 'bateria', orden_id, data.get('bateria'))
    _replace_one(conn, 'termica', orden_id, data.get('termica'))
    _replace_one(conn, 'diagnostico', orden_id, data.get('diagnostico'))
    _replace_one(conn, 'diag_fabricante', orden_id, data.get('diag_fabricante'))
    _replace_one(conn, 'presupuesto', orden_id, data.get('presupuesto'))
    _replace_many(conn, 'ram_modulos', orden_id, data.get('ram'), 'num_modulo')
    _replace_many(conn, 'discos', orden_id, data.get('discos'), 'num_disco')
    _replace_many(conn, 'fallas_identificadas', orden_id, data.get('fallas'), 'num_falla')
    _replace_many(conn, 'presupuesto_items', orden_id, data.get('presupuesto_items'), 'num_item')


def obtener_datos_completos(oid):
    conn = get_db()
    try:
        base = conn.execute(
            """
            SELECT o.*, c.nombres, c.apellidos, c.dni, c.tel, c.email, c.ciudad, c.dir
            FROM ordenes o
            JOIN clientes c ON o.cliente_id = c.id
            WHERE o.id = ?
            """,
            (oid,)
        ).fetchone()
        if not base:
            return None

        data = dict(base)
        for table in ('equipo', 'visual', 'funcional', 'bateria', 'termica', 'diagnostico',
                      'diag_fabricante', 'presupuesto'):
            data[table] = _dict(conn.execute(f'SELECT * FROM {table} WHERE orden_id = ?', (oid,)).fetchone()) or {}

        data['ram'] = [dict(r) for r in conn.execute('SELECT * FROM ram_modulos WHERE orden_id = ? ORDER BY num_modulo', (oid,))]
        data['discos'] = [dict(r) for r in conn.execute('SELECT * FROM discos WHERE orden_id = ? ORDER BY num_disco', (oid,))]
        data['fallas'] = [dict(r) for r in conn.execute('SELECT * FROM fallas_identificadas WHERE orden_id = ? ORDER BY num_falla', (oid,))]
        data['presupuesto_items'] = [dict(r) for r in conn.execute('SELECT * FROM presupuesto_items WHERE orden_id = ? ORDER BY num_item', (oid,))]
        data['imagenes'] = [dict(r) for r in conn.execute('SELECT * FROM imagenes WHERE orden_id = ? ORDER BY id', (oid,))]

        eq = data.get('equipo') or {}
        data.update({k: v for k, v in eq.items() if k not in ('id', 'orden_id')})

        return data
    finally:
        conn.close()


@ordenes_bp.route('/api/ordenes', methods=['GET'])
def api_ordenes():
    q = (request.args.get('q') or '').strip()
    estado = (request.args.get('estado') or '').strip()
    anio = (request.args.get('anio') or '').strip()
    mes = (request.args.get('mes') or '').strip()
    dia = (request.args.get('dia') or '').strip()
    page = request.args.get('page', type=int)
    limit = request.args.get('limit', type=int)

    where = []
    params = []

    if q:
        like = f'%{q}%'
        where.append("""(
            o.num LIKE ? OR c.dni LIKE ? OR c.nombres LIKE ? OR c.apellidos LIKE ?
            OR e.tipo LIKE ? OR e.marca LIKE ? OR e.modelo LIKE ?
        )""")
        params.extend([like] * 7)
    if estado == 'pendientes':
        where.append("o.estado NOT IN ('entregado', 'cancelado')")
    elif estado:
        where.append('o.estado = ?')
        params.append(estado)
    if dia:
        where.append('date(o.fecha_rec) = date(?)')
        params.append(dia)
    elif anio and mes:
        where.append("strftime('%Y', o.fecha_rec) = ? AND strftime('%m', o.fecha_rec) = ?")
        params.extend([anio, str(int(mes)).zfill(2)])
    elif anio:
        where.append("strftime('%Y', o.fecha_rec) = ?")
        params.append(anio)

    base_sql = """
        SELECT o.*, c.nombres, c.apellidos, c.dni, c.tel, c.email,
               e.tipo, e.marca, e.modelo
        FROM ordenes o
        JOIN clientes c ON o.cliente_id = c.id
        LEFT JOIN equipo e ON o.id = e.orden_id
    """
    count_sql = """
        SELECT COUNT(*)
        FROM ordenes o
        JOIN clientes c ON o.cliente_id = c.id
        LEFT JOIN equipo e ON o.id = e.orden_id
    """
    if where:
        clause = ' WHERE ' + ' AND '.join(where)
        base_sql += clause
        count_sql += clause
    base_sql += ' ORDER BY o.id DESC'

    conn = get_db()
    if page and limit:
        page = max(page, 1)
        limit = min(max(limit, 1), 100)
        total = conn.execute(count_sql, params).fetchone()[0]
        status_sql = """
            SELECT o.estado, COUNT(*) AS total
            FROM ordenes o
            JOIN clientes c ON o.cliente_id = c.id
            LEFT JOIN equipo e ON o.id = e.orden_id
        """
        if where:
            status_sql += ' WHERE ' + ' AND '.join(where)
        status_sql += ' GROUP BY o.estado'
        counts = {r['estado']: r['total'] for r in conn.execute(status_sql, params).fetchall()}
        rows = conn.execute(base_sql + ' LIMIT ? OFFSET ?', params + [limit, (page - 1) * limit]).fetchall()
        conn.close()
        pages = (total + limit - 1) // limit if total else 1
        return jsonify({
            'items': [dict(r) for r in rows],
            'total': total,
            'page': page,
            'limit': limit,
            'pages': pages,
            'counts': counts
        })

    rows = conn.execute(base_sql, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@ordenes_bp.route('/api/ordenes/pendientes')
def api_pendientes():
    limit = min(max(request.args.get('limit', default=7, type=int), 1), 50)
    conn = get_db()
    total = conn.execute(
        "SELECT COUNT(*) FROM ordenes WHERE estado NOT IN ('entregado', 'cancelado')"
    ).fetchone()[0]
    rows = conn.execute(
        """
        SELECT o.*, c.nombres, c.apellidos, c.dni, c.tel, c.email,
               e.tipo, e.marca, e.modelo
        FROM ordenes o
        JOIN clientes c ON o.cliente_id = c.id
        LEFT JOIN equipo e ON o.id = e.orden_id
        WHERE o.estado NOT IN ('entregado', 'cancelado')
        ORDER BY o.id DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()
    conn.close()
    return jsonify({'items': [dict(r) for r in rows], 'total': total, 'limit': limit})


@ordenes_bp.route('/api/ordenes/<int:oid>', methods=['GET'])
def get_orden(oid):
    data = obtener_datos_completos(oid)
    if not data:
        return jsonify({'ok': False, 'error': 'Orden no encontrada'}), 404
    return jsonify(data)


@ordenes_bp.route('/api/ordenes', methods=['POST'])
def create_orden():
    data = request.get_json() or {}
    conn = get_db()
    try:
        cliente_id = _get_or_create_cliente(conn, data)

        cur = conn.execute(
            """
            INSERT INTO ordenes (num, cliente_id, fecha_rec, fecha_ent, tecnico, prioridad, estado, precio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                'TEMP',
                cliente_id,
                data.get('fecha_rec'),
                data.get('fecha_ent'),
                data.get('tecnico'),
                data.get('prioridad') or 'Normal',
                data.get('estado') or 'revision',
                data.get('precio')
            )
        )
        oid = cur.lastrowid
        
        num = f"OT-{oid:04d}"   # → OT-0001, OT-0042, OT-0150 ...
        conn.execute("UPDATE ordenes SET num = ? WHERE id = ?", (num, oid))

        _save_order_details(conn, oid, data)
        conn.commit()
        return jsonify({'ok': True, 'id': oid, 'num': num, 'message': f'Orden {num} guardada con éxito'})
    except Exception as exc:
        conn.rollback()
        return jsonify({'ok': False, 'error': str(exc), 'message': str(exc)}), 400
    finally:
        conn.close()


@ordenes_bp.route('/api/ordenes/<int:oid>', methods=['PUT'])
def update_orden(oid):
    data = request.get_json() or {}
    conn = get_db()
    try:
        cliente_id = _get_or_create_cliente(conn, data)
        conn.execute(
            """
            UPDATE ordenes
            SET cliente_id = ?, fecha_rec = ?, fecha_ent = ?, tecnico = ?, prioridad = ?,
                estado = ?, precio = ?, actualizado = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                cliente_id,
                data.get('fecha_rec'),
                data.get('fecha_ent'),
                data.get('tecnico'),
                data.get('prioridad') or 'Normal',
                data.get('estado') or 'revision',
                data.get('precio'),
                oid
            )
        )
        _save_order_details(conn, oid, data)
        conn.commit()
        return jsonify({'ok': True, 'id': oid, 'message': 'Orden actualizada'})
    except Exception as exc:
        conn.rollback()
        return jsonify({'ok': False, 'error': str(exc), 'message': str(exc)}), 400
    finally:
        conn.close()


@ordenes_bp.route('/api/ordenes/<int:oid>', methods=['DELETE'])
def delete_orden(oid):
    conn = get_db()
    conn.execute('DELETE FROM ordenes WHERE id = ?', (oid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@ordenes_bp.route('/api/ordenes/<int:oid>/estado', methods=['PATCH'])
def update_estado(oid):
    data = request.get_json() or {}
    conn = get_db()
    conn.execute(
        'UPDATE ordenes SET estado = ?, actualizado = CURRENT_TIMESTAMP WHERE id = ?',
        (data.get('estado') or 'revision', oid)
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@ordenes_bp.route('/api/anios')
def api_anios():
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT strftime('%Y', fecha_rec) AS anio FROM ordenes WHERE fecha_rec IS NOT NULL ORDER BY anio DESC"
    ).fetchall()
    conn.close()
    return jsonify([r['anio'] for r in rows if r['anio']])


@ordenes_bp.route('/api/pdf/<int:oid>/cliente')
def pdf_cliente(oid):
    from app import build_pdf_cliente

    data = obtener_datos_completos(oid)
    if not data:
        return jsonify({'ok': False, 'error': 'Orden no encontrada'}), 404
    apellido = (data.get('apellidos') or 'cliente').replace(' ', '_')
    return send_file(build_pdf_cliente(data), mimetype='application/pdf', download_name=f"Orden_{data['num']}_{apellido}_cliente.pdf")


@ordenes_bp.route('/api/pdf/<int:oid>/tecnico')
def pdf_tecnico(oid):
    from app import build_pdf_tecnico

    data = obtener_datos_completos(oid)
    if not data:
        return jsonify({'ok': False, 'error': 'Orden no encontrada'}), 404
    apellido = (data.get('apellidos') or 'cliente').replace(' ', '_')
    return send_file(build_pdf_tecnico(data), mimetype='application/pdf', download_name=f"Informe_{data['num']}_{apellido}_tecnico.pdf")


@ordenes_bp.route('/api/orden/<int:id>/ticket', methods=['GET'])
def get_ticket_data(id):
    from database import db
    conn = get_db()
    c = conn.cursor()
    
    # Obtener datos de la orden y del cliente
    c.execute('''
        SELECT o.*, c.nombre as cliente_nombre, c.telefono as cliente_telefono
        FROM ordenes o
        JOIN clientes c ON o.cliente_id = c.id
        WHERE o.id = ?
    ''', (id,))
    orden = c.fetchone()
    conn.close()
    
    if not orden:
        return jsonify({'error': 'Orden no encontrada'}), 404
        
    config = db.obtener_configuracion_taller()
    
    return jsonify({
        'taller': config,
        'orden': {
            'id': orden['id'],
            'fecha': orden['fecha_ingreso'],
            'cliente': orden['cliente_nombre'],
            'telefono': orden['cliente_telefono'],
            'equipo': f"{orden['tipo_equipo']} {orden['marca']} {orden['modelo']}",
            'serie': orden['numero_serie'] or 'N/A',
            'falla': orden['descripcion_falla']
        }
    })