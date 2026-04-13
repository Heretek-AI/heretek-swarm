/**
 * FlowCanvas - React Flow Visual Canvas for Heretek Swarm
 * 
 * Flowise-style visual workflow builder with drag-and-drop interface
 * for the 23-agent swarm with Triad relationship visualization.
 */

import React, { useCallback, useState, useEffect, useRef } from 'react';
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  MiniMap,
  Node,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
  Connection,
  NodeTypes,
  Panel,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { ToolNode } from './ToolNode';
import { LLMNode } from './LLMNode';
import { MemoryNode } from './MemoryNode';
import { DecisionNode } from './DecisionNode';
import { ConnectorNode } from './ConnectorNode';

// Types
export interface AgentNodeData {
  agentId: string;
  agentType: string;
  agentName: string;
  description: string;
  triad?: string;
  llmModel?: string;
  llmProvider?: string;
  status: 'active' | 'idle' | 'error' | 'offline';
  healthScore: number;
  config: Record<string, unknown>;
  label: string;
}

export type AgentType = 
  | 'steward' | 'alpha' | 'beta' | 'charlie' | 'historian'
  | 'executor' | 'validator' | 'memory-manager' | 'telemetry'
  | 'maker' | 'taker' | 'researcher' | 'coder' | 'reviewer'
  | 'tester' | 'deployer' | 'documenter' | 'guardian' | 'orchestrator'
  | 'planner' | 'scheduler' | 'sentinel';

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  nodes: Node[];
  edges: Edge[];
  createdAt: string;
  updatedAt: string;
  version: string;
}

// Agent Registry - All 23 Agents
export const AGENT_REGISTRY: Record<AgentType, {
  name: string;
  description: string;
  icon: string;
  color: string;
  defaultLlmModel?: string;
}> = {
  steward: { name: 'Steward', description: 'Orchestrator agent for coordinating swarm operations', icon: '👑', color: '#f59e0b', defaultLlmModel: 'gpt-4o' },
  alpha: { name: 'Alpha', description: 'Primary analyst in Triad - strategic decision maker', icon: '🧠', color: '#8b5cf6', defaultLlmModel: 'gpt-4o' },
  beta: { name: 'Beta', description: 'Secondary analyst in Triad - tactical executor', icon: '⚡', color: '#3b82f6', defaultLlmModel: 'gpt-4o-mini' },
  charlie: { name: 'Charlie', description: 'Tertiary analyst in Triad - information synthesizer', icon: '🔮', color: '#10b981', defaultLlmModel: 'gpt-4o-mini' },
  historian: { name: 'Historian', description: 'Collects and archives swarm decisions and learnings', icon: '📚', color: '#6366f1', defaultLlmModel: 'gpt-4o-mini' },
  executor: { name: 'Executor', description: 'Executes approved decisions and workflows', icon: '⚙️', color: '#64748b', defaultLlmModel: 'gpt-4o-mini' },
  validator: { name: 'Validator', description: 'Validates outputs and ensures quality', icon: '✅', color: '#22c55e' },
  'memory-manager': { name: 'Memory Manager', description: 'Manages tiered memory across agents', icon: '🧩', color: '#f97316' },
  telemetry: { name: 'Telemetry', description: 'Collects and reports system metrics', icon: '📊', color: '#06b6d4' },
  maker: { name: 'MAKER', description: 'Market-based Agent for Knowledge Extraction and Ranking', icon: '🏛️', color: '#ec4899' },
  taker: { name: 'TAKER', description: 'Consumes and applies knowledge from MAKER', icon: '📥', color: '#d946ef' },
  researcher: { name: 'Researcher', description: 'Conducts deep research on topics', icon: '🔬', color: '#14b8a6' },
  coder: { name: 'Coder', description: 'Writes and implements code', icon: '💻', color: '#3b82f6' },
  reviewer: { name: 'Reviewer', description: 'Reviews code and documents', icon: '👀', color: '#a855f7' },
  tester: { name: 'Tester', description: 'Creates and runs tests', icon: '🧪', color: '#84cc16' },
  deployer: { name: 'Deployer', description: 'Handles deployment operations', icon: '🚀', color: '#f43f5e' },
  documenter: { name: 'Documenter', description: 'Creates and maintains documentation', icon: '📝', color: '#eab308' },
  guardian: { name: 'Guardian', description: 'Security and compliance monitoring', icon: '🛡️', color: '#64748b' },
  orchestrator: { name: 'Orchestrator', description: 'Coordinates multi-agent workflows', icon: '🎭', color: '#8b5cf6' },
  planner: { name: 'Planner', description: 'Creates and maintains execution plans', icon: '📋', color: '#06b6d4' },
  scheduler: { name: 'Scheduler', description: 'Schedules and manages task timing', icon: '⏰', color: '#fb923c' },
  sentinel: { name: 'Sentinel', description: 'Monitors system health and alerts', icon: '🚨', color: '#ef4444' },
};

