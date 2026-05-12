async function loadOrdenes(){

    const ordenes = await api('/api/ordenes')

    console.log(ordenes)
}

function imprimirTicket(id) {
    if (!id) return;
    window.open(`/api/pdf/${id}/cliente`, '_blank');
}

function imprimirInforme(id) {
    if (!id) return;
    window.open(`/api/pdf/${id}/tecnico`, '_blank');
}