import os
import time
from pathlib import Path
from flask import Blueprint, jsonify, request
from database.db import BASE_DIR, get_db
from auth.auth import login_required, can_delete

uploads_bp = Blueprint('uploads', __name__)

UPLOAD_DIR = Path(BASE_DIR) / 'imagenes'
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# MIME types permitidos para imágenes
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}


def _safe_name(filename):
    stem = Path(filename).stem[:60] or 'imagen'
    ext = Path(filename).suffix.lower()
    clean = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in stem)
    return f'{int(time.time() * 1000)}_{clean}{ext}'


def _allowed_file(file):
    """Valida que el archivo sea una imagen válida"""
    if not file or not file.filename:
        return False, 'No se recibió archivo'

    # Verificar extensión
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, 'Formato de imagen no permitido'

    # Verificar tamaño
    file.seek(0, 2)  # Ir al final del archivo
    size = file.tell()
    file.seek(0)  # Volver al inicio
    if size > MAX_FILE_SIZE:
        return False, f'El archivo es demasiado grande (máx. {MAX_FILE_SIZE // 1024 // 1024}MB)'

    # Verificar MIME type real leyendo los primeros bytes
    magic_bytes = file.read(12)
    file.seek(0)  # Resetear puntero

    # Detectar tipo por magic bytes
    if magic_bytes.startswith(b'\xff\xd8\xff'):
        mime_type = 'image/jpeg'
    elif magic_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        mime_type = 'image/png'
    elif magic_bytes.startswith(b'GIF87a') or magic_bytes.startswith(b'GIF89a'):
        mime_type = 'image/gif'
    elif magic_bytes.startswith(b'RIFF') and magic_bytes[8:12] == b'WEBP':
        mime_type = 'image/webp'
    else:
        return False, 'El archivo no es una imagen válida'

    if mime_type not in ALLOWED_MIME_TYPES:
        return False, 'Tipo de imagen no permitido'

    return True, None


@uploads_bp.route('/api/upload/<int:orden_id>', methods=['POST'])
def upload_image(orden_id):
    # Verificar que la orden existe
    conn = get_db()
    orden = conn.execute('SELECT id FROM ordenes WHERE id = ?', (orden_id,)).fetchone()
    if not orden:
        conn.close()
        return jsonify({'ok': False, 'error': 'La orden no existe'}), 404
    conn.close()

    file = request.files.get('file')
    valid, error = _allowed_file(file)
    if not valid:
        return jsonify({'ok': False, 'error': error}), 400

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
@login_required
@can_delete
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