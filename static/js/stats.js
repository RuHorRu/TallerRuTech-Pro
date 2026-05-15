// static/js/stats.js


async function loadTecnicosFilter() {
    try {
        const res = await fetch('/api/tecnicos?activo=1');
        const tecnicos = await res.json();

        const select = document.getElementById('filtro-tecnico');
        if (!select) return;

        // Guardar selección actual
        const selectedValue = select.value;

        // Limpiar opciones excepto "Todos"
        select.innerHTML = '<option value="">Todos los técnicos</option>';

        // Agregar técnicos dinámicamente
        tecnicos.forEach(t => {
            const nombreCompleto = `${t.nombres} ${t.apellidos}`;
            select.innerHTML += `<option value="${t.id}">${nombreCompleto}</option>`;
        });

        // Restaurar selección si es válido
        if (selectedValue && tecnicos.some(t => t.id == selectedValue)) {
            select.value = selectedValue;
        }
    } catch (error) {
        console.error('Error cargando filtro de técnicos:', error);
    }
}

function loadDashboardStats() {
    const tecnicoId = document.getElementById('filtro-tecnico')?.value || '';
    const periodo = document.getElementById('filtro-periodo')?.value || 'mes';

    // Construir URL con parámetros
    let url = `/api/stats?periodo=${periodo}`;
    if (tecnicoId) {
        url += `&tecnico_id=${tecnicoId}`;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Error en la red');
            return response.json();
        })
        .then(data => {
            // Actualizar tarjetas de estadísticas
            const statsMap = {
                'stat-total': data.total,
                'stat-revision': data.revision,
                'stat-repuesto': data.espera,
                'stat-listos': data.listo,
                'stat-entregados': data.entregado,
                'stat-tecnicos': data.tecnicos_activos || 0
            };

            for (const [id, value] of Object.entries(statsMap)) {
                const element = document.getElementById(id);
                if (element) {
                    element.innerText = value !== undefined ? value : 0;
                }
            }

            // Actualizar indicadores de productividad
            if (document.getElementById('prod-mes')) {
                document.getElementById('prod-mes').innerText = data.productividad_mes || 0;
            }
            if (document.getElementById('trend-mes')) {
                const trendMes = data.trend_mes || 0;
                const icon = trendMes >= 0 ? 'ti-arrow-up-right' : 'ti-arrow-down-right';
                const color = trendMes >= 0 ? 'var(--green)' : 'var(--red)';
                const sign = trendMes >= 0 ? '+' : '';
                document.getElementById('trend-mes').innerHTML =
                    `<i class="ti ${icon}" style="color: ${color};"></i> <span style="color: ${color};">${sign}${trendMes}%</span> vs mes anterior`;
            }
            if (document.getElementById('prod-anio')) {
                document.getElementById('prod-anio').innerText = data.productividad_anio || 0;
            }
            if (document.getElementById('trend-anio')) {
                const trendAnio = data.trend_anio || 0;
                const icon = trendAnio >= 0 ? 'ti-arrow-up-right' : 'ti-arrow-down-right';
                const color = trendAnio >= 0 ? 'var(--green)' : 'var(--red)';
                const sign = trendAnio >= 0 ? '+' : '';
                document.getElementById('trend-anio').innerHTML =
                    `<i class="ti ${icon}" style="color: ${color};"></i> <span style="color: ${color};">${sign}${trendAnio}%</span> vs año anterior`;
            }

            // Actualizar gráfico de técnicos
            if (data.tecnicos_carga && document.getElementById('chart-tecnicos')) {
                renderTecnicosChart(data.tecnicos_carga);
            }
        })
        .catch(error => {
            console.error('Error al cargar estadísticas:', error);
        });
}

function renderTecnicosChart(tecnicosData) {
    const container = document.getElementById('chart-tecnicos');
    if (!container || !tecnicosData || tecnicosData.length === 0) {
        container.innerHTML = '<div class="empty"><i class="ti ti-chart-bar"></i><p>Sin datos de técnicos</p></div>';
        return;
    }

    // Encontrar el máximo para calcular porcentajes
    const maxOrdenes = Math.max(...tecnicosData.map(t => t.ordenes_activas), 1);

    let html = '';
    tecnicosData.forEach(tecnico => {
        const porcentaje = (tecnico.ordenes_activas / maxOrdenes) * 100;
        const colores = ['var(--blue)', 'var(--green)', 'var(--amber)', 'var(--red)', 'var(--text2)'];
        const color = colores[tecnico.id % colores.length];

        html += `
            <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:120px;font-size:11px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${tecnico.nombre}</div>
                <div style="flex:1;height:24px;background:var(--bg2);border-radius:4px;overflow:hidden;position:relative;">
                    <div style="width:${porcentaje}%;height:100%;background:${color};transition:width 0.3s ease;"></div>
                    <div style="position:absolute;right:6px;top:50%;transform:translateY(-50%);font-size:10px;font-weight:500;color:var(--text);">
                        ${tecnico.ordenes_activas} órdenes
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Cargar estadísticas al iniciar y cada 30 segundos para mantenerlo actualizado
document.addEventListener('DOMContentLoaded', () => {
    loadTecnicosFilter();
    loadDashboardStats();
    setInterval(loadDashboardStats, 30000);
});