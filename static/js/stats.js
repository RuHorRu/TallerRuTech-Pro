// static/js/stats.js

function loadStats() {
    fetch('/api/stats')
        .then(response => {
            if (!response.ok) throw new Error('Error en la red');
            return response.json();
        })
        .then(data => {
            // Vinculamos cada dato con su ID correspondiente en el HTML
            // Usamos || 0 como "plan B" por si el dato llega vacío
            const statsMap = {
                'stat-total': data.total,
                'stat-revision': data.revision,
                'stat-repuesto': data.repuesto,
                'stat-listos': data.listos,
                'stat-entregados': data.entregados
            };

            for (const [id, value] of Object.entries(statsMap)) {
                const element = document.getElementById(id);
                if (element) {
                    element.innerText = value !== undefined ? value : 0;
                }
            }
        })
        .catch(error => {
            console.error('Error al cargar estadísticas:', error);
        });
}

// Cargar estadísticas al iniciar y cada 30 segundos para mantenerlo actualizado
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    setInterval(loadStats, 30000); 
});