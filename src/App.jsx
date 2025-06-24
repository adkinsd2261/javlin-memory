import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { motion } from 'framer-motion'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import JavWorkspace from './pages/JavWorkspace'
import MemoryTimeline from './pages/MemoryTimeline'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <motion.main
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="container mx-auto px-4 py-8"
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/workspace" element={<JavWorkspace />} />
            <Route path="/memory" element={<MemoryTimeline />} />
          </Routes>
        </motion.main>
      </div>
    </Router>
  )
}

export default App