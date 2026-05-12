# 🛠️ TallerRuTech Pro · Sistema de Gestión para Talleres de Reparación

> **Plataforma profesional para el control integral de órdenes de servicio, diagnóstico técnico avanzado y generación automática de reportes PDF.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-07405E?logo=sqlite&logoColor=white)](https://sqlite.org)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF%20Generation-red)](https://www.reportlab.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 📌 Descripción General

**TallerRuTech Pro** es una solución web diseñada para talleres de reparación de equipos informáticos y electrónicos. Permite gestionar clientes, órdenes de trabajo, diagnósticos técnicos detallados (RAM, discos, térmica, batería, fallas), presupuestos multimoneda, adjuntar imágenes y generar dos tipos de informes PDF (cliente y técnico). Todo con una interfaz moderna, responsiva y sin necesidad de contraseñas para los clientes.

El sistema se ejecuta localmente con Flask y SQLite, siendo ideal para uso interno en el taller, con opción de desplegarse en servidor local o en la nube.

---

## ✨ Características Principales

### 🔧 Gestión de Órdenes de Servicio
- **Formulario en 10 pasos**  
  Cliente → Equipo → Visual → Funcional → Batería → RAM → Discos → Térmica → Diagnóstico → Presupuesto
- **Tablas dinámicas**  
  Agrega/elimina módulos de RAM, unidades de almacenamiento, fallas e ítems de presupuesto en tiempo real.
- **Estados del proceso**  
  En revisión, esperando repuesto, listo, entregado, cancelado.
- **Prioridades**  
  Normal, Alta, Urgente.
- **Fechas clave**  
  Recepción y entrega estimada.
- **Asignación de técnico** responsable.

### 👥 Módulo de Clientes
- Registro completo (cédula, nombres, teléfono, correo, dirección, ciudad).
- Búsqueda en vivo por cédula o nombre.
- Autocompletado automático al seleccionar un cliente para una nueva orden.

### 🔍 Diagnóstico Técnico Profesional
- **Inspección visual** (carcasa, pantalla, teclado, puertos, bisagras, cargador).
- **Pruebas funcionales** (encendido, SO, teclado, audio, pantalla, touchpad, WiFi, USB, cámara).
- **Análisis de batería** (herramienta, capacidades, salud, duración, estado).
- **Test de RAM**  
  Tabla con capacidad, tipo DDR, velocidad, número de serie, pases, duración, resultado.
- **Diagnóstico de discos**  
  Marca, tipo, capacidad, serie, SMART, horas, apagados, sectores, rendimiento, lecturas.
- **Análisis térmico**  
  Temperaturas CPU/GPU en reposo/carga, temperatura disco, estado de ventilación.
- **Software de diagnóstico del fabricante** (HP, Dell, etc.).
- **Evaluación final** (estado general, servicio recomendado, trabajos realizados, repuestos, recomendaciones).
- **Tabla de fallas** identificadas con severidad y prioridad.

### 💰 Presupuestos Multimoneda
- Soporte para USD, EUR, COP, PEN, MXN, ARS, BRL.
- Agrega ítems con descripción, tipo (repuesto/mano de obra) y precio.
- Cálculo automático del total.
- Notas adicionales para condiciones del presupuesto.

### 📸 Gestión de Imágenes
- Subida de múltiples imágenes en las secciones:
  - Equipo al ingreso
  - Inspección visual
  - Generales (desde el modal de orden)
- Visualización en las vistas de detalle y en los PDF generados.

### 📄 Generación de PDF Profesionales
- **Orden de recepción para el cliente**  
  Datos del cliente, equipo, diagnóstico resumido, presupuesto, firma del técnico y del cliente.
- **Informe técnico completo (uso interno)**  
  Todos los campos técnicos, tablas de RAM, discos, fallas, resultados de diagnóstico, imágenes y firma.

Ambos PDF se generan con `reportlab` y se descargan directamente o se sirven al cliente.

### 📊 Panel de Control y Estadísticas
- Dashboard con tarjetas resumen:
  - Total órdenes
  - En revisión
  - Esperando repuesto
  - Listos
  - Entregados
- Lista de equipos pendientes (últimas órdenes no entregadas).
- Gráficos de estado (vía el endpoint `/stats`).

### 🔎 Historial y Filtros
- Vista por año, mes o día.
- Filtros por estado y búsqueda textual.
- Paginación en resultados.

### 🌙 Tema Claro/Oscuro
- Botón de cambio de tema que persiste en el navegador.
- Paleta de colores CSS personalizable.

### 🖨️ Modal de Detalle de Orden
- Ver toda la información de una orden en un modal.
- Visualización de imágenes subidas (por sección).
- Posibilidad de subir imágenes adicionales directamente desde el modal.
- Botones para cambiar estado, generar PDF o eliminar (según permisos).

---

## 🧱 Tecnologías Utilizadas

| Tecnología | Propósito |
|------------|-----------|
| **Python 3.10+** | Lenguaje principal |
| **Flask** | Framework web y API REST |
| **SQLite** | Base de datos ligera (archivo `database.db`) |
| **ReportLab** | Generación de PDFs (clientes y técnicos) |
| **HTML5 / CSS3** | Estructura y estilos (sin frameworks externos) |
| **JavaScript (Vanilla)** | Interactividad, tabs dinámicos, tablas, modales |
| **Tabler Icons** | Biblioteca de iconos libres |
| **Waitress** | Servidor WSGI para producción |

---

## 📋 Requisitos Previos

- Python 3.10 o superior
- pip (gestor de paquetes)
- Navegador web moderno (Chrome, Firefox, Edge)

---

## ⚙️ Instalación y Ejecución Local

## 📺 Opción 1 - Obtener el código
Sin Git desde GiHub y descomprir.

    https://github.com/RuHorRu/TallerRuTech-Pro/archive/refs/heads/master.zip

### 1. Clonar el repositorio (opción para desarrolladores)
```bash
git clone https://github.com/RuHorRu/TallerRuTech-Pro
cd taller-ru-tech-pro
```

### 2. Crear y activar un entorno virtual (opcional pero recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

Si no existe `requirements.txt`, instala manualmente:
```bash
pip install flask waitress reportlab
```

### 4. Inicializar la base de datos
El sistema crea automáticamente la base de datos y las tablas al ejecutarse por primera vez (gracias a `init_db()`).

### 5. Ejecutar la aplicación
```bash
python app.py
```

El servidor se iniciará en `http://localhost:5000` y automáticamente abrirá una pestaña del navegador.

> **Nota**: Por defecto el host es `0.0.0.0` y el puerto `5000`. Puedes modificar `APP_HOST` y `APP_PORT` en `app.py`.

### 6. Uso
- Accede a la interfaz web.
- Comienza registrando clientes (pestaña **Clientes**).
- Crea una nueva orden (pestaña **Nueva Orden**) siguiendo los 10 pasos.
- Administra las órdenes desde **Órdenes** e **Historial**.
- Visualiza y descarga PDFs desde el modal de cada orden.

---

## 📁 Estructura del Proyecto

```
taller-ru-tech-pro/
├── app.py                  # Aplicación principal y rutas globales
├── database/
│   ├── init_db.py          # Creación de tablas SQLite
│   └── db.py               # Conexión y consultas (si existe)
├── routes/
│   ├── clientes.py         # API de clientes (CRUD, búsqueda)
│   ├── ordenes.py          # API de órdenes (guardar, listar, cambiar estado, eliminar)
│   ├── stats.py            # Estadísticas para dashboard
│   └── uploads.py          # Subida de imágenes (multipart)
├── templates/
│   └── index.html          # Interfaz única (SPA)
├── static/
│   ├── css/
│   │   └── main.css        # Estilos personalizados
│   └── js/
│       ├── app.js          # Lógica principal del frontend
│       └── stats.js        # Carga de estadísticas
├── imagenes/               # Carpeta donde se almacenan las imágenes subidas
├── database.db             # Archivo SQLite (se crea automáticamente)
└── README.md               # Este archivo
```

> **Nota**: La generación de PDFs utiliza funciones internas en `app.py` (`build_pdf_cliente`, `build_pdf_tecnico`).

---

## 🐳 Despliegue con Docker (Opcional)

Si deseas contenerizar la aplicación, puedes usar el siguiente `Dockerfile` de ejemplo:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

Construir y ejecutar:
```bash
docker build -t taller-ru-tech .
docker run -d -p 5000:5000 --name taller taller-ru-tech
```

---

## 🔒 Seguridad y Notas

- **No hay autenticación de usuarios** en esta versión básica. Es ideal para uso en red local o con control de acceso por firewall.
- Las contraseñas no son necesarias: el sistema está pensado para ser usado internamente por el personal del taller.
- Las imágenes se guardan en la carpeta `imagenes/` y se sirven estáticamente.
- La base de datos SQLite puede ser respaldada copiando el archivo `database.db`.

---

## 🎯 Personalización

Puedes modificar:
- **Colores y estilos** en `static/css/main.css`.
- **Iconos** cambiando las clases de Tabler Icons.
- **Monedas permitidas** en el paso de presupuesto (`select id="f-presupuesto-moneda"`).
- **PDFs** ajustando las funciones `build_pdf_*` en `app.py`.

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Haz un fork del proyecto.
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza commits descriptivos.
4. Envía un pull request.

---

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

## 📧 Contacto y Soporte

Desarrollado por **RuHor Ru Software Solutions**  
- Youtube: [RuHorRu](https://www.youtube.com/@ruhor)
- Correo: correocity@outlook.com  
- Telegram: [@RuHorRuSoftwareSolutions](https://www.facebook.com/ruhorec)

---

⭐ **Si este proyecto te ha sido útil, no olvides darle una estrella en GitHub.**