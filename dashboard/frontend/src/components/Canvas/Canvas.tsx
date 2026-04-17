/**
 * Collective Canvas - Agent Visualization with ReactFlow
 *
 * Displays all agents as nodes with real-time status updates.
 * Reference: MiniMax Audit Lines 418-486 (Flowise Canvas pattern)
 */

import { useEffect, useState, useCallback } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  Connection,
  addEdge,
  XYPosition,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import AgentNode, { AgentData } from './AgentNode';
import { useConsciousnessMetrics, useSwarmHealth } from './useMetrics';
import MetricsOverlay from './MetricsOverlay';

// Import WorkflowBuilder node types
import { ToolNode, MemoryNode, DecisionNode, ConnectorNode, LLMNode } from '../WorkflowBuilder';

// Use environment variable or relative path (nginx proxies /api to api:8000)
const API_URL = import.meta.env.VITE_API_HOST || localStorage.getItem('swarm_api_host') || '';

interface AgentApiResponse {
  id: string;
  type: string;
  status: string;
  lastActivity?: string;
}

// Node type registry - maps type string to React component
// Using 'any' to bypass strict typing mismatch between WorkflowBuilder NodeProps and ReactFlow NodeTypes
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const nodeTypes: Record<string, any> = {
  agentNode: AgentNode,
  tool: ToolNode,
  memory: MemoryNode,
  decision: DecisionNode,
  connector: ConnectorNode,
  llm: LLMNode,
};

// Node palette configuration
const NODE_PALETTE = [
  {
    category: 'Agents',
    nodes: [
      { type: 'agentNode', label: 'Agent', icon: '🤖', color: '#6B7280' },
    ],
  },
  {
    category: 'Processing',
    nodes: [
      { type: 'llm', label: 'LLM', icon: '🧠', color: '#10B981' },
      { type: 'tool', label: 'Tool', icon: '🔧', color: '#3B82F6' },
    ],
  },
  {
    category: 'Data',
    nodes: [
      { type: 'memory', label: 'Memory', icon: '💾', color: '#8B5CF6' },
    ],
  },
  {
    category: 'Logic',
    nodes: [
      { type: 'decision', label: 'Decision', icon: '🔀', color: '#F59E0B' },
      { type: 'connector', label: 'Connector', icon: '🔗', color: '#6366F1' },
    ],
  },
];

const initialEdges: Edge[] = [];

