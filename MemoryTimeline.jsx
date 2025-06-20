
import React, { useState, useEffect } from 'react';

const MemoryTimeline = ({ apiBaseUrl = '', limit = 10, offset = 0 }) => {
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMemories();
  }, [limit, offset]);

  const fetchMemories = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiBaseUrl}/memory?limit=${limit}&page=${Math.floor(offset / limit) + 1}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setMemories(data.memories || []);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching memories:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return {
        date: date.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric', 
          year: 'numeric' 
        }),
        time: date.toLocaleTimeString('en-US', { 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: true 
        })
      };
    } catch {
      return { date: 'Unknown', time: '' };
    }
  };

  const getTypeIcon = (type) => {
    const iconMap = {
      'SystemUpdate': '⚙️',
      'Feature': '✨',
      'BugFix': '🐛',
      'Interaction': '💬',
      'Note': '📝',
      'Task': '✅',
      'Error': '❌',
      'Success': '🎉',
      'Warning': '⚠️',
      'Info': 'ℹ️'
    };
    return iconMap[type] || '📋';
  };

  const getTypeColor = (type, success) => {
    if (success === false) return 'border-red-200 bg-red-50';
    
    const colorMap = {
      'SystemUpdate': 'border-blue-200 bg-blue-50',
      'Feature': 'border-purple-200 bg-purple-50',
      'BugFix': 'border-orange-200 bg-orange-50',
      'Interaction': 'border-green-200 bg-green-50',
      'Note': 'border-gray-200 bg-gray-50',
      'Task': 'border-indigo-200 bg-indigo-50',
      'Error': 'border-red-200 bg-red-50',
      'Success': 'border-green-200 bg-green-50',
      'Warning': 'border-yellow-200 bg-yellow-50',
      'Info': 'border-cyan-200 bg-cyan-50'
    };
    return colorMap[type] || 'border-gray-200 bg-gray-50';
  };

  const getSuccessIndicator = (success) => {
    if (success === true) return <span className="text-green-500 text-sm">✓ Success</span>;
    if (success === false) return <span className="text-red-500 text-sm">✗ Failed</span>;
    return null;
  };

  const getScoreDisplay = (score, maxScore) => {
    if (!score && !maxScore) return null;
    const percentage = maxScore ? (score / maxScore) * 100 : 0;
    const scoreColor = percentage >= 80 ? 'text-green-600' : 
                      percentage >= 60 ? 'text-yellow-600' : 'text-red-600';
    
    return (
      <div className="flex items-center gap-2 text-sm">
        <span className={scoreColor}>
          {score || 0}/{maxScore || 25}
        </span>
        <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className={`h-full ${percentage >= 80 ? 'bg-green-500' : 
                               percentage >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2 text-gray-600">Loading memories...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <h3 className="font-semibold">Error loading memories</h3>
        <p className="text-sm mt-1">{error}</p>
        <button 
          onClick={fetchMemories}
          className="mt-2 px-3 py-1 bg-red-100 hover:bg-red-200 rounded text-sm transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!memories || memories.length === 0) {
    return (
      <div className="text-center p-8 text-gray-500">
        <div className="text-4xl mb-2">🧠</div>
        <h3 className="text-lg font-medium">No memories found</h3>
        <p className="text-sm">Your memory timeline will appear here once you start adding entries.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="text-2xl">🧠</div>
        <h2 className="text-2xl font-bold text-gray-800">Memory Timeline</h2>
        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm font-medium">
          {memories.length} entries
        </span>
      </div>

      <div className="space-y-4">
        {memories.map((memory, index) => {
          const { date, time } = formatTimestamp(memory.timestamp);
          const typeColor = getTypeColor(memory.type, memory.success);
          
          return (
            <div 
              key={memory.timestamp || index}
              className={`border-l-4 pl-6 pb-6 relative ${
                index !== memories.length - 1 ? 'border-l-gray-200' : 'border-l-transparent'
              }`}
            >
              {/* Timeline dot */}
              <div className="absolute left-0 top-0 w-3 h-3 bg-blue-500 rounded-full transform -translate-x-2"></div>
              
              {/* Memory card */}
              <div className={`border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow ${typeColor}`}>
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{getTypeIcon(memory.type)}</span>
                    <div>
                      <h3 className="font-semibold text-gray-800 text-lg">{memory.topic}</h3>
                      <div className="flex items-center gap-3 text-sm text-gray-600">
                        <span className="font-medium">{memory.type}</span>
                        <span>•</span>
                        <span>{memory.category}</span>
                        {getSuccessIndicator(memory.success)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right text-sm text-gray-500">
                    <div className="font-medium">{date}</div>
                    <div>{time}</div>
                  </div>
                </div>

                {/* Content */}
                <div className="space-y-3">
                  {memory.input && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Input:</h4>
                      <p className="text-gray-800 bg-white/70 rounded p-2 text-sm">{memory.input}</p>
                    </div>
                  )}
                  
                  {memory.output && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Output:</h4>
                      <p className="text-gray-800 bg-white/70 rounded p-2 text-sm">{memory.output}</p>
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between mt-4 pt-3 border-t border-white/50">
                  <div className="flex items-center gap-4">
                    {getScoreDisplay(memory.score, memory.maxScore)}
                    
                    {memory.tags && memory.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {memory.tags.slice(0, 3).map((tag, tagIndex) => (
                          <span 
                            key={tagIndex}
                            className="px-2 py-1 bg-white/70 text-gray-700 rounded-full text-xs"
                          >
                            #{tag}
                          </span>
                        ))}
                        {memory.tags.length > 3 && (
                          <span className="px-2 py-1 bg-white/70 text-gray-500 rounded-full text-xs">
                            +{memory.tags.length - 3} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {memory.reviewed && (
                    <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                      ✓ Reviewed
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Refresh button */}
      <div className="mt-6 text-center">
        <button 
          onClick={fetchMemories}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
        >
          Refresh Timeline
        </button>
      </div>
    </div>
  );
};

export default MemoryTimeline;
