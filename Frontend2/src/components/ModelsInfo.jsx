import React from 'react'
import { Brain, Zap } from 'lucide-react'

const ModelsInfo = () => {
  return (
    <div className="models">
      <div className="model-card">
        <div className="model-icon">
          <Brain />
        </div>
        <h3>Gemini</h3>
        <p>Modelo avanzado de lenguaje para conversaciones naturales</p>
      </div>
      <div className="model-card">
        <div className="model-icon">
          <Zap />
        </div>
        <h3>GPT-4</h3>
        <p>Modelo de última generación para tareas complejas</p>
      </div>
    </div>
  )
}

export default ModelsInfo