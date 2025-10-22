import React from 'react'
import { User, Bot } from 'lucide-react'

const Message = ({ message, isUser, timestamp }) => {
  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className={`message ${isUser ? 'user-message' : 'bot-message'}`}>
      <div className="message-avatar">
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className="message-content">
        <div className="message-text">{message}</div>
        <div className="message-time">
          {timestamp ? formatTime(timestamp) : formatTime(new Date())}
        </div>
      </div>
    </div>
  )
}

export default Message