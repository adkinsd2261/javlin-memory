import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Filter, Calendar, Tag, TrendingUp, Clock, CheckCircle, XCircle } from 'lucide-react'

const MemoryTimeline = () => {
  const [memories, setMemories] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedFilter, setSelectedFilter] = useState('all')
  const [selectedCategory, setSelectedCategory] = useState('all')

  useEffect(() => {
    fetchMemories()
  }, [])

  const fetchMemories = async () => {
    try {
      const response = await fetch('/api/memory?limit=50')
      const data = await response.json()
      setMemories(data.memories || [])
    } catch (error) {
      console.error('Failed to fetch memories:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredMemories = memories.filter(memory => {
    const matchesSearch = memory.topic.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         memory.output.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesFilter = selectedFilter === 'all' || 
                         (selectedFilter === 'success' && memory.success) ||
                         (selectedFilter === 'failed' && !memory.success)
    
    const matchesCategory = selectedCategory === 'all' || memory.category === selectedCategory

    return matchesSearch && matchesFilter && matchesCategory
  })

  const categories = [...new Set(memories.map(m => m.category))].filter(Boolean)
  const types = [...new Set(memories.map(m => m.type))].filter(Boolean)

  const getTypeIcon = (type) => {
    const icons = {
      'SystemUpdate': '⚙️',
      'Feature': '✨',
      'BugFix': '🐛',
      'UserInteraction': '👤',
      'Interaction': '💬',
      'API': '🔌',
      'Database': '🗄️',
      'Security': '🔒',
      'Performance': '⚡',
      'Documentation': '📚',
      'Testing': '🧪',
      'Deployment': '🚀',
      'Monitoring': '📊'
    }
    return icons[type] || '📝'
  }

  const formatDate = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInHours = (now - date) / (1000 * 60 * 60)
    
    if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`
    } else if (diffInHours < 168) {
      return `${Math.floor(diffInHours / 24)}d ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  const MemoryCard = ({ memory, index }) => (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="relative"
    >
      {/* Timeline line */}
      <div className="absolute left-6 top-16 bottom-0 w-px bg-gradient-to-b from-purple-500/50 to-transparent" />
      
      {/* Timeline dot */}
      <div className="absolute left-4 top-8 w-4 h-4 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 border-2 border-gray-900" />
      
      {/* Card */}
      <div className="ml-16 mb-8">
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="glass rounded-2xl p-6 hover-lift"
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{getTypeIcon(memory.type)}</span>
              <div>
                <h3 className="text-lg font-semibold text-white">{memory.topic}</h3>
                <div className="flex items-center space-x-2 mt-1">
                  <span className="text-xs font-medium text-purple-400 uppercase tracking-wide">
                    {memory.type}
                  </span>
                  <span className="text-gray-500">•</span>
                  <span className="text-xs text-gray-400">{memory.category}</span>
                </div>
              </div>
            </div>
            
            <div className="text-right">
              <div className="flex items-center space-x-2 mb-1">
                {memory.success ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400" />
                )}
                <span className={`text-sm font-medium ${
                  memory.success ? 'text-green-400' : 'text-red-400'
                }`}>
                  {memory.success ? 'Success' : 'Failed'}
                </span>
              </div>
              <span className="text-xs text-gray-500">{formatDate(memory.timestamp)}</span>
            </div>
          </div>

          {/* Content */}
          <div className="space-y-3">
            {memory.input && (
              <div>
                <h4 className="text-sm font-medium text-gray-400 mb-1">Input:</h4>
                <p className="text-gray-300 text-sm bg-white/5 rounded-lg p-3">
                  {memory.input}
                </p>
              </div>
            )}
            
            {memory.output && (
              <div>
                <h4 className="text-sm font-medium text-gray-400 mb-1">Output:</h4>
                <p className="text-gray-300 text-sm bg-white/5 rounded-lg p-3">
                  {memory.output}
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/10">
            <div className="flex items-center space-x-4">
              {memory.score && (
                <div className="flex items-center space-x-2">
                  <TrendingUp className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-400">
                    {memory.score}/{memory.maxScore || 25}
                  </span>
                </div>
              )}
            </div>
            
            {memory.tags && memory.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {memory.tags.slice(0, 3).map((tag, i) => (
                  <span key={i} className="px-2 py-1 bg-white/10 rounded-md text-xs text-gray-300">
                    #{tag}
                  </span>
                ))}
                {memory.tags.length > 3 && (
                  <span className="px-2 py-1 bg-white/10 rounded-md text-xs text-gray-400">
                    +{memory.tags.length - 3}
                  </span>
                )}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </motion.div>
  )

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading your memory timeline...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-violet-900/20">
      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <motion.h1 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl font-bold gradient-text mb-2"
          >
            Memory Timeline
          </motion.h1>
          <p className="text-gray-400 text-lg">
            Your complete creative journey, remembered and connected
          </p>
        </div>

        {/* Filters */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-2xl p-6 mb-8"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search memories..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus-ring"
              />
            </div>

            {/* Status Filter */}
            <select
              value={selectedFilter}
              onChange={(e) => setSelectedFilter(e.target.value)}
              className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus-ring"
            >
              <option value="all">All Status</option>
              <option value="success">Success Only</option>
              <option value="failed">Failed Only</option>
            </select>

            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus-ring"
            >
              <option value="all">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
        </motion.div>

        {/* Timeline */}
        <div className="relative">
          <AnimatePresence>
            {filteredMemories.length > 0 ? (
              filteredMemories.map((memory, index) => (
                <MemoryCard 
                  key={memory.timestamp || index} 
                  memory={memory} 
                  index={index} 
                />
              ))
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-16"
              >
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-xl font-semibold text-white mb-2">No memories found</h3>
                <p className="text-gray-400">Try adjusting your search or filters</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}

export default MemoryTimeline