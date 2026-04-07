/**
 * Chat Interface - Agent Communication
 * 
 * Multi-turn conversation with agent selection and memory display.
 */

import React, { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

interface Agent {
  id: string;
  type: string;
  status: string;
}

// Use environment variable or relative path (nginx proxies /api to api:8000)
const API_URL = import.meta.env.VITE_API_URL || '';

const agentIcons: Record<string, string> = {
  steward: '🎯',
  alpha: '🔬',
  beta: '✅',
  coder: '💻',
  sentinel: '🛡️',
  historian: '📚',
};

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('steward');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch available agents
  useEffect(() => {
    fetch(`${API_URL}/api/agents`)
      .then(res => res.json())
      .then(data => setAgents(data.agents || []))
      .catch(console.error);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/agents/${selectedAgent}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response || data.message || 'No response',
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        role: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Sidebar - Agent Selection */}
      <div className="w-64 bg-gray-800 border-r border-gray-700 p-4">
        <h2 className="text-white font-bold mb-4 flex items-center gap-2">
          <span>🤖</span> Agents
        </h2>
        
        <div className="space-y-2">
          {agents.map(agent => (
            <button
              key={agent.id}
              onClick={() => setSelectedAgent(agent.id)}
              className={`
                w-full p-3 rounded-lg text-left transition-all
                ${selectedAgent === agent.id 
                  ? 'bg-blue-600 ring-2 ring-blue-400' 
                  : 'bg-gray-700 hover:bg-gray-600'}
              `}
            >
              <div className="flex items-center gap-2">
                <span className="text-xl">
                  {agentIcons[agent.type.toLowerCase()] || '🤖'}
                </span>
                <div>
                  <div className="text-white font-semibold text-sm">
                    {agent.type}
                  </div>
                  <div className="text-xs text-gray-400">
                    {agent.status}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {agents.length === 0 && (
          <div className="text-gray-500 text-sm text-center py-4">
            No agents available
          </div>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">
              {agentIcons[selectedAgent] || '🤖'}
            </span>
            <div>
              <h1 className="text-white font-bold">
                {selectedAgent.charAt(0).toUpperCase() + selectedAgent.slice(1)}
              </h1>
              <p className="text-gray-400 text-sm">
                {agents.find(a => a.id === selectedAgent)?.status || 'Unknown'}
              </p>
            </div>
          </div>
          
          <button
            onClick={clearChat}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded"
          >
            Clear Chat
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <div className="text-4xl mb-2">💬</div>
                <div>Start a conversation with {selectedAgent}</div>
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`
                    max-w-[70%] p-3 rounded-lg
                    ${msg.role === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : msg.role === 'system'
                      ? 'bg-red-900 text-red-200'
                      : 'bg-gray-700 text-white'}
                  `}
                >
                  <div className="text-sm mb-1 opacity-75">
                    {msg.role === 'user' ? 'You' : msg.role}
                  </div>
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                  <div className="text-xs mt-2 opacity-50">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))
          )}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-700 text-white p-3 rounded-lg">
                <div className="flex gap-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-gray-800 border-t border-gray-700 p-4">
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={2}
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-semibold rounded-lg transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
