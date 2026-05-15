import io
import os
import threading
import time
import webbrowser
from database import db
from datetime import datetime
from xml.sax.saxutils import escape

from flask import Flask, render_template, send_from_directory, request, jsonify
from waitress import serve

from database.init_db import init_db
from routes.clientes import clientes_bp
from routes.ordenes import ordenes_bp
from routes.stats import stats_bp
from routes.uploads import uploads_bp

APP_HOST = '0.0.0.0'
APP_PORT = 5000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

app.register_blueprint(clientes_bp)
app.register_blueprint(ordenes_bp)
app.register_blueprint(uploads_bp)
app.register_blueprint(stats_bp)


@app.route('/')
def home():
    return render_template('index.html')



@app.route('/imagenes/<path:filename>')
def imagenes(filename):
    return send_from_directory('imagenes', filename)

@app.route('/api/configuracion', methods=['GET', 'POST'])
def gestion_configuracion():
    if request.method == 'GET':
        config = db.obtener_configuracion_taller()
        return jsonify(config if config else {})
    
    if request.method == 'POST':
        data = request.json
        if not data or 'nombre' not in data:
            return jsonify({'error': 'Datos incompletos'}), 400
        
        db.guardar_configuracion_taller(data)
        return jsonify({'mensaje': 'Configuración guardada correctamente'})
    


def _txt(value, default='—'):
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def _money(value, moneda='USD'):
    try:
        return f'{moneda} {float(value):.2f}'
    except (TypeError, ValueError):
        return f'{moneda} 0.00'


def _styles():
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle('TitlePDF', parent=base['Title'], fontName='Helvetica-Bold',
                                fontSize=16, leading=20, textColor=colors.HexColor('#1f2937'),
                                alignment=1, spaceAfter=2),
        'subtitle': ParagraphStyle('SubtitlePDF', parent=base['Normal'], fontSize=10, leading=13,
                                   textColor=colors.HexColor('#475569'), alignment=1,
                                   spaceAfter=8),
        'section': ParagraphStyle('SectionPDF', parent=base['Heading2'], fontName='Helvetica-Bold',
                                  fontSize=10.5, leading=13, textColor=colors.HexColor('#0f3d5f'),
                                  spaceBefore=10, spaceAfter=5),
        'body': ParagraphStyle('BodyPDF', parent=base['BodyText'], fontSize=8.5, leading=11,
                               textColor=colors.HexColor('#111827')),
        'small': ParagraphStyle('SmallPDF', parent=base['BodyText'], fontSize=7.5, leading=9,
                                textColor=colors.HexColor('#475569')),
        'label': ParagraphStyle('LabelPDF', parent=base['BodyText'], fontSize=7.2, leading=9,
                                textColor=colors.HexColor('#6b7280'), spaceAfter=1),
        'value': ParagraphStyle('ValuePDF', parent=base['BodyText'], fontName='Helvetica-Bold',
                                fontSize=8.6, leading=11, textColor=colors.black),
        'white_title': ParagraphStyle('WhiteTitlePDF', parent=base['BodyText'], fontName='Helvetica-Bold',
                                      fontSize=15, leading=17, textColor=colors.white),
        'white_small': ParagraphStyle('WhiteSmallPDF', parent=base['BodyText'], fontSize=7.5,
                                      leading=9, textColor=colors.white),
        'table_head': ParagraphStyle('TableHeadPDF', parent=base['BodyText'], fontName='Helvetica-Bold',
                                     fontSize=7.6, leading=9, textColor=colors.white),
        'status': ParagraphStyle('StatusPDF', parent=base['BodyText'], fontName='Helvetica-Bold',
                                 fontSize=9.5, leading=12, textColor=colors.HexColor('#7a3e00')),
    }


def _p(value, style):
    from reportlab.platypus import Paragraph

    return Paragraph(escape(_txt(value)), style)


