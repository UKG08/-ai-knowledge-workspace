import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './App.css'

const API_URL = 'http://localhost:8000'

// Particle Component
function Particles() {
  return (
    <div className="particles">
      {[...Array(50)].map((_, i) => (
        <div
          key={i}
          className="particle"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 5}s`,
            animationDuration: `${5 + Math.random() * 10}s`
          }}
        />
      ))}
    </div>
  )
}

// Typing Animation Component
function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <span></span>
      <span></span>
      <span></span>
    </div>
  )
}

// Typing Text Animation Component
function TypewriterText({ text, onComplete }) {
  const [displayedText, setDisplayedText] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setDisplayedText(prev => prev + text[currentIndex])
        setCurrentIndex(prev => prev + 1)
      }, 20) // Speed of typing (20ms per character)

      return () => clearTimeout(timeout)
    } else if (onComplete) {
      onComplete()
    }
  }, [currentIndex, text, onComplete])

  return <span>{displayedText}</span>
}

// File Upload Card Component
function FileUploadCard({ onUpload, uploading }) {
  const fileInputRef = useRef(null)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onUpload({ target: { files: [e.dataTransfer.files[0]] } })
    }
  }

  return (
    <div
      className={`upload-card ${dragActive ? 'drag-active' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => !uploading && fileInputRef.current?.click()}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        onChange={onUpload}
        disabled={uploading}
        style={{ display: 'none' }}
      />
      
      <div className="upload-icon">
        {uploading ? (
          <div className="spinner"></div>
        ) : (
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
        )}
      </div>
      
      <h3>{uploading ? 'Processing...' : 'Upload PDF'}</h3>
      <p>{uploading ? 'Analyzing your document' : 'Click or drag & drop'}</p>
    </div>
  )
}

// Message Component with typewriter effect
function Message({ message, index, isLatest }) {
  const [isTyping, setIsTyping] = useState(isLatest && message.type === 'assistant')

  return (
    <div 
      className={`message ${message.type}`}
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      <div className="message-avatar">
        {message.type === 'user' ? '👤' : message.type === 'assistant' ? '🤖' : 'ℹ️'}
      </div>
      
      <div className="message-bubble">
        {message.type === 'assistant' && (
          <div className="message-header">
            <span className="ai-badge">AI Assistant</span>
          </div>
        )}
        
        <div className="message-text">
          {isTyping && message.type === 'assistant' ? (
            <TypewriterText 
              text={message.content} 
              onComplete={() => setIsTyping(false)}
            />
          ) : (
            message.content
          )}
        </div>
      </div>
    </div>
  )
}

// Main App Component
function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [status, setStatus] = useState(null)
  const [showStats, setShowStats] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    fetchStatus()
    // Welcome message
    setTimeout(() => {
      setMessages([{
        type: 'assistant',
        content: '👋 Welcome to AI Knowledge Workspace! Upload a PDF to get started, and I\'ll help you find answers instantly.',
      }])
    }, 500)
  }, [])

  // Smooth scroll with delay
  useEffect(() => {
    const timer = setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end'
      })
    }, 100)
    return () => clearTimeout(timer)
  }, [messages])

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/status`)
      setStatus(response.data)
    } catch (error) {
      console.error('Error fetching status:', error)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    setUploading(true)
    
    setMessages(prev => [...prev, {
      type: 'system',
      content: `📄 Processing ${file.name}...`
    }])

    try {
      await axios.post(`${API_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      setMessages(prev => [
        ...prev.slice(0, -1),
        {
          type: 'system',
          content: `✅ ${file.name} is ready! You can now ask questions about it.`
        }
      ])
      
      await fetchStatus()
      setTimeout(() => inputRef.current?.focus(), 500)
    } catch (error) {
      setMessages(prev => [
        ...prev.slice(0, -1),
        {
          type: 'error',
          content: `❌ Failed to process ${file.name}. Please try again.`
        }
      ])
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const question = input.trim()
    setInput('')
    
    setMessages(prev => [...prev, { 
      type: 'user', 
      content: question 
    }])
    
    setLoading(true)
    
    try {
      const response = await axios.post(`${API_URL}/ask`, {
        question: question,
        n_results: 3
      })
      
      // Add AI response (will trigger typewriter effect)
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: response.data.answer
      }])
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'error',
        content: error.response?.data?.detail || 'I couldn\'t find an answer. Please try rephrasing your question.'
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleClearDatabase = async () => {
    if (!confirm('🗑️ Clear all documents? This cannot be undone.')) return
    
    try {
      await axios.delete(`${API_URL}/clear`)
      setMessages([{
        type: 'system',
        content: '✅ All documents have been cleared. Upload new PDFs to get started!'
      }])
      await fetchStatus()
    } catch (error) {
      console.error('Clear error:', error)
    }
  }

  const totalPDFs = status ? Object.keys(status.indexed_pdfs).length : 0

  return (
    <div className="app">
      <Particles />
      
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
            </div>
            <div>
              <h1>AI Knowledge Workspace</h1>
              <p>Powered by RAG Technology</p>
            </div>
          </div>
          
          <div className="header-actions">
            <button 
              className="stats-button"
              onClick={() => setShowStats(!showStats)}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="20" x2="12" y2="10"></line>
                <line x1="18" y1="20" x2="18" y2="4"></line>
                <line x1="6" y1="20" x2="6" y2="16"></line>
              </svg>
              Stats
            </button>
          </div>
        </div>
        
        {/* Stats Panel - REMOVED AI MODEL */}
        {showStats && status && (
          <div className="stats-panel">
            <div className="stat-card">
              <div className="stat-icon">📄</div>
              <div className="stat-value">{status.total_documents}</div>
              <div className="stat-label">Document Chunks</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">📚</div>
              <div className="stat-value">{totalPDFs}</div>
              <div className="stat-label">PDF Files</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">💬</div>
              <div className="stat-value">{messages.filter(m => m.type === 'user').length}</div>
              <div className="stat-label">Questions Asked</div>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <div className="main-container">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-section">
            <h3 className="section-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
              Upload Documents
            </h3>
            
            <FileUploadCard 
              onUpload={handleFileUpload}
              uploading={uploading}
            />
          </div>

          {totalPDFs > 0 && (
            <div className="sidebar-section">
              <h3 className="section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                </svg>
                Your Documents
              </h3>
              
              <div className="pdf-list">
                {Object.entries(status.indexed_pdfs).map(([name]) => (
                  <div key={name} className="pdf-item">
                    <div className="pdf-icon">📄</div>
                    <div className="pdf-info">
                      <div className="pdf-name">{name}</div>
                      <div className="pdf-status">Ready</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="sidebar-section">
            <h3 className="section-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M12 1v6m0 6v6m5.657-13.657l-4.243 4.243m0 4.243l-4.243 4.243m12.728 0l-4.243-4.243m0-4.243l-4.243-4.243"></path>
              </svg>
              Actions
            </h3>
            
            <button
              className="action-btn refresh"
              onClick={fetchStatus}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 4 23 10 17 10"></polyline>
                <polyline points="1 20 1 14 7 14"></polyline>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
              </svg>
              Refresh
            </button>
            
            {totalPDFs > 0 && (
              <button
                className="action-btn danger"
                onClick={handleClearDatabase}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
                Clear All
              </button>
            )}
          </div>

          <div className="sidebar-footer">
            <div className="tech-badge">
              <span className="badge-label">Powered by</span>
              <div className="tech-stack">
                <span>React</span>
                <span>FastAPI</span>
                <span>AI</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Chat Area */}
        <main className="chat-area">
          <div className="messages-container">
            {messages.map((msg, idx) => (
              <Message 
                key={idx} 
                message={msg} 
                index={idx}
                isLatest={idx === messages.length - 1}
              />
            ))}
            
            {loading && (
              <div className="message assistant" style={{ animationDelay: '0s' }}>
                <div className="message-avatar">🤖</div>
                <div className="message-bubble">
                  <div className="message-header">
                    <span className="ai-badge">AI Assistant</span>
                  </div>
                  <TypingIndicator />
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="input-container">
            <form className="input-form" onSubmit={handleSubmit}>
              <div className="input-wrapper">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={
                    status?.total_documents === 0 
                      ? "Upload a PDF first..."
                      : "Ask me anything..."
                  }
                  disabled={loading || status?.total_documents === 0}
                  className="input-field"
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim() || status?.total_documents === 0}
                  className="send-btn"
                >
                  {loading ? (
                    <div className="spinner-small"></div>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="22" y1="2" x2="11" y2="13"></line>
                      <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                  )}
                </button>
              </div>
              
              <div className="input-footer">
                <span className="hint">
                  {status?.total_documents > 0 
                    ? `💡 ${totalPDFs} document${totalPDFs > 1 ? 's' : ''} ready`
                    : '💡 Upload a PDF to start'
                  }
                </span>
              </div>
            </form>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App