async function loadClientes(){

    const search = document.getElementById('search-cli').value
async function loadClientes(){

    const search = document.getElementById('search-cli').value

    const clientes = await api(`/api/clientes?q=${search}`)

    console.log(clientes)
}
    const clientes = await api(`/api/clientes?q=${search}`)

    console.log(clientes)
}