// Triad Configurations
export const TRIAD_CONFIGS = {
  core: { name: 'Core Triad', agents: ['alpha', 'beta', 'charlie'] as AgentType[], description: 'Primary decision-making triad', color: '#8b5cf6' },
  oversight: { name: 'Oversight Triad', agents: ['steward', 'historian', 'guardian'] as AgentType[], description: 'Governance and oversight triad', color: '#f59e0b' },
  execution: { name: 'Execution Triad', agents: ['maker', 'taker', 'executor'] as AgentType[], description: 'Knowledge and execution triad', color: '#10b981' },
};

// Custom Agent Node Component
const HeretekAgentNode: React.FC<any> = ({ data, selected }) => {
  const agentInfo = AGENT_REGISTRY[data.agentType as AgentType];
  
  const getStatusColor = () => {
    switch (data.status) {
      case 'active': return '#22c55e';
      case 'idle': return '#f59e0b';
      case 'error': return '#ef4444';
      default: return '#64748b';
    }
  };

  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 min-w-[180px] transition-all ${selected ? 'shadow-lg scale-105' : ''}`}
      style={{
        borderColor: selected ? (agentInfo?.color || '#6366f1') : '#374151',
        backgroundColor: '#1f2937',
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xl">{agentInfo?.icon || '🤖'}</span>
          <div>
            <div className="font-semibold text-white text-sm">{agentInfo?.name || data.agentName}</div>
            {data.triad && <div className="text-xs text-gray-400 uppercase">{data.triad}</div>}
          </div>
        </div>
        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: getStatusColor() }} title={data.status} />
      </div>
      {data.llmModel && (
        <div className="text-xs text-gray-400 mb-1">
          Model: <span className="text-blue-400">{data.llmModel}</span>
        </div>
      )}
      <div className="mt-2">
        <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
          <span>Health</span>
          <span className={data.healthScore >= 70 ? 'text-green-400' : data.healthScore >= 40 ? 'text-yellow-400' : 'text-red-400'}>
            {data.healthScore}%
          </span>
        </div>
        <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all"
            style={{
              width: `${data.healthScore}%`,
              backgroundColor: data.healthScore >= 70 ? '#22c55e' : data.healthScore >= 40 ? '#eab308' : '#ef4444',
            }}
          />
        </div>
      </div>
    </div>
  );
};

// Node types
const nodeTypes: NodeTypes = {
  agent: HeretekAgentNode,
  tool: ToolNode,
  llm: LLMNode,
  memory: MemoryNode,
  decision: DecisionNode,
  connector: ConnectorNode,
};

// FlowCanvas Component
interface FlowCanvasProps {
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onSave?: (nodes: Node[], edges: Edge[]) => void;
  onExecute?: (nodes: Node[], edges: Edge[]) => void;
}

function FlowCanvasInner({ initialNodes = [], initialEdges = [], onSave }: FlowCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [workflowName, setWorkflowName] = useState('Untitled Workflow');
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showLoadModal, setShowLoadModal] = useState(false);
  const [savedWorkflows, setSavedWorkflows] = useState<WorkflowTemplate[]>([]);
  const [llmRoutingOpen, setLlmRoutingOpen] = useState(false);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition } = useReactFlow();

  // Load saved workflows
  useEffect(() => {
    const saved = localStorage.getItem('heretek-workflows');
    if (saved) {
      try {
        setSavedWorkflows(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse saved workflows:', e);
      }
    }
  }, []);

  // Handlers
  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onConnect = useCallback((connection: Connection) => {
    setEdges((eds) =>
      addEdge({
        ...connection,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#6366f1', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1' },
      }, eds)
    );
  }, [setEdges]);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    const agentType = event.dataTransfer.getData('application/heretek-agent');
    if (!agentType || !AGENT_REGISTRY[agentType as AgentType]) return;

    const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
    const agentInfo = AGENT_REGISTRY[agentType as AgentType];
    const newNode: Node = {
      id: `agent-${Date.now()}`,
      type: 'agentNode',
      position,
      data: {
        agentName: agentInfo.name,
        description: agentInfo.description,
        llmModel: agentInfo.defaultLlmModel,
        llmProvider: 'openai',
        status: 'idle',
        healthScore: 100,
        config: {},
        label: agentInfo.name,
      },
    };
    setNodes((nds) => [...nds, newNode]);
  }, [screenToFlowPosition, setNodes]);

  const handleSave = useCallback(() => {
    const template: WorkflowTemplate = {
      id: `workflow-${Date.now()}`,
      name: workflowName,
      description: `Workflow: ${workflowName}`,
      nodes,
      edges,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      version: '1.0.0',
    };
    const updated = [...savedWorkflows.filter(w => w.id !== template.id), template];
    setSavedWorkflows(updated);
    localStorage.setItem('heretek-workflows', JSON.stringify(updated));
    onSave?.(nodes, edges);
    setShowSaveModal(false);
  }, [workflowName, nodes, edges, savedWorkflows, onSave]);

  const handleLoad = useCallback((workflow: WorkflowTemplate) => {
    setNodes(workflow.nodes);
    setEdges(workflow.edges);
    setWorkflowName(workflow.name);
    setShowLoadModal(false);
  }, [setNodes, setEdges]);

  const handleDeleteWorkflow = useCallback((id: string) => {
    const updated = savedWorkflows.filter(w => w.id !== id);
    setSavedWorkflows(updated);
    localStorage.setItem('heretek-workflows', JSON.stringify(updated));
  }, [savedWorkflows]);

  const handleExport = useCallback(() => {
    const exportData = { name: workflowName, nodes, edges, exportedAt: new Date().toISOString(), version: '1.0.0' };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${workflowName.replace(/\s+/g, '-').toLowerCase()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [workflowName, nodes, edges]);

  const handleImport = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target?.result as string);
        if (data.nodes && data.edges) {
          setNodes(data.nodes);
          setEdges(data.edges);
          setWorkflowName(data.name || 'Imported Workflow');
        }
      } catch (err) {
        console.error('Failed to import workflow:', err);
      }
    };
    reader.readAsText(file);
  }, [setNodes, setEdges]);

  const addTriad = useCallback((triadKey: keyof typeof TRIAD_CONFIGS) => {
    const triad = TRIAD_CONFIGS[triadKey];
    const newNodes = triad.agents.map((agentType, index) => {
      const agentInfo = AGENT_REGISTRY[agentType];
      return {
        id: `${agentType}-${Date.now()}-${index}`,
        type: 'agent',
        position: { x: 300 + index * 250, y: 100 },
        data: {
          agentType: agentType === 'supervisor' ? (['alpha', 'beta', 'charlie'][index]) : undefined,
          llmModel: agentInfo.defaultLlmModel,
          llmProvider: 'openai',
          status: 'idle',
          healthScore: 100,
          config: {},
          label: agentInfo.name,
        },
      };
    });
    setNodes((nds) => [...nds, ...newNodes]);
  }, [setNodes]);

  const updateNodeModel = useCallback((nodeId: string, field: string, value: string) => {
    setNodes((nds) => nds.map((node) => {
      if (node.id === nodeId) {
        return {
          ...node,
          data: { ...node.data, [field]: value },
        };
      }
      return node;
    }));
  }, [setNodes]);

  return (
    <div className="flex h-full">
      {/* Left Sidebar */}
      <div className="w-64 bg-gray-900 border-r border-gray-700 overflow-y-auto">
        <div className="p-4">
          <h2 className="text-lg font-semibold text-white mb-4">Agent Palette</h2>

          {/* Quick Add Triads */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-400 mb-2 uppercase tracking-wider">Quick Add - Triads</h3>
            <div className="space-y-2">
              {(Object.entries(TRIAD_CONFIGS) as [keyof typeof TRIAD_CONFIGS, typeof TRIAD_CONFIGS.core][]).map(([key, triad]) => (
                <button
                  key={key}
                  onClick={() => addTriad(key)}
                  className="w-full px-3 py-2 rounded-lg border border-gray-600 bg-gray-800 hover:bg-gray-700 text-left transition-colors"
                  style={{ borderLeftColor: triad.color, borderLeftWidth: 3 }}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{triad.agents.map(a => AGENT_REGISTRY[a]?.icon).join(' ')}</span>
                    <div>
                      <div className="text-sm font-medium text-white">{triad.name}</div>
                      <div className="text-xs text-gray-400">{triad.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* All Agents */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-400 mb-2 uppercase tracking-wider">All Agents (23)</h3>
            <div className="space-y-1">
              {(Object.entries(AGENT_REGISTRY) as [AgentType, typeof AGENT_REGISTRY.steward][]).map(([type, info]) => (
                <div
                  key={type}
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData('application/heretek-agent', type);
                    e.dataTransfer.effectAllowed = 'move';
                  }}
                  className="px-3 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 cursor-grab active:cursor-grabbing transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span>{info.icon}</span>
                    <span className="text-sm text-white">{info.name}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tools */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-400 mb-2 uppercase tracking-wider">Tools</h3>
            <div className="space-y-1">
              {['Code Execution', 'Web Browser', 'File System', 'API Call'].map((tool) => (
                <div key={tool} className="px-3 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 cursor-pointer transition-colors">
                  <div className="text-sm text-white">{tool}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Canvas */}
      <div className="flex-1 relative" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onDragOver={onDragOver}
          onDrop={onDrop}
          nodeTypes={nodeTypes}
          fitView
          snapToGrid
          snapGrid={[15, 15]}
          defaultEdgeOptions={{
            type: 'smoothstep',
            animated: true,
            style: { stroke: '#6366f1', strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1' },
          }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#374151" />
          <Controls className="bg-gray-800 border border-gray-700 rounded-lg" />
          <MiniMap
            className="bg-gray-900 border border-gray-700 rounded-lg"
            nodeColor={(node) => AGENT_REGISTRY[node.data?.agentType as AgentType]?.color || '#6366f1'}
          />
          <Panel position="top-left">
            <div className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2">
              <input
                type="text"
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                className="bg-transparent text-white text-lg font-medium focus:outline-none"
                placeholder="Workflow Name"
              />
            </div>
          </Panel>
          <Panel position="top-right" className="flex gap-2">
            <button onClick={() => setShowSaveModal(true)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">💾 Save</button>
            <button onClick={() => setShowLoadModal(true)} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors">📂 Load</button>
            <button onClick={handleExport} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors">📤 Export</button>
            <label className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors cursor-pointer">
              📥 Import
              <input type="file" accept=".json" onChange={handleImport} className="hidden" />
            </label>
          </Panel>
          <Panel position="bottom-right">
            <button onClick={() => setLlmRoutingOpen(true)} className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors">
              🤖 LLM Routing
            </button>
          </Panel>
        </ReactFlow>

        {/* Selected Node Panel */}
        {selectedNode && (
          <div className="absolute right-4 top-20 w-80 bg-gray-900 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Node Details</h3>
              <button onClick={() => setSelectedNode(null)} className="text-gray-400 hover:text-white">✕</button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 uppercase">Agent Type</label>
                <div className="text-white">{(selectedNode.data as AgentNodeData).agentType}</div>
              </div>
              <div>
                <label className="text-xs text-gray-400 uppercase">LLM Model</label>
                <select
                  value={(selectedNode.data as AgentNodeData).llmModel || ''}
                  onChange={(e) => updateNodeModel(selectedNode.id, 'llmModel', e.target.value)}
                  className="w-full mt-1 px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white"
                >
                  <option value="">Default</option>
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-4o-mini">GPT-4o Mini</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="claude-3-opus">Claude 3 Opus</option>
                  <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 uppercase">Provider</label>
                <select
                  value={(selectedNode.data as AgentNodeData).llmProvider || 'openai'}
                  onChange={(e) => updateNodeModel(selectedNode.id, 'llmProvider', e.target.value)}
                  className="w-full mt-1 px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="google">Google</option>
                  <option value="ollama">Ollama</option>
                  <option value="minimax">MiniMax</option>
                  <option value="zai">Z.AI</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Save Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold text-white mb-4">Save Workflow</h3>
            <input
              type="text"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white mb-4"
              placeholder="Workflow name"
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowSaveModal(false)} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg">Cancel</button>
              <button onClick={handleSave} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Load Modal */}
      {showLoadModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-[500px] max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-white mb-4">Load Workflow</h3>
            {savedWorkflows.length === 0 ? (
              <div className="text-gray-400 text-center py-8">No saved workflows yet</div>
            ) : (
              <div className="space-y-2">
                {savedWorkflows.map((workflow) => (
                  <div key={workflow.id} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg hover:bg-gray-700">
                    <div>
                      <div className="text-white font-medium">{workflow.name}</div>
                      <div className="text-xs text-gray-400">{workflow.nodes.length} nodes • {workflow.edges.length} edges</div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => handleLoad(workflow)} className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded">Load</button>
                      <button onClick={() => handleDeleteWorkflow(workflow.id)} className="px-3 py-1 bg-red-600/50 hover:bg-red-600 text-white text-sm rounded">Delete</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="flex justify-end mt-4">
              <button onClick={() => setShowLoadModal(false)} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg">Close</button>
            </div>
          </div>
        </div>
      )}

      {/* LLM Routing Panel */}
      {llmRoutingOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-[700px] max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">LLM Routing Configuration</h3>
              <button onClick={() => setLlmRoutingOpen(false)} className="text-gray-400 hover:text-white text-xl">✕</button>
            </div>
            <div className="space-y-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-400 mb-3">Provider Distribution</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-400">Primary Provider</label>
                    <select className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                      <option value="openai">OpenAI (60%)</option>
                      <option value="anthropic">Anthropic (25%)</option>
                      <option value="google">Google (10%)</option>
                      <option value="ollama">Ollama (5%)</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Fallback Provider</label>
                    <select className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                      <option value="anthropic">Anthropic</option>
                      <option value="openai">OpenAI</option>
                      <option value="google">Google</option>
                    </select>
                  </div>
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-400 mb-3">Agent Model Assignments</h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {(Object.entries(AGENT_REGISTRY) as [AgentType, typeof AGENT_REGISTRY.steward][]).slice(0, 10).map(([type, info]) => (
                    <div key={type} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span>{info.icon}</span>
                        <span className="text-white text-sm">{info.name}</span>
                      </div>
                      <select className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm">
                        <option value="gpt-4o">GPT-4o</option>
                        <option value="gpt-4o-mini">GPT-4o Mini</option>
                        <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                      </select>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-400 mb-3">Cost Optimization</h4>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 text-white">
                    <input type="checkbox" className="rounded bg-gray-700 border-gray-600" />
                    Enable model routing based on task complexity
                  </label>
                </div>
                <div className="mt-3 text-sm text-gray-400">
                  Estimated monthly cost: <span className="text-green-400">$1,234.56</span>
                </div>
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <button onClick={() => setLlmRoutingOpen(false)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">Apply Configuration</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export const FlowCanvas: React.FC<FlowCanvasProps> = (props) => (
  <ReactFlowProvider>
    <FlowCanvasInner {...props} />
  </ReactFlowProvider>
);

export default FlowCanvas;
