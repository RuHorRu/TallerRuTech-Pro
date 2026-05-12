function toast(message){

    const div = document.createElement('div')

    div.className = 'toast'
    div.innerText = message

    document.body.appendChild(div)

    setTimeout(()=>{
        div.remove()
    },3000)
}