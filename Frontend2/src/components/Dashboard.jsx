import React, { useState, useEffect } from 'react'
import { Server, Cpu, HardDrive, Network, AlertCircle, Play, PowerOff, RefreshCw, AlertTriangle } from 'lucide-react'

const Dashboard = () => {
  const [metricas, setMetricas] = useState(null)
  const [maquinas, setMaquinas] = useState([])
  const [alertas, setAlertas] = useState([])
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [error, setError] = useState(null)

  const cargarDatos = async () => {
    try {
      setError(null)
      
      // Cargar solo las métricas principales, no los endpoints individuales
      const metricasResponse = await fetch('/api/dashboard/metricas')
      if (!metricasResponse.ok) {
        throw new Error(`Error ${metricasResponse.status}: ${metricasResponse.statusText}`)
      }
      
      const metricasData = await metricasResponse.json()
      
      setMetricas(metricasData)
      setMaquinas(Array.isArray(metricasData.maquinas) ? metricasData.maquinas : [])
      setAlertas(Array.isArray(metricasData.alertas) ? metricasData.alertas : [])
      
    } catch (error) {
      console.error('Error general cargando datos:', error)
      setError(`Error al cargar los datos: ${error.message}`)
      setMaquinas([])
      setAlertas([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    cargarDatos()
    
    if (autoRefresh) {
      const interval = setInterval(cargarDatos, 10000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const getSaludColor = (salud) => {
    switch (salud) {
      case 'healthy': return 'text-green-500'
      case 'warning': return 'text-yellow-500'
      case 'critical': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  const getSaludBgColor = (salud) => {
    switch (salud) {
      case 'healthy': return 'bg-green-50 border-green-200'
      case 'warning': return 'bg-yellow-50 border-yellow-200'
      case 'critical': return 'bg-red-50 border-red-200'
      default: return 'bg-gray-50 border-gray-200'
    }
  }

  const getPowerStateIcon = (powerState) => {
    return powerState === 'on' ? 
      <Play size={16} className="text-green-500" /> : 
      <PowerOff size={16} className="text-red-500" />
  }

  if (loading) {
    return (
      <div className="dashboard-loading">
        <RefreshCw size={32} className="animate-spin text-primary-color" />
        <p>Cargando dashboard...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <AlertTriangle size={48} className="text-red-500 mb-4" />
        <h2>Error al cargar el dashboard</h2>
        <p>{error}</p>
        <button onClick={cargarDatos} className="btn-refresh mt-4">
          <RefreshCw size={16} />
          Reintentar
        </button>
      </div>
    )
  }

  return (
    <div className="dashboard">
      {/* Header del Dashboard */}
      <div className="dashboard-header">
        <h1>Dashboard MAAS</h1>
        <div className="dashboard-controls">
          <button 
            onClick={cargarDatos}
            className="btn-refresh"
          >
            <RefreshCw size={16} />
            Actualizar
          </button>
          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh cada 10s
          </label>
        </div>
      </div>

      {/* Estado de conexión */}
      {metricas?.error && (
        <div className="alerta-card warning">
          <AlertTriangle size={20} />
          <div className="alerta-content">
            <strong>Advertencia</strong>
            <p>Algunos datos pueden estar incompletos: {metricas.error}</p>
          </div>
        </div>
      )}

      {/* Métricas Principales */}
      {metricas?.resumen && Object.keys(metricas.resumen).length > 0 && (
        <div className="metricas-grid">
          <div className="metrica-card">
            <div className="metrica-icon">
              <Server size={24} />
            </div>
            <div className="metrica-content">
              <h3>Total Máquinas</h3>
              <p className="metrica-valor">{metricas.resumen.total_maquinas || 0}</p>
              <div className="metrica-sub">
                <span className="text-green-500">🟢 {metricas.resumen.maquinas_encendidas || 0}</span>
                <span className="text-red-500">🔴 {metricas.resumen.maquinas_apagadas || 0}</span>
              </div>
            </div>
          </div>

          <div className="metrica-card">
            <div className="metrica-icon">
              <Cpu size={24} />
            </div>
            <div className="metrica-content">
              <h3>CPU Total</h3>
              <p className="metrica-valor">{metricas.resumen.total_cpu_cores || 0} núcleos</p>
            </div>
          </div>

          <div className="metrica-card">
          
            <div className="metrica-content">
              <h3>RAM Total</h3>
              <p className="metrica-valor">{metricas.resumen.total_ram_gb || 0} GB</p>
            </div>
          </div>

          <div className="metrica-card">
            <div className="metrica-icon">
              <HardDrive size={24} />
            </div>
            <div className="metrica-content">
              <h3>Almacenamiento</h3>
              <p className="metrica-valor">{metricas.resumen.total_almacenamiento_gb || 0} GB</p>
            </div>
          </div>

          <div className="metrica-card">
            <div className="metrica-icon">
              <Network size={24} />
            </div>
            <div className="metrica-content">
              <h3>Subredes</h3>
              <p className="metrica-valor">{metricas.red?.total_subredes || 0}</p>
            </div>
          </div>

          <div className="metrica-card">
            <div className="metrica-icon">
              <AlertCircle size={24} />
            </div>
            <div className="metrica-content">
              <h3>Alertas Activas</h3>
              <p className="metrica-valor">{alertas.length}</p>
              <div className="metrica-sub">
                {alertas.filter(a => a.tipo === 'critical').length} críticas
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Alertas */}
      {alertas.length > 0 && (
        <div className="alertas-section">
          <h2>Alertas Activas</h2>
          <div className="alertas-grid">
            {alertas.map((alerta, index) => (
              <div key={index} className={`alerta-card ${alerta.tipo}`}>
                <AlertCircle size={20} />
                <div className="alerta-content">
                  <strong>{alerta.maquina}</strong>
                  <p>{alerta.mensaje}</p>
                  <small>{new Date(alerta.timestamp).toLocaleString()}</small>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Lista de Máquinas */}
      <div className="maquinas-section">
        <h2>Máquinas ({maquinas.length})</h2>
        
        {maquinas.length === 0 ? (
          <div className="no-data">
            <Server size={48} className="text-gray-400" />
            <p>No se encontraron máquinas</p>
          </div>
        ) : (
          <div className="maquinas-grid">
            {maquinas.map((maquina, index) => (
              <div key={maquina.system_id || index} className={`maquina-card ${getSaludBgColor(maquina.salud)}`}>
                <div className="maquina-header">
                  <div className="maquina-info">
                    <h3>{maquina.hostname}</h3>
                    <span className={`salud-badge ${getSaludColor(maquina.salud)}`}>
                      {maquina.salud}
                    </span>
                  </div>
                  <div className="maquina-estado">
                    {getPowerStateIcon(maquina.power_state)}
                    <span>{maquina.power_state === 'on' ? 'Encendida' : 'Apagada'}</span>
                  </div>
                </div>
                
                <div className="maquina-details">
                  <div className="detail-row">
                    <span>IP:</span>
                    <span>{maquina.ip}</span>
                  </div>
                  <div className="detail-row">
                    <span>SO:</span>
                    <span>{maquina.so}</span>
                  </div>
                  <div className="detail-row">
                    <span>CPU:</span>
                    <span>{maquina.cpu_cores} núcleos</span>
                  </div>
                  <div className="detail-row">
                    <span>RAM:</span>
                    <span>{maquina.ram_gb} GB</span>
                  </div>
                  <div className="detail-row">
                    <span>Almacenamiento:</span>
                    <span>{maquina.almacenamiento_gb} GB</span>
                  </div>
                  <div className="detail-row">
                    <span>Zona:</span>
                    <span>{maquina.zona}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard