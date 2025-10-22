import React from 'react'
import { Cpu, MessageCircle } from 'lucide-react'

const Header = () => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">
          <Cpu className="logo-icon" />
          <h1>Chat MAAS</h1>
        </div>
        <p>Model as a Service - Chatea con nuestros modelos de IA</p>
      </div>
    </header>
  )
}

export default Header