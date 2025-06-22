import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Brain, Baseline as Timeline, Space as Workspace, Settings, Activity, Zap, Palette } from 'lucide-react'

const Navbar = ({ currentMode, setCurrentMode, systemHealth }) => {
  const location = useLocation()

  const navItems = [
    { path: '/', icon: Brain, label: 'Dashboard' },
    { path: '/timeline', icon: Timeline, label: 'Memory Timeline' },
    { path: '/workspace', icon: Workspace, label: 'Jav Workspace' },
  ]

  const isHealthy = systemHealth?.status === 'healthy'

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-black/20 backdrop-blur-lg border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center"
            >
              <Brain className="w-5 h-5 text-white" />
            </motion.div>
            <span className="text-xl font-bold text-white">MemoryOS</span>
          </Link>

          {/* Navigation Items */}
          <div className="flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              
              return (
                <Link key={item.path} to={item.path}>
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                      isActive 
                        ? 'bg-purple-600 text-white' 
                        : 'text-gray-300 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </motion.div>
                </Link>
              )
            })}
          </div>

          {/* Mode Toggle & Status */}
          <div className="flex items-center space-x-4">
            {/* Mode Toggle */}
            <div className="flex items-center space-x-2 bg-white/10 rounded-lg p-1">
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={() => setCurrentMode('creative')}
                className={`px-3 py-1 rounded-md flex items-center space-x-1 text-sm transition-colors ${
                  currentMode === 'creative'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                <Palette className="w-3 h-3" />
                <span>Creative</span>
              </motion.button>
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={() => setCurrentMode('dev')}
                className={`px-3 py-1 rounded-md flex items-center space-x-1 text-sm transition-colors ${
                  currentMode === 'dev'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                <Zap className="w-3 h-3" />
                <span>Dev</span>
              </motion.button>
            </div>

            {/* System Health */}
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                isHealthy ? 'bg-green-400' : 'bg-red-400'
              }`} />
              <span className="text-xs text-gray-300">
                {isHealthy ? 'Healthy' : 'Issues'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar