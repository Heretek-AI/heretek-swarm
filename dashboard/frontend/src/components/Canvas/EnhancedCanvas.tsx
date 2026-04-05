/**
 * Enhanced Collective Canvas - Agent Visualization with ReactFlow
 *
 * Features:
 * - Drag-and-drop node palette with multiple node types
 * - Workflow execution visualization
 * - Real-time status updates
 * - Save/load workflow functionality
 * - Agent connections and handoff visualization
 *
 * Reference: Flowise visual builder pattern
 */

import React, { useEffect, useState, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  Connection,
  addEdge,
  Panel,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { AgentNode, AgentData } from './AgentNode';
import type { AgentNode, TriadNode, HistorianNode, ToolNode, MemoryNode, RAGNode, ConditionNode, LoopNode, HandoffNode, MergeNode, DiscordNode, TelegramNode, WebhookNode } from '../types/reactflow';

const API_URL = import.meta.env.VITE_API_URL;
if (!API_URL) {
  throw new Error('VITE_API_URL environment variable is required');
}

// =============================================================================
// Type Definitions
// =============================================================================

interface AgentApiResponse {
  id: string;
  type: string;
  status: string;
  lastActivity?: string;
}

interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
}

interface Workflow {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: Edge[];
  createdAt: string;
  updatedAt: string;
}

interface ExecutionState {
  status: 'idle' | 'running' | 'completed' | 'error';
  currentNode?: string;
  message?: string;
  progress: number;
}

// =============================================================================
// Node Types Configuration
// =============================================================================

const NODE_TYPES = {
  agentNode: 'agentNode',
  triadNode: 'triadNode',
  historianNode: 'historianNode',
  toolNode: 'toolNode',
  memoryNode: 'memoryNode',
  ragNode: 'ragNode',
  conditionNode: 'conditionNode',
  loopNode: 'loopNode',
  handoffNode: 'handoffNode',
  mergeNode: 'mergeNode',
  discordNode: 'discordNode',
  telegramNode: 'telegramNode',
  webhookNode: 'webhookNode',
} as const;

const NODE_COLORS = {
  agent: '#6B7280',
  triad: '#22C55E',
  historian: '#3B82F6',
  tool: '#10B981',
  memory: '#8B5CF6',
  rag: '#F59E0B',
  condition: '#FBBF24',
  loop: '#9CA3AF',
  handoff: '#EC4899',
  merge: '#8B5CF6',
  discord: '#5865F2',
  telegram: '#229ED9',
  webhook: '#6366F1',
} as const;

// =============================================================================
// Node Palette Configuration
// =============================================================================

const NODE_PALETTE = [
  // Agent Nodes
  {
    category: 'Agents',
    nodes: [
      { type: 'agentNode', label: 'Agent', icon: '🤖' },
      { type: 'triadNode', label: 'Triad', icon: '🧠' },
      { type: 'historianNode', label: 'Historian', icon: '📚' },
    ],
  },
  {
    category: 'Tools',
    nodes: [
      { type: 'toolNode', label: 'Tool', icon: '🔧' },
      { type: 'memoryNode', label: 'Memory', icon: '💾' },
      { type: 'ragNode', label: 'RAG', icon: '🔍' },
    ],
  },
  {
    category: 'Flow Control',
    nodes: [
      { type: 'conditionNode', label: 'Condition', icon: '🔀' },
      { type: 'loopNode', label: 'Loop', icon: '🔄' },
      { type: 'handoffNode', label: 'Handoff', icon: '🔄' },
      { type: 'mergeNode', label: 'Merge', icon: '🔀' },
    ],
  },
  {
    category: 'Integrations',
    nodes: [
      { type: 'discordNode', label: 'Discord', icon: '💬' },
      { type: 'telegramNode', label: 'Telegram', icon: '✈️' },
      { type: 'webhookNode', label: 'Webhook', icon: '🔗' },
    ],
  },
];

// =============================================================================
// Enhanced Canvas Component
// =============================================================================

