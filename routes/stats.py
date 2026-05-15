from flask import Blueprint, jsonify, request
from database.db import get_db
from datetime import datetime, timedelta

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/api/stats')
def stats():
    conn = get_db()

    # Obtener parámetros de filtro
    periodo = request.args.get('periodo', 'mes')
    tecnico_id = request.args.get('tecnico_id', '')

    # Construir cláusulas WHERE según filtros
    where_clauses = []
    params = []

    if tecnico_id:
        where_clauses.append('tecnico = ?')
        params.append(tecnico_id)

    # Filtro por período (usando fecha_rec en lugar de fecha_ingreso)
    today = datetime.now()
    if periodo == 'mes':
        start_date = today.replace(day=1)
        where_clauses.append("fecha_rec >= ?")
        params.append(start_date.strftime('%Y-%m-%d'))
    elif periodo == 'trimestre':
        start_date = today - timedelta(days=90)
        where_clauses.append("fecha_rec >= ?")
        params.append(start_date.strftime('%Y-%m-%d'))
    elif periodo == 'anio':
        start_date = today.replace(month=1, day=1)
        where_clauses.append("fecha_rec >= ?")
        params.append(start_date.strftime('%Y-%m-%d'))
    # 'todo' no agrega filtro de fecha

    where_sql = ''
    if where_clauses:
        where_sql = 'WHERE ' + ' AND '.join(where_clauses)

    # Consulta base con filtros
    base_query = f'SELECT COUNT(*) FROM ordenes {where_sql}'

    total = conn.execute(base_query, params).fetchone()[0] or 0

    # Estados con filtros
    def count_estado(estado, extra_params=None):
        p = params.copy()
        if extra_params:
            p.extend(extra_params)
        estados_where = f"estado = '{estado}'"
        if where_clauses:
            estados_where += ' AND ' + ' AND '.join([c for i, c in enumerate(where_clauses) if not (len(params) > 0 and 'fecha' in c.lower())])
            # Rebuild properly
            clauses = []
            if tecnico_id:
                clauses.append('tecnico = ?')
            if periodo != 'todo':
                if periodo == 'mes':
                    start_date = today.replace(day=1)
                    clauses.append("fecha_rec >= ?")
                elif periodo == 'trimestre':
                    start_date = today - timedelta(days=90)
                    clauses.append("fecha_rec >= ?")
                elif periodo == 'anio':
                    start_date = today.replace(month=1, day=1)
                    clauses.append("fecha_rec >= ?")
            if clauses:
                estados_where = f"estado = '{estado}' AND " + ' AND '.join(clauses)
        query = f"SELECT COUNT(*) FROM ordenes WHERE {estados_where}"
        return conn.execute(query, p).fetchone()[0] or 0

    revision = count_estado('revision')
    espera = count_estado('espera')
    listo = count_estado('listo')
    entregado = count_estado('entregado')

    # Técnicos activos (con al menos una orden activa)
    tecnicos_activos = conn.execute("""
        SELECT COUNT(DISTINCT tecnico)
        FROM ordenes
        WHERE estado IN ('revision', 'espera', 'listo') AND tecnico IS NOT NULL AND tecnico != ''
    """).fetchone()[0] or 0

    # Productividad mensual (órdenes entregadas este mes) - usando fecha_ent
    mes_start = today.replace(day=1).strftime('%Y-%m-%d')
    productividad_mes = conn.execute(
        "SELECT COUNT(*) FROM ordenes WHERE estado = 'entregado' AND fecha_ent >= ?",
        [mes_start]
    ).fetchone()[0] or 0

    # Trend mensual (comparación con mes anterior)
    mes_anterior_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d')
    mes_anterior_end = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
    productividad_mes_anterior = conn.execute(
        "SELECT COUNT(*) FROM ordenes WHERE estado = 'entregado' AND fecha_ent BETWEEN ? AND ?",
        [mes_anterior_start, mes_anterior_end]
    ).fetchone()[0] or 0

    trend_mes = 0
    if productividad_mes_anterior > 0:
        trend_mes = round(((productividad_mes - productividad_mes_anterior) / productividad_mes_anterior) * 100)
    elif productividad_mes > 0:
        trend_mes = 100

    # Productividad anual
    anio_start = today.replace(month=1, day=1).strftime('%Y-%m-%d')
    productividad_anio = conn.execute(
        "SELECT COUNT(*) FROM ordenes WHERE estado = 'entregado' AND fecha_ent >= ?",
        [anio_start]
    ).fetchone()[0] or 0

    # Trend anual
    anio_anterior_start = today.replace(year=today.year - 1, month=1, day=1).strftime('%Y-%m-%d')
    anio_anterior_end = today.replace(year=today.year - 1, month=12, day=31).strftime('%Y-%m-%d')
    productividad_anio_anterior = conn.execute(
        "SELECT COUNT(*) FROM ordenes WHERE estado = 'entregado' AND fecha_ent BETWEEN ? AND ?",
        [anio_anterior_start, anio_anterior_end]
    ).fetchone()[0] or 0

    trend_anio = 0
    if productividad_anio_anterior > 0:
        trend_anio = round(((productividad_anio - productividad_anio_anterior) / productividad_anio_anterior) * 100)
    elif productividad_anio > 0:
        trend_anio = 100

    # Carga de trabajo por técnico (órdenes activas) - usando tabla tecnica si existe, o nombres
    # Primero verificamos si hay una tabla de técnicos
    try:
        tecnicos_carga = conn.execute("""
            SELECT t.id, t.nombre, COUNT(o.id) as ordenes_activas
            FROM tecnicos t
            LEFT JOIN ordenes o ON t.id = o.tecnico AND o.estado IN ('revision', 'espera', 'listo')
            GROUP BY t.id, t.nombre
            ORDER BY ordenes_activas DESC
        """).fetchall()
    except:
        # Si no hay tabla tecnicos, usamos los nombres directamente de ordenes
        tecnicos_carga = conn.execute("""
            SELECT tecnico, tecnico, COUNT(*) as ordenes_activas
            FROM ordenes
            WHERE estado IN ('revision', 'espera', 'listo') AND tecnico IS NOT NULL AND tecnico != ''
            GROUP BY tecnico
            ORDER BY ordenes_activas DESC
        """).fetchall()

    tecnicos_carga_list = [
        {'id': row[0], 'nombre': row[1] or 'Sin asignar', 'ordenes_activas': row[2]}
        for row in tecnicos_carga
    ]

    conn.close()

    return jsonify({
        'total': total,
        'revision': revision,
        'espera': espera,
        'listo': listo,
        'entregado': entregado,
        'tecnicos_activos': tecnicos_activos,
        'productividad_mes': productividad_mes,
        'trend_mes': trend_mes,
        'productividad_anio': productividad_anio,
        'trend_anio': trend_anio,
        'tecnicos_carga': tecnicos_carga_list
    })