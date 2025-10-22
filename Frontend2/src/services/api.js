const API_BASE = '/api'

const handleResponse = async (response) => {
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Error ${response.status}: ${errorText}`)
  }
  return response.json()
}

export const sendMessage = async (message) => {
  try {
    const response = await fetch(`${API_BASE}/preguntar`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ pregunta: message }),
    })
    return await handleResponse(response)
  } catch (error) {
    console.error('Error sending message:', error)
    throw new Error('No se pudo conectar con el servidor. Verifica que el backend esté ejecutándose.')
  }
}

export const startMonitoring = async () => {
  try {
    const response = await fetch(`${API_BASE}/monitor/start`, {
      method: 'POST',
    })
    return await handleResponse(response)
  } catch (error) {
    console.error('Error starting monitoring:', error)
    throw new Error('No se pudo iniciar el monitoreo')
  }
}

export const stopMonitoring = async () => {
  try {
    const response = await fetch(`${API_BASE}/monitor/stop`, {
      method: 'POST',
    })
    return await handleResponse(response)
  } catch (error) {
    console.error('Error stopping monitoring:', error)
    throw new Error('No se pudo detener el monitoreo')
  }
}

export const getMonitoringStatus = async () => {
  try {
    const response = await fetch(`${API_BASE}/monitor/status`)
    return await handleResponse(response)
  } catch (error) {
    console.error('Error getting monitoring status:', error)
    throw new Error('No se pudo obtener el estado del monitoreo')
  }
}