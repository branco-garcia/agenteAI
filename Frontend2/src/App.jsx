import React, { useState } from 'react'
import Header from './components/Header'
import ModelsInfo from './components/ModelsInfo'
import Chat from './components/Chat'
import Dashboard from './components/Dashboard'
// Importa los iconos que usaremos
import { MessageSquare, LayoutDashboard } from 'lucide-react'

function App() {
  const [currentView, setCurrentView] = useState('chat')

  return (
    <div className="app">
      <div className="container">
        <Header />
        <ModelsInfo />
        {/* Navegación entre Chat y Dashboard */}
        <div className="view-navigation">
          <button
            className={`nav-btn ${currentView === 'chat' ? 'active' : ''}`}
            onClick={() => setCurrentView('chat')}
          >
            {/* Icono y texto añadidos */}
            <MessageSquare size={18} />
            Chat
          </button>
          <button
            className={`nav-btn ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
          >
            {/* Icono y texto añadidos */}
            <LayoutDashboard size={18} />
            Dashboard
          </button>
        </div>

        {currentView === 'chat' ? <Chat /> : <Dashboard />}
      </div>
    </div>
  )
}

export default App