def _section(story, num, title, styles):
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle

    table = Table([[Paragraph(f'{num}. {title}', styles['section'])]], colWidths=[492], hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e3f0fb')),
        ('LINEBEFORE', (0, 0), (0, -1), 2, colors.HexColor('#1f66ad')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(table)


def _doc():
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=36, bottomMargin=34)
    return buf, doc


def _header(story, title, subtitle, data, styles):
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    left = [
        Paragraph(escape(title), styles['white_title']),
        Paragraph(escape(subtitle), styles['white_small']),
    ]
    right = [
        Paragraph(f"<b>{escape(_txt(data.get('num')))}</b>", styles['white_title']),
        Paragraph(f"Recepción: {escape(_txt(data.get('fecha_rec')))}", styles['white_small']),
    ]
    table = Table([[left, right]], colWidths=[360, 132], hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1f66ad')),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 11))


def _kv_table(rows, styles, widths=(132, 360)):
    from reportlab.platypus import Paragraph
    from reportlab.platypus import Table, TableStyle

    def field(label, value):
        return [
            Paragraph(escape(_txt(label, '')), styles['label']),
            Paragraph(escape(_txt(value)), styles['value']),
        ]

    grouped = []
    for i in range(0, len(rows), 2):
        left = field(rows[i][0], rows[i][1])
        right = field(rows[i + 1][0], rows[i + 1][1]) if i + 1 < len(rows) else ''
        grouped.append([left, right])
    table = Table(grouped, colWidths=[246, 246], hAlign='LEFT')
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def _table(headers, rows, styles, widths):
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph
    from reportlab.platypus import Table, TableStyle

    def cell(value):
        return Paragraph(escape('' if value is None else str(value)), styles['small'])

    data = [[Paragraph(escape('' if h is None else str(h)), styles['table_head']) for h in headers]]
    data.extend([[cell(c) for c in row] for row in rows])
    table = Table(data, colWidths=widths, hAlign='LEFT', repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3d5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return table


def _budget(story, data, styles, num='4'):
    from reportlab.platypus import Spacer

    items = data.get('presupuesto_items') or []
    presupuesto = data.get('presupuesto') or {}
    moneda = presupuesto.get('moneda') or 'USD'
    _section(story, num, f'DETALLE DEL PRESUPUESTO ({moneda})', styles)
    if items:
        rows = [[i.get('descripcion'), i.get('tipo'), _money(i.get('precio'), moneda)] for i in items]
        total = sum(float(i.get('precio') or 0) for i in items)
        rows.append(['TOTAL', '', _money(total, moneda)])
        story.append(_table(['Descripción', 'Tipo', f'Precio ({moneda})'], rows, styles, [260, 110, 120]))
    else:
        story.append(_kv_table([('Costo del servicio:', _money(data.get('precio') or 0, moneda))], styles))
    if presupuesto.get('notas'):
        story.append(Spacer(1, 4))
        story.append(_p(f"Notas: {presupuesto.get('notas')}", styles['small']))


def _images(story, data, styles, title='FOTOGRAFÍAS DEL EQUIPO', section=None, max_images=4):
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image, Paragraph, Spacer, Table

    imgs = data.get('imagenes') or []
    if section:
        imgs = [img for img in imgs if img.get('seccion') == section]

    story.append(Paragraph(title, styles['section']))
    if not imgs:
        story.append(_p('Sin fotografías adjuntas.', styles['small']))
        return

    cells = []
    for img in imgs[:max_images]:
        path = os.path.join(BASE_DIR, 'imagenes', img.get('ruta') or '')
        if not os.path.exists(path):
            continue
        try:
            w, h = ImageReader(path).getSize()
            scale = min(230 / w, 155 / h)
            cells.append([Image(path, width=w * scale, height=h * scale),
                          _p(img.get('descripcion') or img.get('seccion') or '', styles['small'])])
        except Exception:
            continue

    if not cells:
        story.append(_p('No se pudieron cargar las fotografías adjuntas.', styles['small']))
        return

    rows = []
    for i in range(0, len(cells), 2):
        rows.append(cells[i:i + 2] + [''] * (2 - len(cells[i:i + 2])))
    story.append(Table(rows, colWidths=[245, 245], hAlign='LEFT'))
    story.append(Spacer(1, 4))


def _signatures(story, data, styles):
    from reportlab.platypus import Spacer, Table, TableStyle

    cliente = f"{_txt(data.get('nombres'), '')} {_txt(data.get('apellidos'), '')}".strip()
    dni = _txt(data.get('dni'), '')
    tecnico = _txt(data.get('tecnico'), 'Técnico')
    story.append(Spacer(1, 24))
    table = Table([
        ['________________________________', '________________________________'],
        ['Firma del Técnico', 'Firma del Cliente'],
        [tecnico, f'{cliente} CI: {dni}'.strip()],
        ['Taller de Reparación', ''],
    ], colWidths=[245, 245], hAlign='LEFT')
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), '#334155'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(table)
    story.append(Spacer(1, 8))
    story.append(_p(f"Conserve este documento. {_txt(data.get('num'))} | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['small']))


def _inspection_rows(source, labels):
    value_map = {'ok': '✓', 'si': '✓', 'si_actualizado': '✓', 'falla': '✗', 'no': '✗',
                 'pendiente': '✗', 'na': '—'}
    text_map = {'ok': 'OK', 'si': 'OK', 'si_actualizado': 'ACTUALIZADO', 'falla': 'FALLA',
                'no': 'NO', 'pendiente': 'PENDIENTE', 'na': 'N/A'}
    rows = []
    for key, label in labels:
        raw = source.get(key) or 'na'
        rows.append([value_map.get(raw, '—'), label, text_map.get(raw, raw)])
    return rows


def build_pdf_cliente(data):
    from reportlab.platypus import Spacer

    buf, doc = _doc()
    styles = _styles()
    eq = data.get('equipo') or {}
    diag = data.get('diagnostico') or {}
    presupuesto = data.get('presupuesto') or {}
    moneda = presupuesto.get('moneda') or 'USD'
    items = data.get('presupuesto_items') or []
    total = sum(float(i.get('precio') or 0) for i in items) or data.get('precio') or 0
    cliente = f"{_txt(data.get('nombres'), '')} {_txt(data.get('apellidos'), '')}".strip()

    story = []
    _header(story, 'ORDEN DE RECEPCIÓN DE EQUIPO', f'Versión Cliente — {_txt(eq.get("tipo"))}', data, styles)
    _section(story, '1', 'DATOS DEL CLIENTE', styles)
    story.append(_kv_table([
        ('Nombre completo:', cliente),
        ('Cédula / DNI:', data.get('dni')),
        ('Teléfono:', data.get('tel')),
        ('Correo electrónico:', data.get('email')),
        ('Ciudad:', data.get('ciudad')),
        ('Dirección:', data.get('dir')),
    ], styles))
    _section(story, '2', 'INFORMACIÓN DEL EQUIPO', styles)
    story.append(_kv_table([
        ('Tipo:', eq.get('tipo')),
        ('Marca / Modelo:', ' '.join(x for x in [eq.get('marca'), eq.get('modelo')] if x)),
        ('N° de Serie:', eq.get('serie')),
        ('Sistema Operativo:', eq.get('so')),
        ('Procesador:', eq.get('procesador')),
        ('RAM total:', eq.get('ram_total')),
        ('Almacenamiento:', eq.get('almacenamiento_total')),
        ('Versión BIOS:', eq.get('version_bios')),
        ('Condición al ingreso:', eq.get('condicion')),
        ('Accesorios entregados:', eq.get('accesorios')),
        ('Falla reportada por el cliente:', eq.get('falla')),
    ], styles))
    _section(story, '3', 'DIAGNÓSTICO Y SERVICIO', styles)
    story.append(_kv_table([
        ('Estado del equipo:', diag.get('estado_general')),
        ('Servicio recomendado:', diag.get('servicio')),
        ('Técnico responsable:', data.get('tecnico')),
        ('Costo del servicio:', _money(total, moneda)),
        ('Fecha recepción:', data.get('fecha_rec')),
        ('Fecha entrega est.:', data.get('fecha_ent')),
        ('Diagnóstico técnico:', diag.get('diagnostico')),
    ], styles))
    _budget(story, data, styles, '4')
    story.append(Spacer(1, 4))
    _images(story, data, styles, 'FOTOGRAFÍAS DEL EQUIPO', max_images=4)
    _signatures(story, data, styles)

    doc.build(story)
    buf.seek(0)
    return buf


def build_pdf_tecnico(data):
    from reportlab.platypus import Spacer

    buf, doc = _doc()
    styles = _styles()
    eq = data.get('equipo') or {}
    visual = data.get('visual') or {}
    funcional = data.get('funcional') or {}
    bateria = data.get('bateria') or {}
    termica = data.get('termica') or {}
    diag = data.get('diagnostico') or {}
    fabricante = data.get('diag_fabricante') or {}
    cliente = f"{_txt(data.get('nombres'), '')} {_txt(data.get('apellidos'), '')}".strip()

    story = []
    _header(story, 'INFORME TÉCNICO DE DIAGNÓSTICO', f'Informe Técnico Completo — Uso Interno — {_txt(eq.get("tipo"))}', data, styles)
    _section(story, '1', 'DATOS DEL EQUIPO Y PROPIETARIO', styles)
    story.append(_kv_table([
        ('Marca / Modelo:', ' — '.join(x for x in [eq.get('marca'), eq.get('modelo')] if x)),
        ('N° de Serie:', eq.get('serie')),
        ('Sistema Operativo:', eq.get('so')),
        ('Tipo de equipo:', eq.get('tipo')),
        ('Procesador:', eq.get('procesador')),
        ('Tarjeta de video:', eq.get('tarjeta_video')),
        ('Otra tarjeta PCIe:', eq.get('tarjeta_pcie')),
        ('RAM total:', eq.get('ram_total')),
        ('Almacenamiento total:', eq.get('almacenamiento_total')),
        ('Versión del BIOS:', eq.get('version_bios')),
        ('Cliente / Propietario:', cliente),
        ('Cédula / DNI:', data.get('dni')),
        ('Teléfono:', data.get('tel')),
        ('Correo electrónico:', data.get('email')),
        ('Ciudad / Dirección:', f"{_txt(data.get('ciudad'), '')} {_txt(data.get('dir'), '')}".strip()),
        ('Técnico Responsable:', data.get('tecnico')),
        ('Fecha Recepción:', data.get('fecha_rec')),
        ('Fecha Entrega Est.:', data.get('fecha_ent')),
        ('Prioridad:', data.get('prioridad')),
        ('Condición al ingreso:', eq.get('condicion')),
        ('Accesorios entregados:', eq.get('accesorios')),
        ('Falla reportada:', eq.get('falla')),
    ], styles))
    _section(story, '2', 'INSPECCIÓN VISUAL', styles)
    story.append(_table(['', 'Elemento', 'Resultado'], _inspection_rows(visual, [
        ('carcasa', 'Carcasa / Chasis'), ('pantalla', 'Pantalla'), ('teclado_vis', 'Teclado (visual)'),
        ('puertos', 'Puertos externos'), ('bisagras', 'Bisagras'), ('cargador_inc', 'Cargador incluido'),
    ]), styles, [28, 285, 175]))
    story.append(Spacer(1, 4))
    story.append(_kv_table([('Estado cargador:', visual.get('cargador_est')),
                            ('Voltaje medido:', visual.get('voltaje')),
                            ('Observaciones:', visual.get('obs'))], styles))
    _section(story, '3', 'PRUEBAS FUNCIONALES', styles)
    story.append(_table(['', 'Prueba', 'Resultado'], _inspection_rows(funcional, [
        ('enc_bat', 'Encendido con batería'), ('enc_car', 'Encendido con cargador'),
        ('carga_so', 'Carga del sistema operativo'), ('teclado', 'Teclado (funcional)'),
        ('audio', 'Audio'), ('display', 'Pantalla / Display'), ('touchpad', 'Touchpad / Mouse'),
        ('wifi', 'Wi-Fi / Red'), ('usb', 'USB / Puertos'), ('camara', 'Cámara'),
    ]), styles, [28, 285, 175]))
    if funcional.get('obs'):
        story.append(Spacer(1, 4))
        story.append(_p(f"Obs: {funcional.get('obs')}", styles['small']))
    _section(story, '4', 'DIAGNÓSTICO DE BATERÍA', styles)
    story.append(_kv_table([
        ('Herramienta usada:', bateria.get('tool')), ('Estado de carga:', bateria.get('estado')),
        ('Capacidad diseño:', bateria.get('disenio')), ('Capacidad actual:', bateria.get('actual')),
        ('Salud de batería:', bateria.get('salud')), ('Duración real:', bateria.get('duracion')),
        ('Serie:', bateria.get('serie')), ('Observaciones:', bateria.get('obs')),
    ], styles))

    ram = data.get('ram') or []
    _section(story, '5', f'TEST DE RAM — {len(ram)} MÓDULO(S)', styles)
    if ram:
        story.append(_table(['#', 'Capacidad/Tipo', 'Velocidad', 'Pases/Duración', 'Resultado'], [
            [f'#{i + 1}', f"{_txt(r.get('capacidad'), '')} {_txt(r.get('tipo_ram'), '')}".strip(),
             r.get('velocidad'), f"{_txt(r.get('pases'), '')} p / {_txt(r.get('duracion_test'), '')}".strip(),
             r.get('resultado')]
            for i, r in enumerate(ram)
        ], styles, [28, 140, 80, 140, 100]))
    else:
        story.append(_p('Sin módulos registrados.', styles['small']))

    discos = data.get('discos') or []
    _section(story, '6', f'ALMACENAMIENTO — {len(discos)} UNIDAD(ES)', styles)
    if discos:
        story.append(_table(['#', 'Marca/Tipo', 'Cap.', 'S.M.A.R.T.', 'Horas', 'Sect.', 'Rend.', 'Lect.Máx', 'Lect.Med', 'Lect.Bja'], [
            [i + 1, f"{_txt(d.get('marca'), '')}/{_txt(d.get('tipo'), '')}".strip('/'), d.get('capacidad'),
             d.get('smart'), d.get('horas'), d.get('sectores'), d.get('rendimiento'), d.get('lectura_max'),
             d.get('lectura_media'), d.get('lectura_baja')]
            for i, d in enumerate(discos)
        ], styles, [22, 82, 48, 58, 45, 38, 48, 58, 58, 58]))
    else:
        story.append(_p('Sin unidades registradas.', styles['small']))

    _section(story, '7', 'ANÁLISIS TÉRMICO', styles)
    story.append(_kv_table([
        ('CPU reposo:', termica.get('cpu_rep')), ('CPU carga:', termica.get('cpu_carga')),
        ('GPU reposo:', termica.get('gpu_rep')), ('GPU carga:', termica.get('gpu_carga')),
        ('Disco:', termica.get('disco')), ('Ventilación:', termica.get('ventilacion')),
        ('Observaciones:', termica.get('obs')),
    ], styles))
    _section(story, '8', 'EVALUACIÓN FINAL Y DIAGNÓSTICO', styles)
    story.append(_p(f"ESTADO GENERAL: {_txt(diag.get('estado_general')).upper()}", styles['status']))
    story.append(_kv_table([
        ('Servicio recomendado:', diag.get('servicio')), ('Actualización de BIOS:', diag.get('bios_estado')),
        ('Diagnóstico técnico:', diag.get('diagnostico')), ('Trabajos realizados:', diag.get('trabajos')),
        ('Repuestos necesarios:', diag.get('repuestos')), ('Recomendaciones al cliente:', diag.get('obs')),
    ], styles))
    _section(story, '8A', 'SOFTWARE DE DIAGNÓSTICO DEL FABRICANTE', styles)
    story.append(_kv_table([
        ('Software utilizado:', fabricante.get('software')), ('Resultado general:', fabricante.get('resultado')),
        ('Observaciones del diagnóstico:', fabricante.get('obs')),
    ], styles))
    fallas = data.get('fallas') or []
    _section(story, '8B', 'TABLA DE FALLAS IDENTIFICADAS', styles)
    if fallas:
        story.append(_table(['#', 'Falla identificada', 'Componente', 'Severidad', 'Prioridad'], [
            [i + 1, f.get('falla'), f.get('componente'), f.get('severidad'), f.get('prioridad')]
            for i, f in enumerate(fallas)
        ], styles, [28, 200, 110, 75, 80]))
    else:
        story.append(_p('Sin fallas adicionales registradas.', styles['small']))
    _budget(story, data, styles, '9')
    _images(story, data, styles, 'FOTOGRAFÍAS DEL EQUIPO', 'equipo', max_images=4)
    _images(story, data, styles, 'IMÁGENES DE INSPECCIÓN VISUAL', 'visual', max_images=4)
    _signatures(story, data, styles)

    doc.build(story)
    buf.seek(0)
    return buf


def open_browser():
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{APP_PORT}')


if __name__ == '__main__':
    init_db()
    threading.Thread(target=open_browser, daemon=True).start()
    print(f'Servidor activo en http://localhost:{APP_PORT}')
    serve(app, host=APP_HOST, port=APP_PORT)