export function EnhancedCanvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [currentWorkflow, setCurrentWorkflow] = useState<Workflow | null>(null);
  const [executionState, setExecutionState] = useState<ExecutionState>({
    status: 'idle',
    progress: 0,
  });
  const [isExecuting, setIsExecuting] = useState(false);
  const [showPalette, setShowPalette] = useState(true);
  const [savedWorkflows, setSavedWorkflows] = useState<Workflow[]>([]);
  const [showExecution, setShowExecution] = useState(false);

  // Fetch agents
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
            x: (index % 4) * 300 + 100,
            y: Math.floor(index / 4) * 200 + 100,
          },
          data: {
            agentId: agent.id,
            agentType: agent.type.toLowerCase() as AgentData['agentType'],
            status: agent.status as AgentData['status'],
            lastActivity: agent.lastActivity || new Date().toISOString(),
          },
        })
      );
      
      setNodes(agentNodes);
    } catch (err) {
      console.error('Failed to fetch agents:', err);
    }
  }, [setNodes]);

  // Save workflow
  const saveWorkflow = useCallback(async (workflow: Workflow) => {
    try {
      const response = await fetch(`${API_URL}/api/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workflow),
      });
      
      if (!response.ok) throw new Error('Failed to save workflow');
      
      const saved = await response.json();
      setSavedWorkflows([...savedWorkflows, saved]);
      setCurrentWorkflow(saved);
    } catch (err) {
      console.error('Failed to save workflow:', err);
    }
  }, [savedWorkflows, setCurrentWorkflow]);

  // Load workflow
  const loadWorkflow = useCallback(async (workflowId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/workflows/${workflowId}`);
      if (!response.ok) throw new Error('Failed to load workflow');
      
      const workflow = await response.json();
      setCurrentWorkflow(workflow);
      setNodes(workflow.nodes);
      setEdges(workflow.edges);
    } catch (err) {
      console.error('Failed to load workflow:', err);
    }
  }, [setCurrentWorkflow, setNodes, setEdges]);

  // Execute workflow
  const executeWorkflow = useCallback(async () => {
    if (!currentWorkflow) return;
    
    setIsExecuting(true);
    setExecutionState({ status: 'running', progress: 0 });

    try {
      const response = await fetch(`${API_URL}/api/workflows/${currentWorkflow.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nodes: currentWorkflow.nodes,
          edges: currentWorkflow.edges,
        }),
      });

      if (!response.ok) throw new Error('Failed to execute workflow');
      
      const result = await response.json();
      
      // Simulate execution with progress updates
      for (let i = 0; i < currentWorkflow.nodes.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 500));
        setExecutionState({
          status: 'running',
          currentNode: currentWorkflow.nodes[i].id,
          progress: (i + 1) / currentWorkflow.nodes.length * 100,
          message: `Executing node ${currentWorkflow.nodes[i].id}`,
        });
      }

      setExecutionState({
        status: 'completed',
        progress: 100,
        message: 'Workflow execution completed',
      });
    } catch (err) {
      setExecutionState({
        status: 'error',
        message: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setIsExecuting(false);
      setTimeout(() => setShowExecution(false), 2000);
    }
  }, [currentWorkflow, setExecutionState, setShowExecution]);

  // Create node from palette
  const addNode = useCallback((type: string, position: Position) => {
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type,
      position,
      data: { isNew: true },
    };
    
    setNodes((nds) => [...nds, newNode]);
    return newNode;
  }, [setNodes]);

  // Handle node connections
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge(params, eds));
    },
    [setEdges]
  );

  // Handle node selection
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchAgents();
  }, []);

  // Poll for updates
  useEffect(() => {
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, [fetchAgents]);

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
    <div className="w-full h-screen flex">
      {/* Node Palette */}
      {showPalette && (
        <div className="w-64 bg-gray-800 border-r border-gray-700 p-4 overflow-y-auto">
          <div className="text-white font-bold mb-4">Node Palette</div>
          {NODE_PALETTE.map((category) => (
            <div key={category.category} className="mb-4">
              <div className="text-gray-400 text-sm font-semibold mb-2">
                {category.category}
              </div>
              <div className="grid grid-cols-2 gap-2">
                {category.nodes.map((nodeConfig) => (
                  <button
                    key={nodeConfig.type}
                    draggable
                    onDragStart={(event) => {
                      const type = nodeConfig.type;
                      const position = {
                        x: event.clientX - 100,
                        y: event.clientY - 50,
                      };
                      addNode(type, position);
                    }}
                    className="flex items-center gap-2 p-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                    title={nodeConfig.label}
                  >
                    <span className="text-2xl">{nodeConfig.icon}</span>
                    <span className="text-sm">{nodeConfig.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Toolbar */}
      <div className="flex-1 bg-gray-800 border-r border-gray-700 p-4">
        <button
          onClick={() => setShowPalette(!showPalette)}
          className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          title="Toggle Node Palette"
        >
          {showPalette ? '📋' : '📋'}
        </button>
        <button
          onClick={() => {
            if (currentWorkflow) {
              saveWorkflow(currentWorkflow);
            } else {
              const newWorkflow: Workflow = {
                id: `workflow-${Date.now()}`,
                name: `Workflow ${savedWorkflows.length + 1}`,
                description: 'New workflow',
                nodes,
                edges,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
              };
              setCurrentWorkflow(newWorkflow);
            }
          }}
          disabled={!nodes.length}
          className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Save Workflow"
        >
          💾
        </button>
        <button
          onClick={() => {
            if (currentWorkflow) {
              setCurrentWorkflow(null);
              setNodes([]);
              setEdges([]);
            } else {
              setCurrentWorkflow(null);
            }
          }}
          disabled={!currentWorkflow}
          className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Clear Workflow"
        >
          🗑️
        </button>
        <button
          onClick={() => setShowExecution(!showExecution)}
          disabled={!currentWorkflow || nodes.length === 0}
          className="p-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Execute Workflow"
        >
          ▶️
        </button>
      </div>

      {/* ReactFlow Canvas */}
      <div className="flex-1 bg-gray-900">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={{
            agentNode: AgentNode,
            triadNode: AgentNode,
            historianNode: AgentNode,
            toolNode: AgentNode,
            memoryNode: AgentNode,
            ragNode: AgentNode,
            conditionNode: AgentNode,
            loopNode: AgentNode,
            handoffNode: AgentNode,
            mergeNode: AgentNode,
            discordNode: AgentNode,
            telegramNode: AgentNode,
            webhookNode: AgentNode,
          }}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onNodeDragStop={(event, node) => {
            // Update node position
            setNodes((nds) =>
              nds.map((n) =>
                n.id === node.id ? { ...n, position: node.position } : n
              )
            );
          }}
          fitView
          className="bg-gray-900"
        >
          <Background color="#1a1a2a" gap={20} />
          <Controls className="bg-gray-800 border-gray-700" />
          <MiniMap
            nodeColor={(node) => {
              const status = (node.data as AgentData)?.status;
              switch (status) {
                case 'idle': return NODE_COLORS.agent;
                case 'thinking': return NODE_COLORS.triad;
                case 'acting': return NODE_COLORS.historian;
                default: return '#6B7280';
              }
            }}
            className="bg-gray-800 border-gray-700"
            maskColor="rgba(0, 0, 0, 0.5)"
          />
        </ReactFlow>

        {/* Workflow Execution Panel */}
        {showExecution && (
          <div className="absolute top-4 right-4 w-96 bg-gray-800 border-l border-gray-700 rounded-lg p-4 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white text-lg font-bold">Workflow Execution</h3>
              <button
                onClick={() => setShowExecution(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            {executionState.status === 'running' && (
              <div className="mb-4">
                <div className="text-gray-400 text-sm mb-1">
                  Status: <span className="text-green-400 font-semibold">Running</span>
                </div>
                {executionState.currentNode && (
                  <div className="text-gray-400 text-sm mb-1">
                    Current Node: {executionState.currentNode}
                  </div>
                )}
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${executionState.progress}%` }}
                  />
                </div>
                <div className="text-gray-400 text-sm mt-1">
                  {executionState.message}
                </div>
              </div>
            )}
            
            {executionState.status === 'completed' && (
              <div className="text-center">
                <div className="text-6xl mb-4">✅</div>
                <div className="text-white text-lg">Workflow Completed Successfully</div>
              </div>
            )}
            
            {executionState.status === 'error' && (
              <div className="text-center">
                <div className="text-6xl mb-4">❌</div>
                <div className="text-red-500 text-lg">{executionState.message}</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
