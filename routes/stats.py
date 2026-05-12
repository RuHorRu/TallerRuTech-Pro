from flask import Blueprint, jsonify
from database.db import get_db

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/api/stats')
def stats():
    conn = get_db()
    
    total = conn.execute('SELECT COUNT(*) FROM ordenes').fetchone()[0] or 0
    revision = conn.execute("SELECT COUNT(*) FROM ordenes WHERE estado = 'revision'").fetchone()[0] or 0
    espera = conn.execute("SELECT COUNT(*) FROM ordenes WHERE estado = 'espera'").fetchone()[0] or 0
    listo = conn.execute("SELECT COUNT(*) FROM ordenes WHERE estado = 'listo'").fetchone()[0] or 0
    entregado = conn.execute("SELECT COUNT(*) FROM ordenes WHERE estado = 'entregado'").fetchone()[0] or 0
    cancelado = conn.execute("SELECT COUNT(*) FROM ordenes WHERE estado = 'cancelado'").fetchone()[0] or 0

    conn.close()

    return jsonify({
        'total': total,
        'revision': revision,
        'espera': espera,
        'listo': listo,
        'entregado': entregado,
        'cancelado': cancelado
    })
