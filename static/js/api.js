async function api(url, method='GET', data=null){

    const options = {
        method,
        headers:{
            'Content-Type':'application/json'
        }
    }

    if(data){
        options.body = JSON.stringify(data)
    }

    const response = await fetch(url, options)

    return await response.json()
}