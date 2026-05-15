// static/js/stats.js

function loadStats() {
    fetch('/api/stats')
        .then(response => {
            if (!response.ok) throw new Error('Error en la red');
            return response.json();
        })
        .then(data => {
            const statsMap = {
                'stat-total': data.total,
                'stat-revision': data.revision,
                'stat-repuesto': data.espera,
                'stat-listos': data.listo,
                'stat-entregados': data.entregado
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