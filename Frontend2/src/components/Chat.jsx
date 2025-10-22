import React, { useState, useRef, useEffect } from 'react'
import { Send, Monitor } from 'lucide-react'
import Message from './Message'
import { sendMessage, startMonitoring, stopMonitoring, getMonitoringStatus } from '../services/api'

const Chat = () => {
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      text: '¡Hola! Soy tu asistente MAAS. ¿En qué puedo ayudarte hoy?', 
      isUser: false,
      timestamp: new Date()
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [monitoringStatus, setMonitoringStatus] = useState(false)
  const chatContainerRef = useRef(null)

  useEffect(() => {
    checkMonitoringStatus()
    scrollToBottom()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }

  const checkMonitoringStatus = async () => {
    try {
      const status = await getMonitoringStatus()
      setMonitoringStatus(status.monitoreo_activo)
    } catch (error) {
      console.error('Error checking monitoring status:', error)
    }
  }

  const handleSend = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      text: inputMessage.trim(),
      isUser: true,
      timestamp: new Date()
    }
    
    setInputMessage('')
    setIsLoading(true)

    // Add user message immediately
    setMessages(prev => [...prev, userMessage])

    try {
      // Send to backend
      const response = await sendMessage(userMessage.text)
      
      // Add bot response
      const botMessage = {
        id: Date.now() + 1,
        text: response.respuesta,
        isUser: false,
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Lo siento, ha ocurrido un error. Por favor, intenta de nuevo más tarde.',
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleMonitoringToggle = async () => {
    try {
      if (monitoringStatus) {
        await stopMonitoring()
        setMonitoringStatus(false)
        const stopMessage = {
          id: Date.now(),
          text: '🔍 Monitoreo de máquinas detenido',
          isUser: false,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, stopMessage])
      } else {
        await startMonitoring()
        setMonitoringStatus(true)
        const startMessage = {
          id: Date.now(),
          text: '🔍 Monitoreo de máquinas iniciado. Recibirás notificaciones de cambios.',
          isUser: false,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, startMessage])
      }
    } catch (error) {
      console.error('Error toggling monitoring:', error)
      const errorMessage = {
        id: Date.now(),
        text: '❌ Error al cambiar el estado del monitoreo',
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-controls">
        <button 
          className={`monitor-btn ${monitoringStatus ? 'active' : ''}`}
          onClick={handleMonitoringToggle}
          type="button"
        >
          <Monitor size={18} />
          {monitoringStatus ? 'Detener Monitoreo' : 'Iniciar Monitoreo'}
        </button>
      </div>

      <div className="chat-messages" ref={chatContainerRef}>
        {messages.map((message) => (
          <Message 
            key={message.id}
            message={message.text}
            isUser={message.isUser}
            timestamp={message.timestamp}
          />
        ))}
        {isLoading && (
          <div className="message bot-message">
            <div className="message-avatar">
              <Monitor size={16} />
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Escribe tu mensaje..."
          disabled={isLoading}
        />
        <button 
          onClick={handleSend} 
          disabled={isLoading || !inputMessage.trim()}
          type="button"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  )
}

export default Chat