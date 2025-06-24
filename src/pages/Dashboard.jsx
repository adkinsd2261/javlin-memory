import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Brain, Activity, TrendingUp, Clock, Zap, Plus, Search, Filter } from 'lucide-react'

const Dashboard = ({ systemHealth }) => {
  const [stats, setStats] = useState(null)
  const [recentMemories, setRecentMemories] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [statsRes, memoriesRes] = await Promise.all([
        fetch('http://localhost:5000/stats'),
        fetch('http://localhost:5000/memory?limit=5')
      ])
      
      const statsData = await statsRes.json()
      const memoriesData = await memoriesRes.json()
      
      setStats(statsData)
      setRecentMemories(memoriesData.memories || [])
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const StatCard = ({ icon: Icon, title, value, subtitle, color = "purple" }) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="glass rounded-2xl p-6 hover-lift"
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${
          color === 'purple' ? 'from-purple-500 to-pink-500' :
          color === 'blue' ? 'from-blue-500 to-cyan-500' :
          color === 'green' ? 'from-green-500 to-emerald-500' :
          'from-orange-500 to-red-500'
        } flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-white">{value}</div>
          <div className="text-sm text-gray-400">{subtitle}</div>
        </div>
      </div>
      <h3 className="text-lg font-semibold text-white">{title}</h3>
    </motion.div>
  )

  const MemoryCard = ({ memory, index }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="glass rounded-xl p-4 hover-lift cursor-pointer"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            memory.success ? 'bg-green-400' : 'bg-red-400'
          }`} />
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
            {memory.type}
          </span>
        </div>
        <span className="text-xs text-gray-500">
          {new Date(memory.timestamp).toLocaleDateString()}
        </span>
      </div>
      
      <h4 className="text-white font-medium mb-2 line-clamp-2">
        {memory.topic}
      </h4>
      
      <p className="text-gray-400 text-sm line-clamp-2">
        {memory.output}
      </p>
      
      {memory.tags && memory.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {memory.tags.slice(0, 3).map((tag, i) => (
            <span key={i} className="px-2 py-1 bg-white/10 rounded-md text-xs text-gray-300">
              #{tag}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  )

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading your workspace...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-violet-900/20">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <motion.h1 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl font-bold gradient-text mb-2"
          >
            Welcome back
          </motion.h1>
          <p className="text-gray-400 text-lg">
            Your creative workspace is ready. What will we build today?
          </p>
        </div>

        {/* Quick Actions */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <div className="flex items-center space-x-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-xl font-semibold flex items-center space-x-2 hover-lift"
            >
              <Plus className="w-5 h-5" />
              <span>New Memory</span>
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="glass text-white px-6 py-3 rounded-xl font-semibold flex items-center space-x-2 hover-lift"
            >
              <Search className="w-5 h-5" />
              <span>Search</span>
            </motion.button>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          <StatCard
            icon={Brain}
            title="Total Memories"
            value={stats?.total_memories || 0}
            subtitle="entries"
            color="purple"
          />
          <StatCard
            icon={TrendingUp}
            title="Success Rate"
            value={stats?.success_rate || "0%"}
            subtitle="completion"
            color="green"
          />
          <StatCard
            icon={Activity}
            title="System Health"
            value={systemHealth?.status === 'healthy' ? 'Healthy' : 'Issues'}
            subtitle="status"
            color={systemHealth?.status === 'healthy' ? 'green' : 'orange'}
          />
          <StatCard
            icon={Zap}
            title="Active Sessions"
            value="1"
            subtitle="current"
            color="blue"
          />
        </motion.div>

        {/* Recent Activity */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="grid grid-cols-1 lg:grid-cols-3 gap-8"
        >
          {/* Recent Memories */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Recent Activity</h2>
              <button className="text-purple-400 hover:text-purple-300 text-sm font-medium">
                View All
              </button>
            </div>
            
            <div className="space-y-4">
              {recentMemories.map((memory, index) => (
                <MemoryCard key={memory.timestamp || index} memory={memory} index={index} />
              ))}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="glass rounded-2xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Quick Insights</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Categories</span>
                  <span className="text-white font-medium">
                    {Object.keys(stats?.categories || {}).length}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Types</span>
                  <span className="text-white font-medium">
                    {Object.keys(stats?.types || {}).length}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Success Rate</span>
                  <span className="text-green-400 font-medium">
                    {stats?.success_rate || "0%"}
                  </span>
                </div>
              </div>
            </div>

            {/* System Status */}
            <div className="glass rounded-2xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">System Status</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">API</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full" />
                    <span className="text-green-400 text-sm">Online</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Memory</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full" />
                    <span className="text-green-400 text-sm">Healthy</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">AI Agent</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full" />
                    <span className="text-green-400 text-sm">Ready</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default Dashboard