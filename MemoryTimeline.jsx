
import React, { useState, useEffect } from 'react';

const MemoryTimeline = ({ apiUrl = 'https://memoryos.replit.app' }) => {
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  const fetchMemories = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${apiUrl}/memory?limit=10&offset=0`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setMemories(data.memories || []);
    } catch (err) {
      console.error('Failed to fetch memories:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, [apiUrl, retryCount]);

  const formatTimestamp = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
      });
    } catch {
      return timestamp;
    }
  };

  const getTypeIcon = (type) => {
    const icons = {
      'SystemUpdate': '⚙️',
      'Feature': '✨',
      'BugFix': '🐛',
      'UserInteraction': '👤',
      'API': '🔌',
      'Database': '🗄️',
      'Security': '🔒',
      'Performance': '⚡',
      'Documentation': '📚',
      'Testing': '🧪',
      'Deployment': '🚀',
      'Monitoring': '📊'
    };
    return icons[type] || '📝';
  };

  const getTypeColor = (type) => {
    const colors = {
      'SystemUpdate': 'bg-blue-100 border-blue-300 text-blue-800',
      'Feature': 'bg-green-100 border-green-300 text-green-800',
      'BugFix': 'bg-red-100 border-red-300 text-red-800',
      'UserInteraction': 'bg-purple-100 border-purple-300 text-purple-800',
      'API': 'bg-orange-100 border-orange-300 text-orange-800',
      'Database': 'bg-indigo-100 border-indigo-300 text-indigo-800',
      'Security': 'bg-yellow-100 border-yellow-300 text-yellow-800',
      'Performance': 'bg-pink-100 border-pink-300 text-pink-800',
      'Documentation': 'bg-gray-100 border-gray-300 text-gray-800',
      'Testing': 'bg-teal-100 border-teal-300 text-teal-800',
      'Deployment': 'bg-emerald-100 border-emerald-300 text-emerald-800',
      'Monitoring': 'bg-cyan-100 border-cyan-300 text-cyan-800'
    };
    return colors[type] || 'bg-gray-100 border-gray-300 text-gray-800';
  };

  const getSuccessIndicator = (success) => {
    return success ? (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
        ✅ Success
      </span>
    ) : (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
        ❌ Failed
      </span>
    );
  };

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
  };

  // Loading State
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Loading memories...</h3>
          <p className="text-gray-500">Fetching your memory timeline</p>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
            <span className="text-2xl">⚠️</span>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load memories</h3>
          <p className="text-gray-500 mb-6">Error: {error}</p>
          <button
            onClick={handleRetry}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  // Empty State
  if (memories.length === 0) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-gray-100 mb-4">
            <span className="text-2xl">📭</span>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No memory entries found</h3>
          <p className="text-gray-500 mb-6">Start using MemoryOS to see your activity timeline here</p>
          <button
            onClick={handleRetry}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            🔄 Refresh
          </button>
        </div>
      </div>
    );
  }

  // Memory Timeline
  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Memory Timeline</h1>
        <p className="text-gray-600">Recent activity from your MemoryOS system</p>
        <div className="mt-4 flex items-center justify-between">
          <span className="text-sm text-gray-500">{memories.length} entries</span>
          <button
            onClick={handleRetry}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {memories.map((memory, index) => (
          <div
            key={index}
            className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow duration-200"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{getTypeIcon(memory.type)}</span>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{memory.topic}</h3>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getTypeColor(memory.type)}`}>
                      {memory.type}
                    </span>
                    {getSuccessIndicator(memory.success)}
                  </div>
                </div>
              </div>
              <time className="text-sm text-gray-500 flex-shrink-0">
                {formatTimestamp(memory.timestamp)}
              </time>
            </div>

            {/* Content */}
            <div className="space-y-3">
              {memory.input && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-1">Input:</h4>
                  <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded border-l-4 border-blue-200">
                    {memory.input}
                  </p>
                </div>
              )}
              
              {memory.output && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-1">Output:</h4>
                  <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded border-l-4 border-green-200">
                    {memory.output}
                  </p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center space-x-4">
                  {memory.category && (
                    <span>Category: {memory.category}</span>
                  )}
                  {memory.score && (
                    <span>Score: {memory.score}/{memory.maxScore || 25}</span>
                  )}
                </div>
                {memory.tags && memory.tags.length > 0 && (
                  <div className="flex items-center space-x-1">
                    {memory.tags.slice(0, 3).map((tag, tagIndex) => (
                      <span
                        key={tagIndex}
                        className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs"
                      >
                        #{tag}
                      </span>
                    ))}
                    {memory.tags.length > 3 && (
                      <span className="text-gray-400">+{memory.tags.length - 3}</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MemoryTimeline;
