/**
 * A2A Communication Tracker
 * 
 * Real-time dashboard for monitoring NATS-based agent-to-agent communication.
 * Visualizes agent chatter, filters by Agent ID, and shows task & resource monitoring.
 * 
 * Features:
 * - Real-time NATS message interception visualization
 * - Filter by Agent ID for internal monologue view
 * - Task & resource monitoring (active workflows, memory, token consumption)
 * - Message flow graph
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';

// Types
interface A2AMessage {
  id: string;
  timestamp: string;
  from: string;
  to: string;
  subject: string;
  type: 'task' | 'response' | 'broadcast' | 'heartbeat' | 'consensus';
  payload: Record<string, unknown>;
  latencyMs: number;
  status: 'sent' | 'delivered' | 'failed' | 'pending';
}

interface AgentActivity {
  agentId: string;
  agentName: string;
  messagesSent: number;
  messagesReceived: number;
  lastActivity: string;
  status: 'active' | 'idle' | 'error' | 'offline';
  tasksCompleted: number;
  tasksPending: number;
  memoryUsage: number;
  tokenUsage: number;
}

interface WorkflowStats {
  activeWorkflows: number;
  completedWorkflows: number;
  failedWorkflows: number;
  avgDuration: number;
}

interface ResourceStats {
  totalTokens: number;
  avgMemoryUsage: number;
  activeConnections: number;
  natsQueueDepth: number;
}

interface A2ATrackerProps {
  natsUrl?: string;
  refreshInterval?: number;
  maxMessages?: number;
}

// Demo data generators
// NOTE: Math.random() is used here for demo/mock data generation only.
// This is NOT security-critical - these functions generate fake observable data
// for the dashboard demo mode. Real agent-to-agent communication uses proper
// UUIDs and authentication. See docs/security/S05_TYPESCRIPT_PRNG_REVIEW.md

const AGENT_IDS = [
  'steward', 'alpha', 'beta', 'charlie', 'historian',
  'maker', 'taker', 'executor', 'validator', 'researcher',
  'coder', 'reviewer', 'tester', 'deployer', 'documenter'
];

const AGENT_NAMES: Record<string, string> = {
  steward: 'Steward', alpha: 'Alpha', beta: 'Beta', charlie: 'Charlie', historian: 'Historian',
  maker: 'MAKER', taker: 'TAKER', executor: 'Executor', validator: 'Validator', researcher: 'Researcher',
  coder: 'Coder', reviewer: 'Reviewer', tester: 'Tester', deployer: 'Deployer', documenter: 'Documenter'
};

const MESSAGE_SUBJECTS = [
  'task_assignment', 'task_completion', 'status_update', 'consensus_request',
  'memory_query', 'memory_update', 'health_check', 'resource_request',
  'workflow_status', 'error_report', 'delegate_task'
];

function generateRandomMessage(): A2AMessage {
  const from = AGENT_IDS[Math.floor(Math.random() * AGENT_IDS.length)];
  let to = AGENT_IDS[Math.floor(Math.random() * AGENT_IDS.length)];
  while (to === from) {
    to = AGENT_IDS[Math.floor(Math.random() * AGENT_IDS.length)];
  }

  return {
    id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date().toISOString(),
    from,
    to,
    subject: MESSAGE_SUBJECTS[Math.floor(Math.random() * MESSAGE_SUBJECTS.length)],
    type: ['task', 'response', 'broadcast', 'heartbeat', 'consensus'][Math.floor(Math.random() * 5)] as A2AMessage['type'],
    payload: {
      taskSample: Math.random(),
    },
    latencyMs: Math.floor(Math.random() * 500) + 10,
    status: ['sent', 'delivered', 'failed', 'pending'][Math.floor(Math.random() * 4)] as A2AMessage['status'],
  };
}

function generateAgentActivity(): AgentActivity[] {
  return AGENT_IDS.map(agentId => ({
    agentId,
    agentName: AGENT_NAMES[agentId] || agentId,
    messagesSent: Math.floor(Math.random() * 100),
    messagesReceived: Math.floor(Math.random() * 100),
    lastActivity: new Date(Date.now() - Math.random() * 60000).toISOString(),
    status: ['active', 'idle', 'error', 'offline'][Math.floor(Math.random() * 4)] as AgentActivity['status'],
    tasksCompleted: Math.floor(Math.random() * 20),
    tasksPending: Math.floor(Math.random() * 5),
    memoryUsage: Math.floor(Math.random() * 80) + 10,
    tokenUsage: Math.floor(Math.random() * 10000),
  }));
}

// Components
const MessageTimeline: React.FC<{ messages: A2AMessage[]; filterAgent?: string }> = ({ messages, filterAgent }) => {
  const filteredMessages = filterAgent
    ? messages.filter(m => m.from === filterAgent || m.to === filterAgent)
    : messages;

  const getTypeColor = (type: A2AMessage['type']) => {
    switch (type) {
      case 'task': return 'bg-blue-500';
      case 'response': return 'bg-green-500';
      case 'broadcast': return 'bg-purple-500';
      case 'heartbeat': return 'bg-gray-500';
      case 'consensus': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: A2AMessage['status']) => {
    switch (status) {
      case 'sent': return '→';
      case 'delivered': return '✓';
      case 'failed': return '✗';
      case 'pending': return '⏳';
    }
  };

  return (
    <div className="space-y-2 max-h-96 overflow-y-auto">
      {filteredMessages.length === 0 ? (
        <div className="text-gray-500 text-center py-8">No messages yet</div>
      ) : (
        filteredMessages.slice(-50).reverse().map((msg) => (
          <div
            key={msg.id}
            className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg hover:bg-gray-750 transition-colors"
          >
            <div className={`w-2 h-2 rounded-full ${getTypeColor(msg.type)}`} title={msg.type} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-mono text-blue-400">{msg.from}</span>
                <span className="text-gray-500">{getStatusIcon(msg.status)}</span>
                <span className="font-mono text-green-400">{msg.to}</span>
              </div>
              <div className="text-xs text-gray-500 truncate">{msg.subject}</div>
            </div>
            <div className="text-xs text-gray-400 whitespace-nowrap">
              {msg.latencyMs}ms
            </div>
            <div className="text-xs text-gray-500 whitespace-nowrap">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))
      )}
    </div>
  );
};

const AgentActivityList: React.FC<{
  agents: AgentActivity[];
  selectedAgent: string | null;
  onSelectAgent: (id: string | null) => void;
}> = ({ agents, selectedAgent, onSelectAgent }) => {
  const getStatusColor = (status: AgentActivity['status']) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'idle': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      case 'offline': return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-2 max-h-80 overflow-y-auto">
      {agents.map((agent) => (
        <div
          key={agent.agentId}
          onClick={() => onSelectAgent(selectedAgent === agent.agentId ? null : agent.agentId)}
          className={`p-3 rounded-lg cursor-pointer transition-colors ${
            selectedAgent === agent.agentId ? 'bg-blue-900/30 border border-blue-500' : 'bg-gray-800 hover:bg-gray-750'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
              <span className="font-medium text-white">{agent.agentName}</span>
              <span className="text-xs text-gray-500 font-mono">({agent.agentId})</span>
            </div>
            <span className="text-xs text-gray-400">
              {agent.messagesSent + agent.messagesReceived} msgs
            </span>
          </div>
          <div className="grid grid-cols-4 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Sent:</span>
              <span className="ml-1 text-blue-400">{agent.messagesSent}</span>
            </div>
            <div>
              <span className="text-gray-500">Recv:</span>
              <span className="ml-1 text-green-400">{agent.messagesReceived}</span>
            </div>
            <div>
              <span className="text-gray-500">Mem:</span>
              <span className="ml-1 text-purple-400">{agent.memoryUsage}%</span>
            </div>
            <div>
              <span className="text-gray-500">Tokens:</span>
              <span className="ml-1 text-yellow-400">{agent.tokenUsage}</span>
            </div>
          </div>
          {agent.tasksPending > 0 && (
            <div className="mt-2 text-xs text-orange-400">
              {agent.tasksPending} pending tasks
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

const MessageFlowGraph: React.FC<{ messages: A2AMessage[] }> = ({ messages }) => {
  const [connections, setConnections] = useState<Record<string, number>>({});

  useEffect(() => {
    const conns: Record<string, number> = {};
    messages.slice(-100).forEach((msg) => {
      const key = `${msg.from}→${msg.to}`;
      conns[key] = (conns[key] || 0) + 1;
    });
    setConnections(conns);
  }, [messages]);

  const topConnections = Object.entries(connections)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  return (
    <div className="space-y-2">
      {topConnections.length === 0 ? (
        <div className="text-gray-500 text-center py-8">No connections yet</div>
      ) : (
        topConnections.map(([conn, count]) => (
          <div key={conn} className="flex items-center gap-3">
            <div className="flex-1 flex items-center gap-2">
              <span className="font-mono text-sm text-blue-400">{conn.split('→')[0]}</span>
              <span className="text-gray-500">→</span>
              <span className="font-mono text-sm text-green-400">{conn.split('→')[1]}</span>
            </div>
            <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 rounded-full"
                style={{ width: `${Math.min(100, (Number(count) / 10) * 100)}%` }}
              />
            </div>
            <span className="text-xs text-gray-400 w-8 text-right">{count}</span>
          </div>
        ))
      )}
    </div>
  );
};

const ResourceMonitor: React.FC<{ resources: ResourceStats }> = ({ resources }) => (
  <div className="grid grid-cols-2 gap-4">
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-xs text-gray-400 uppercase mb-1">Total Tokens</div>
      <div className="text-2xl font-bold text-blue-400">
        {resources.totalTokens.toLocaleString()}
      </div>
    </div>
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-xs text-gray-400 uppercase mb-1">Avg Memory</div>
      <div className="text-2xl font-bold text-purple-400">
        {resources.avgMemoryUsage.toFixed(1)}%
      </div>
    </div>
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-xs text-gray-400 uppercase mb-1">Active Connections</div>
      <div className="text-2xl font-bold text-green-400">
        {resources.activeConnections}
      </div>
    </div>
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-xs text-gray-400 uppercase mb-1">NATS Queue</div>
      <div className="text-2xl font-bold text-yellow-400">
        {resources.natsQueueDepth}
      </div>
    </div>
  </div>
);

const WorkflowStatsPanel: React.FC<{ stats: WorkflowStats }> = ({ stats }) => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-xs text-gray-400 uppercase mb-1">Active</div>
      <div className="text-2xl font-bold text-blue-400">{stats.activeWorkflows}</div>
    </div>
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-xs text-gray-400 uppercase mb-1">Completed</div>
      <div className="text-2xl font-bold text-green-400">{stats.completedWorkflows}</div>
    </div>
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-xs text-gray-400 uppercase mb-1">Failed</div>
      <div className="text-2xl font-bold text-red-400">{stats.failedWorkflows}</div>
    </div>
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-xs text-gray-400 uppercase mb-1">Avg Duration</div>
      <div className="text-2xl font-bold text-yellow-400">{stats.avgDuration.toFixed(0)}s</div>
    </div>
  </div>
);

// Main Component
export function A2ATracker({
  natsUrl = 'nats://localhost:4222',
  refreshInterval = 2000,
  maxMessages = 200,
}: A2ATrackerProps) {
  const [messages, setMessages] = useState<A2AMessage[]>([]);
  const [agentActivity, setAgentActivity] = useState<AgentActivity[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'messages' | 'agents' | 'flows' | 'resources'>('messages');
  const [isConnected, setIsConnected] = useState(false);
  const [stats, setStats] = useState<ResourceStats>({
    totalTokens: 0,
    avgMemoryUsage: 0,
    activeConnections: 0,
    natsQueueDepth: 0,
  });
  const [workflowStats, setWorkflowStats] = useState<WorkflowStats>({
    activeWorkflows: 0,
    completedWorkflows: 0,
    failedWorkflows: 0,
    avgDuration: 0,
  });
  const messageId = useRef(0);

  // Simulate NATS connection and message streaming
  useEffect(() => {
    // Simulate connection
    const connectTimeout = setTimeout(() => {
      setIsConnected(true);
    }, 1000);

    // Initialize with some messages
    const initialMessages = Array.from({ length: 20 }, generateRandomMessage);
    setMessages(initialMessages);
    setAgentActivity(generateAgentActivity());

    // Stream new messages
    const messageInterval = setInterval(() => {
      const newMessage = generateRandomMessage();
      setMessages((prev) => {
        const updated = [...prev, newMessage];
        return updated.slice(-maxMessages);
      });
    }, refreshInterval);

    // Update agent activity periodically
    const activityInterval = setInterval(() => {
      setAgentActivity(generateAgentActivity());
    }, 5000);

    // Update stats periodically
    const statsInterval = setInterval(() => {
      setStats({
        totalTokens: Math.floor(Math.random() * 100000) + 50000,
        avgMemoryUsage: Math.random() * 30 + 40,
        activeConnections: Math.floor(Math.random() * 20) + 5,
        natsQueueDepth: Math.floor(Math.random() * 100),
      });
      setWorkflowStats({
        activeWorkflows: Math.floor(Math.random() * 10),
        completedWorkflows: Math.floor(Math.random() * 100) + 50,
        failedWorkflows: Math.floor(Math.random() * 5),
        avgDuration: Math.random() * 60 + 30,
      });
    }, 3000);

    return () => {
      clearTimeout(connectTimeout);
      clearInterval(messageInterval);
      clearInterval(activityInterval);
      clearInterval(statsInterval);
    };
  }, [refreshInterval, maxMessages]);

  // Filter messages for selected agent's "internal monologue"
  const internalMonologue = selectedAgent
    ? messages.filter((m) => m.from === selectedAgent || m.to === selectedAgent)
    : [];

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold text-white">A2A Communication Tracker</h2>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
            <span className="text-sm text-gray-400">
              {isConnected ? `Connected to ${natsUrl}` : 'Connecting...'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">
            {messages.length} messages
          </span>
          <span className="text-sm text-gray-400">
            {agentActivity.filter((a) => a.status === 'active').length} active agents
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-700">
        {(['messages', 'agents', 'flows', 'resources'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-[2px] ${
              activeTab === tab
                ? 'text-blue-400 border-blue-400'
                : 'text-gray-400 border-transparent hover:text-white'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Agent Filter (shown when agent selected) */}
      {selectedAgent && (
        <div className="mb-4 p-3 bg-blue-900/30 border border-blue-500/50 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-blue-400">Filtering by:</span>
            <span className="font-mono text-white">{selectedAgent}</span>
            <span className="text-sm text-gray-400">
              ({internalMonologue.length} messages)
            </span>
          </div>
          <button
            onClick={() => setSelectedAgent(null)}
            className="text-sm text-gray-400 hover:text-white"
          >
            Clear filter
          </button>
        </div>
      )}

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'messages' && (
          <MessageTimeline messages={messages} filterAgent={selectedAgent || undefined} />
        )}

        {activeTab === 'agents' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3">Agent Activity</h3>
              <AgentActivityList
                agents={agentActivity}
                selectedAgent={selectedAgent}
                onSelectAgent={setSelectedAgent}
              />
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3">Workflow Statistics</h3>
              <WorkflowStatsPanel stats={workflowStats} />
              <h3 className="text-sm font-medium text-gray-400 mb-3 mt-6">Resource Usage</h3>
              <ResourceMonitor resources={stats} />
            </div>
          </div>
        )}

        {activeTab === 'flows' && (
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">Top Communication Flows</h3>
            <MessageFlowGraph messages={messages} />
          </div>
        )}

        {activeTab === 'resources' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3">Resource Statistics</h3>
              <ResourceMonitor resources={stats} />
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3">Workflow Statistics</h3>
              <WorkflowStatsPanel stats={workflowStats} />
            </div>
          </div>
        )}
      </div>

      {/* Quick Stats Footer */}
      <div className="mt-6 pt-4 border-t border-gray-700 flex items-center justify-between text-sm">
        <div className="flex items-center gap-6">
          <div>
            <span className="text-gray-500">Messages/sec:</span>
            <span className="ml-2 text-white">{(1000 / refreshInterval).toFixed(1)}</span>
          </div>
          <div>
            <span className="text-gray-500">Total Throughput:</span>
            <span className="ml-2 text-white">
              {messages.reduce((acc, m) => acc + (m.payload && Object.keys(m.payload).length > 0 ? 100 : 50), 0).toLocaleString()} bytes
            </span>
          </div>
          <div>
            <span className="text-gray-500">Avg Latency:</span>
            <span className="ml-2 text-white">
              {messages.length > 0
                ? (messages.reduce((acc, m) => acc + m.latencyMs, 0) / messages.length).toFixed(0)
                : 0}ms
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-500">NATS Status:</span>
          <span className={`${isConnected ? 'text-green-400' : 'text-red-400'}`}>
            {isConnected ? 'Operational' : 'Disconnected'}
          </span>
        </div>
      </div>
    </div>
  );
}

export default A2ATracker;
