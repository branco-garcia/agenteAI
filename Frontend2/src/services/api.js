const API_BASE = '/api'

export const sendMessage = async (message) => {
    try {
        console.log(`🔍 Frontend: Enviando mensaje: "${message}"`)
        console.log(`🔍 Frontend: URL de destino: ${API_BASE}/preguntar`)
        
        const response = await fetch(`${API_BASE}/preguntar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ pregunta: message })
        })

        console.log(`🔍 Frontend: Response status: ${response.status}`)
        console.log(`🔍 Frontend: Response ok: ${response.ok}`)
        console.log(`🔍 Frontend: Response headers:`, Object.fromEntries(response.headers.entries()))

        if (!response.ok) {
            const errorText = await response.text()
            console.error(`❌ Frontend: Error response: ${errorText}`)
            throw new Error(`HTTP ${response.status}: ${errorText}`)
        }

        const responseText = await response.text()
        console.log(`🔍 Frontend: Raw response text: "${responseText}"`)
        
        let data;
        try {
            data = JSON.parse(responseText)
            console.log('✅ Frontend: JSON parsed successfully:', data)
        } catch (parseError) {
            console.error('❌ Frontend: JSON parse error:', parseError)
            throw new Error(`Invalid JSON response: ${responseText}`)
        }

        return data
        
    } catch (error) {
        console.error('❌ Frontend: Error en sendMessage:', error)
        
        if (error.message.includes('Failed to fetch')) {
            throw new Error('No se pudo conectar con el servidor. Verifica que el backend esté ejecutándose en http://localhost:5000')
        }
        throw error
    }
}

export const startMonitoring = async () => {
    const response = await fetch(`${API_BASE}/monitor/start`, { method: 'POST' })
    if (!response.ok) throw new Error('No se pudo iniciar el monitoreo')
    return await response.json()
}

export const stopMonitoring = async () => {
    const response = await fetch(`${API_BASE}/monitor/stop`, { method: 'POST' })
    if (!response.ok) throw new Error('No se pudo detener el monitoreo')
    return await response.json()
}

export const getMonitoringStatus = async () => {
    const response = await fetch(`${API_BASE}/monitor/status`)
    if (!response.ok) throw new Error('No se pudo obtener el estado del monitoreo')
    return await response.json()
}