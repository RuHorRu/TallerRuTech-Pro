import os
import time
from pathlib import Path

from flask import Blueprint, jsonify, request

from database.db import BASE_DIR, get_db

uploads_bp = Blueprint('uploads', __name__)

UPLOAD_DIR = Path(BASE_DIR) / 'imagenes'
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def _safe_name(filename):
    stem = Path(filename).stem[:60] or 'imagen'
    ext = Path(filename).suffix.lower()
    clean = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in stem)
    return f'{int(time.time() * 1000)}_{clean}{ext}'


@uploads_bp.route('/api/upload/<int:orden_id>', methods=['POST'])
def upload_image(orden_id):
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'ok': False, 'error': 'No se recibió archivo'}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'ok': False, 'error': 'Formato de imagen no permitido'}), 400

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = _safe_name(file.filename)
    file.save(UPLOAD_DIR / filename)

    conn = get_db()
    cur = conn.execute(
        'INSERT INTO imagenes (orden_id, seccion, ruta, descripcion) VALUES (?, ?, ?, ?)',
        (
            orden_id,
            request.form.get('seccion') or 'equipo',
            filename,
            request.form.get('descripcion') or ''
        )
    )
    conn.commit()
    conn.close()

    return jsonify({'ok': True, 'id': cur.lastrowid, 'ruta': filename})


@uploads_bp.route('/api/imagenes/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    conn = get_db()
    row = conn.execute('SELECT ruta FROM imagenes WHERE id = ?', (image_id,)).fetchone()
    conn.execute('DELETE FROM imagenes WHERE id = ?', (image_id,))
    conn.commit()
    conn.close()

    if row:
        try:
            os.remove(UPLOAD_DIR / row['ruta'])
        except OSError:
            pass

    return jsonify({'ok': True})