export function CollectiveCanvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<AgentData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showMetrics, setShowMetrics] = useState(false);
  const [showPalette, setShowPalette] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [agentsData, setAgentsData] = useState<AgentApiResponse[]>([]);

  // Metrics hooks
  const { metrics: consciousness, loading: consciousnessLoading } = useConsciousnessMetrics();
  const swarmHealth = useSwarmHealth(agentsData);

  // Toggle metrics overlay with 'm' key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'm' || e.key === 'M') {
        setShowMetrics(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Fetch agents from API
  const fetchAgents = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/agents`);
      if (!response.ok) throw new Error('Failed to fetch agents');
      
      const data = await response.json();
      
      const agentNodes: Node<AgentData>[] = data.agents.map(
        (agent: AgentApiResponse, index: number) => ({
          id: agent.id,
          type: 'agentNode',
          position: {
            x: (index % 3) * 300 + 100,
            y: Math.floor(index / 3) * 200 + 100,
          },
          data: {
            agentId: agent.id,
            agentType: agent.type.toLowerCase() as AgentData['agentType'],
            status: agent.status as AgentData['status'],
            lastActivity: agent.lastActivity || new Date().toISOString(),
          },
        })
      );
      
      setNodes(agentNodes as Node<AgentData>[]);
      setAgentsData(data.agents);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [setNodes]);

  // Initial fetch
  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  // Poll for updates every 5 seconds
  useEffect(() => {
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, [fetchAgents]);

  // Handle node connections
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds: Edge[]) => addEdge(params, eds));
    },
    [setEdges]
  );

  // Handle adding nodes from palette
  const addNodeFromPalette = useCallback((nodeType: string, position?: XYPosition) => {
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: nodeType,
      position: position || {
        x: 100 + Math.random() * 400,
        y: 100 + Math.random() * 300,
      },
      data: {
        id: `node-${Date.now()}`,
        label: nodeType.charAt(0).toUpperCase() + nodeType.slice(1),
      },
    };
    // Type assertion needed for mixed node types (Agent + WorkflowBuilder nodes)
    setNodes((nds) => [...nds, newNode as Node<AgentData>]);
  }, [setNodes]);

  // Handle node click for selection
  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  // Handle pane click to deselect
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // Handle delete key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedNode && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
          setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
          setEdges((eds) => eds.filter((ed) => ed.source !== selectedNode.id && ed.target !== selectedNode.id));
          setSelectedNode(null);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNode, setNodes, setEdges]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-white text-xl">Loading swarm...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-red-500 text-xl">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen bg-gray-900 relative">
      {/* Node Palette Panel */}
      {showPalette && (
        <div className="absolute top-16 left-4 z-20 w-56 bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-3 max-h-[70vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-semibold text-sm">Node Palette</h3>
            <button
              onClick={() => setShowPalette(false)}
              className="text-gray-400 hover:text-white text-xs"
            >
              ✕
            </button>
          </div>
          {NODE_PALETTE.map((category) => (
            <div key={category.category} className="mb-3">
              <div className="text-gray-400 text-xs font-semibold mb-1 uppercase tracking-wide">
                {category.category}
              </div>
              <div className="grid grid-cols-2 gap-1">
                {category.nodes.map((nodeConfig) => (
                  <button
                    key={nodeConfig.type}
                    onClick={() => addNodeFromPalette(nodeConfig.type)}
                    className="flex items-center gap-2 p-2 bg-gray-700 hover:bg-gray-600 rounded transition-colors text-left"
                    style={{ borderLeft: `3px solid ${nodeConfig.color}` }}
                  >
                    <span className="text-lg">{nodeConfig.icon}</span>
                    <span className="text-xs text-gray-300">{nodeConfig.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Toolbar */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 flex items-center gap-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-2">
        {/* Toggle Palette Button */}
        <button
          onClick={() => setShowPalette(prev => !prev)}
          className={`p-2 rounded-lg transition-colors ${
            showPalette ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400 hover:text-white'
          }`}
          title="Toggle Node Palette"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        
        {/* Metrics Toggle */}
        <button
          onClick={() => setShowMetrics(prev => !prev)}
          className={`p-2 rounded-lg transition-colors ${
            showMetrics ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400 hover:text-white'
          }`}
          title="Toggle Metrics (M)"
        >
          📊
        </button>

        {/* Clear Canvas */}
        <button
          onClick={() => {
            setNodes([]);
            setEdges([]);
            setSelectedNode(null);
          }}
          disabled={nodes.length === 0}
          className="p-2 bg-gray-700 hover:bg-red-900 rounded-lg text-gray-400 hover:text-red-400 transition-colors disabled:opacity-50"
          title="Clear Canvas"
        >
          🗑️
        </button>
      </div>

      {/* Selected Node Info */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 z-20 bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-3">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm">Selected:</span>
            <span className="text-white font-medium">{selectedNode.type}</span>
            <span className="text-gray-500 text-xs">({selectedNode.id})</span>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-400 hover:text-white ml-2"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        fitView
        className="bg-gray-900"
        deleteKeyCode="Delete"
      >
        <Background color="#374151" gap={20} />
        <Controls className="bg-gray-800 border-gray-700" />
        <MiniMap
          nodeColor={(node: Node) => {
            const data = node.data as AgentData;
            const status = data?.status;
            switch (status) {
              case 'idle': return '#6B7280';
              case 'thinking': return '#3B82F6';
              case 'acting': return '#22C55E';
              case 'error': return '#EF4444';
              default: return '#6B7280';
            }
          }}
          className="bg-gray-800 border-gray-700"
          maskColor="rgba(0, 0, 0, 0.5)"
        />
      </ReactFlow>
      {showMetrics && (
        <MetricsOverlay
          consciousness={consciousness}
          swarmHealth={swarmHealth}
          metricsLoading={consciousnessLoading}
          onClose={() => setShowMetrics(false)}
        />
      )}
    </div>
  );
}

export default CollectiveCanvas;
