import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Mic, MicOff, Settings, Maximize2, Minimize2, Brain, Code, Palette } from 'lucide-react'

const JavWorkspace = ({ mode, setMode }) => {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    // Initial greeting
    setMessages([
      {
        id: 1,
        type: 'jav',
        content: `Hey! I'm Jav, your creative AI partner. I'm currently in ${mode} mode. What would you like to work on together?`,
        timestamp: new Date()
      }
    ])
  }, [mode])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const javResponse = {
        id: Date.now() + 1,
        type: 'jav',
        content: generateResponse(inputValue, mode),
        timestamp: new Date()
      }
      setMessages(prev => [...prev, javResponse])
      setIsTyping(false)
    }, 1500)
  }

  const generateResponse = (input, currentMode) => {
    const responses = {
      creative: [
        "That's a fascinating idea! Let me help you explore that concept further. What specific aspect would you like to dive into?",
        "I love the creative direction you're thinking! Here's how we could approach this...",
        "Great creative thinking! Let's build on that idea and see where it takes us.",
      ],
      dev: [
        "I can help you implement that. Let me break down the technical approach...",
        "Good technical question! Here's how we can solve this systematically...",
        "Let's debug this step by step. I'll guide you through the process...",
      ]
    }
    
    const modeResponses = responses[currentMode] || responses.creative
    return modeResponses[Math.floor(Math.random() * modeResponses.length)]
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const toggleListening = () => {
    setIsListening(!isListening)
    // Voice recognition would be implemented here
  }

  const Message = ({ message }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} mb-6`}
    >
      <div className={`max-w-3xl ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
        {message.type === 'jav' && (
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-medium text-purple-400">Jav</span>
            <span className="text-xs text-gray-500">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
        )}
        
        <div className={`rounded-2xl px-6 py-4 ${
          message.type === 'user' 
            ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white ml-12' 
            : 'glass text-white'
        }`}>
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        
        {message.type === 'user' && (
          <div className="text-right mt-1">
            <span className="text-xs text-gray-500">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  )

  return (
    <div className={`${isFullscreen ? 'fixed inset-0 z-50' : 'min-h-screen'} bg-gradient-to-br from-gray-900 via-purple-900/20 to-violet-900/20`}>
      <div className="max-w-6xl mx-auto px-6 py-8 h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <motion.h1 
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-3xl font-bold gradient-text"
            >
              Jav Workspace
            </motion.h1>
            <p className="text-gray-400">
              {mode === 'creative' ? 'Creative collaboration mode' : 'Development assistance mode'}
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Mode Toggle */}
            <div className="flex items-center space-x-2 glass rounded-xl p-1">
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={() => setMode('creative')}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 text-sm transition-colors ${
                  mode === 'creative'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                <Palette className="w-4 h-4" />
                <span>Creative</span>
              </motion.button>
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={() => setMode('dev')}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 text-sm transition-colors ${
                  mode === 'dev'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                <Code className="w-4 h-4" />
                <span>Dev</span>
              </motion.button>
            </div>
            
            {/* Controls */}
            <div className="flex items-center space-x-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="glass p-2 rounded-lg hover-lift"
              >
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="glass p-2 rounded-lg hover-lift"
              >
                <Settings className="w-4 h-4" />
              </motion.button>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 glass rounded-2xl p-6 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto mb-6 space-y-4">
            <AnimatePresence>
              {messages.map((message) => (
                <Message key={message.id} message={message} />
              ))}
            </AnimatePresence>
            
            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start mb-6"
              >
                <div className="max-w-3xl">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                      <Brain className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-sm font-medium text-purple-400">Jav</span>
                  </div>
                  <div className="glass rounded-2xl px-6 py-4">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
                      <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                      <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="flex items-end space-x-4">
            <div className="flex-1 relative">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Ask Jav anything in ${mode} mode...`}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 resize-none focus-ring"
                rows="1"
                style={{ minHeight: '48px', maxHeight: '120px' }}
              />
            </div>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={toggleListening}
              className={`p-3 rounded-xl transition-colors ${
                isListening 
                  ? 'bg-red-600 text-white' 
                  : 'glass text-gray-400 hover:text-white'
              }`}
            >
              {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-3 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default JavWorkspace