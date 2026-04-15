/**
 * Workflow Builder - Visual Workflow Editor
 * 
 * Flowise-like visual workflow builder for Heretek Swarm.
 * Based on ReactFlow for drag-and-drop node-based workflow design.
 */

import React, { useCallback, useState, useMemo, useRef, useEffect } from 'react';
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  MiniMap,
  Node,
  NodeChange,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
  Connection,
  NodeTypes,
} from 'reactflow';

import {
  BaseNodeData,
  NodeType,
  Workflow,
  WorkflowValidation,
  NodePaletteItem,
  NodeCategory,
  WorkflowTemplate,
  WorkflowHistory,
  WorkflowExportFormat,
} from './types';

import 'reactflow/dist/style.css';
import {
  AgentNode,
  ToolNode,
  MemoryNode,
  DecisionNode,
  ConnectorNode,
  LLMNode,
} from './index';
import { NodeConfigPanel } from '../Workflow/NodeConfigPanel';
import type { AgentConfig } from '../Workflow/NodeConfigPanel';

// Use environment variable or relative path (nginx proxies /api to api:8000)
const API_URL = import.meta.env.VITE_API_HOST || '';

/**
 * Workflow Builder Component
 */
export function WorkflowBuilder() {
  const [nodes, setNodes, onNodesChange] = useNodesState<BaseNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedNode, setSelectedNode] = useState<BaseNodeData | null>(null);
  const [nodeConfig, setNodeConfig] = useState<Record<string, Record<string, any>>>({});
  const [validation, setValidation] = useState<WorkflowValidation>({ valid: true, errors: [], warnings: [] });
  const [isExecuting, setIsExecuting] = useState(false);
  const [savedWorkflows, setSavedWorkflows] = useState<Workflow[]>([]);
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);
  
  // NodeConfigPanel state
  const [configPanelOpen, setConfigPanelOpen] = useState(false);
  const [configPanelNode, setConfigPanelNode] = useState<{
    id: string;
    type: string;
    data: {
      agentId?: string;
      agentType?: string;
      config?: Record<string, any>;
    };
  } | null>(null);

  const reactFlowWrapperRef = useRef<HTMLDivElement>(null);

  /**
   * Node palette - organized by category
   */
  const nodePalette: NodePaletteItem[] = useMemo(() => [
    // Agents
    {
      type: NodeType.AGENT,
      label: 'Steward',
      icon: '👥',
      category: NodeCategory.AGENTS,
      description: 'Orchestrator agent for coordinating swarm operations',
      defaultConfig: {
        agentType: 'steward',
      },
    },
    {
      type: NodeType.AGENT,
      label: 'Alpha',
      icon: '🧠',
      category: NodeCategory.AGENTS,
      description: 'Primary analyst agent in Triad',
      defaultConfig: {
        agentType: 'alpha',
      },
    },
    // Tools
    {
      type: NodeType.TOOL,
      label: 'Code Execution',
      icon: '⚡',
      category: NodeCategory.TOOLS,
      description: 'Execute code in a secure environment',
      defaultConfig: {
        toolType: 'code_execution',
      },
    },
    {
      type: NodeType.TOOL,
      label: 'Web Browser',
      icon: '🌐',
      category: NodeCategory.TOOLS,
      description: 'Browse and interact with web pages',
      defaultConfig: {
        toolType: 'web_browser',
      },
    },
    // Memory
    {
      type: NodeType.MEMORY,
      label: 'Ephemeral Memory',
      icon: '⚡',
      category: NodeCategory.MEMORY,
      description: 'Short-term in-memory storage',
      defaultConfig: {
        memoryType: 'ephemeral',
      },
    },
    {
      type: NodeType.MEMORY,
      label: 'Persistent Memory',
      icon: '💾',
      category: NodeCategory.MEMORY,
      description: 'Long-term database storage',
      defaultConfig: {
        memoryType: 'persistent',
      },
    },
    {
      type: NodeType.MEMORY,
      label: 'mem0 Memory',
      icon: '🧠',
      category: NodeCategory.MEMORY,
      description: 'AI-powered memory with mem0',
      defaultConfig: {
        memoryType: 'mem0',
      },
    },
    // Decision
    {
      type: NodeType.DECISION,
      label: 'Conditional Branch',
      icon: '🔀',
      category: NodeCategory.LOGIC,
      description: 'Branch workflow based on conditions',
      defaultConfig: {
        condition: 'true',
        branches: [
          { id: 'true', label: 'True', condition: 'true' },
          { id: 'false', label: 'False', condition: 'false' },
        ],
      },
    },
    // Connector
    {
      type: NodeType.CONNECTOR,
      label: 'Agent to Agent',
      icon: '🤝',
      category: NodeCategory.CONNECTORS,
      description: 'Connect agents for collaboration',
      defaultConfig: {
        connectorType: 'agent_to_agent',
      },
    },
    // LLM
    {
      type: NodeType.LLM,
      label: 'OpenAI GPT-4',
      icon: '🤖',
      category: NodeCategory.LLM,
      description: 'OpenAI GPT-4 model',
      defaultConfig: {
        model: 'gpt-4',
        provider: 'openai',
        temperature: 0.7,
        maxTokens: 4096,
      },
    },
  ], []);

  /**
   * Register custom node types
   */
  const nodeTypes: NodeTypes = useMemo(() => ({
    [NodeType.AGENT]: AgentNode,
    [NodeType.TOOL]: ToolNode,
    [NodeType.MEMORY]: MemoryNode,
    [NodeType.DECISION]: DecisionNode,
    [NodeType.CONNECTOR]: ConnectorNode,
    [NodeType.LLM]: LLMNode,
  }), []);

  /**
   * Add node to canvas
   */
  const addNode = useCallback((type: NodeType) => {
    const paletteItem = nodePalette.find((item) => item.type === type);
    if (!paletteItem) return;

    const nodeId = `node-${Date.now()}`;
    const newNode: Node<BaseNodeData> = {
      id: nodeId,
      type: type,
      position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 },
      data: {
        id: nodeId,
        type: type,
        ...paletteItem.defaultConfig,
        config: paletteItem.defaultConfig || {},
        // Add callback for opening config panel
        onOpenConfig: handleOpenConfig,
      } as any,
    };

    setNodes((nds) => [...nds, newNode]);
    setNodeConfig((prev) => ({
      ...prev,
      [newNode.id]: paletteItem.defaultConfig || {},
    }));
  }, [nodePalette]);

  /**
   * Handle opening configuration panel
   */
  const handleOpenConfig = useCallback((nodeId: string) => {
    const node = nodes.find((n) => n.id === nodeId);
    if (node) {
      setConfigPanelNode({
        id: node.id,
        type: node.type || 'agent',
        data: {
          agentId: (node.data as any).agentId || node.id,
          agentType: (node.data as any).agentType || 'steward',
          config: (node.data as any).config || {},
        },
      });
      setConfigPanelOpen(true);
    }
  }, [nodes]);

  /**
   * Handle closing configuration panel
   */
  const handleCloseConfig = useCallback(() => {
    setConfigPanelOpen(false);
    setConfigPanelNode(null);
  }, []);

  /**
   * Handle saving configuration via API
   */
  const handleSaveConfig = useCallback(async (config: AgentConfig) => {
    try {
      const response = await fetch(`${API_URL}/api/agent-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: config.agentId,
          agent_type: config.agentType,
          config: {
            llmProvider: config.llmProvider,
            model: config.model,
            temperature: config.temperature,
            maxTokens: config.maxTokens,
            // Arbiter-specific
            decisionThreshold: config.decisionThreshold,
            quorumSize: config.quorumSize,
            timeout: config.timeout,
            // Prism-specific
            analysisDepth: config.analysisDepth,
            perspectiveCount: config.perspectiveCount,
            confidenceThreshold: config.confidenceThreshold,
            // Habit-Forge-specific
            repetitionThreshold: config.repetitionThreshold,
            rewardSchedule: config.rewardSchedule,
            extinctionCriteria: config.extinctionCriteria,
          },
        }),
      });
      
      if (!response.ok) throw new Error('Failed to save configuration');
      
      // Update local node config
      if (configPanelNode) {
        setNodeConfig((prev) => ({
          ...prev,
          [configPanelNode.id]: {
            ...prev[configPanelNode.id],
            agentType: config.agentType,
            llmProvider: config.llmProvider,
            model: config.model,
            temperature: config.temperature,
            maxTokens: config.maxTokens,
          },
        }));
        
        // Update node data in ReactFlow
        setNodes((nds) =>
          nds.map((node) =>
            node.id === configPanelNode.id
              ? {
                  ...node,
                  data: {
                    ...(node.data as any),
                    agentType: config.agentType,
                    config: {
                      ...((node.data as any).config || {}),
                      llmProvider: config.llmProvider,
                      model: config.model,
                      temperature: config.temperature,
                      maxTokens: config.maxTokens,
                    },
                  },
                }
              : node
          )
        );
      }
    } catch (error) {
      console.error('Failed to save agent configuration:', error);
      throw error;
    }
  }, [configPanelNode, setNodes]);

  /**
   * Delete node
   */
  const deleteNode = useCallback((nodeId: string) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
    setNodeConfig((prev) => {
      const newConfig = { ...prev };
      delete newConfig[nodeId];
      return newConfig;
    });
    if (selectedNode?.id === nodeId) {
      setSelectedNode(null);
    }
  }, [selectedNode]);

  /**
   * Handle connection
   */
  const onConnect = useCallback((connection: Connection) => {
    setEdges((eds) => addEdge(connection, eds));
  }, []);

  /**
   * Handle node selection
   */
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    // Don't select node if config panel was opened
    if ((node.data as any).onOpenConfig) {
      // Let the node handle the click for config
    }
    setSelectedNode(node.data as BaseNodeData);
  }, []);

  /**
   * Handle background click to deselect
   */
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  /**
   * Validate workflow
   */
  const validateWorkflow = useCallback(() => {
    const errors: { nodeId: string; field: string; message: string; severity: 'error' | 'warning' }[] = [];
    const warnings: { nodeId: string; message: string; suggestion?: string }[] = [];
    
    // Check for nodes without connections
    nodes.forEach((node) => {
      const hasConnections = edges.some(
        (edge) => edge.source === node.id || edge.target === node.id
      );
      if (!hasConnections && nodes.length > 1) {
        warnings.push({
          nodeId: node.id,
          message: 'Node is not connected to any other node',
        });
      }
    });

    // Check for cycles
    const visited = new Set<string>();
    const hasCycle = (nodeId: string, path: string[] = []): boolean => {
      if (path.includes(nodeId)) {
        return true;
      }
      if (visited.has(nodeId)) {
        return false;
      }
      visited.add(nodeId);
      const outgoingEdges = edges.filter((edge) => edge.source === nodeId);
      return outgoingEdges.some((edge) => hasCycle(edge.target, [...path, nodeId]));
    };

    nodes.forEach((node) => {
      if (hasCycle(node.id)) {
        errors.push({
          nodeId: node.id,
          field: 'connections',
          message: 'Cycle detected in workflow',
          severity: 'error',
        });
      }
    });

    setValidation({
      valid: errors.length === 0,
      errors,
      warnings,
    });
  }, [nodes, edges]);

  /**
   * Export workflow
   */
  const exportWorkflow = useCallback((format: WorkflowExportFormat) => {
    const workflow: Workflow = {
      id: 'custom',
      name: 'Custom Workflow',
      description: 'Custom workflow created in Workflow Builder',
      nodes: nodes.map((n) => n.data as BaseNodeData),
      edges: edges,
      version: 1,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    let content = '';
    if (format === 'json') {
      content = JSON.stringify(workflow, null, 2);
    } else if (format === 'yaml') {
      content = `name: ${workflow.name}\n`;
      content += `description: ${workflow.description}\n`;
      content += `nodes:\n`;
      nodes.forEach((node) => {
        content += `  - id: ${node.id}\n`;
        content += `    type: ${node.type}\n`;
      });
      content += `edges:\n`;
      edges.forEach((edge) => {
        content += `  - source: ${edge.source}\n`;
        content += `    target: ${edge.target}\n`;
      });
    }

    // Create download link
    const blob = new Blob([content], {
      type: format === 'yaml' ? 'text/yaml' : 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workflow.${format}`;
    a.click();
  }, [nodes, edges]);

  /**
   * Save workflow to backend
   */
  const saveWorkflow = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: currentWorkflowId || `workflow-${Date.now()}`,
          name: 'Custom Workflow',
          description: 'Workflow created in Workflow Builder',
          nodes: nodes.map(n => ({ id: n.id, type: n.type, position: n.position, data: n.data })),
          edges: edges,
          version: 1,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
      
      if (!response.ok) throw new Error('Failed to save workflow');
      
      const saved = await response.json();
      setCurrentWorkflowId(saved.id);
      setSavedWorkflows(prev => [...prev, saved]);
      alert('Workflow saved successfully!');
    } catch (error) {
      console.error('Failed to save workflow:', error);
      alert('Failed to save workflow');
    }
  }, [nodes, edges, currentWorkflowId]);

  /**
   * Load workflow from backend
   */
  const loadWorkflows = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/workflows`);
      if (!response.ok) throw new Error('Failed to load workflows');
      
      const data = await response.json();
      setSavedWorkflows(data.workflows || []);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    }
  }, []);

  /**
   * Load specific workflow
   */
  const loadWorkflow = useCallback(async (workflowId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/workflows/${workflowId}`);
      if (!response.ok) throw new Error('Failed to load workflow');
      
      const data = await response.json();
      setNodes(data.nodes.map((n: any) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        data: n.data,
      })));
      setEdges(data.edges || []);
      setCurrentWorkflowId(workflowId);
    } catch (error) {
      console.error('Failed to load workflow:', error);
    }
  }, []);

  /**
   * Execute workflow
   */
  const executeWorkflow = useCallback(async () => {
    if (!validation.valid || nodes.length === 0) {
      alert('Please fix validation errors before executing');
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/api/workflows/${currentWorkflowId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nodes: nodes,
          edges: edges,
        }),
      });
      
      if (!response.ok) throw new Error('Failed to execute workflow');
      
      const result = await response.json();
      alert(`Workflow executed! Execution ID: ${result.execution_id}`);
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      alert('Failed to execute workflow');
    }
  }, [nodes, edges, currentWorkflowId, validation.valid]);

  /**
   * Load workflows on mount
   */
  useEffect(() => {
    loadWorkflows();
  }, [loadWorkflows]);

  /**
   * Validate on nodes/edges change
   */
  useEffect(() => {
    validateWorkflow();
  }, [nodes, edges]);

  return (
    <div className="workflow-builder">
      <div className="workflow-header">
        <h1>Workflow Builder</h1>
        <div className="header-actions">
          <button
            onClick={validateWorkflow}
            className="btn btn-secondary"
            disabled={nodes.length === 0}
          >
            Validate
          </button>
          <button
            onClick={saveWorkflow}
            className="btn btn-primary"
            disabled={nodes.length === 0}
          >
            Save Workflow
          </button>
          <div className="export-buttons">
            <button onClick={() => exportWorkflow('json')} className="btn btn-secondary">
              Export JSON
            </button>
            <button onClick={() => exportWorkflow('yaml')} className="btn btn-secondary">
              Export YAML
            </button>
          </div>
        </div>
        <div className="workflow-actions">
          <select
            value={currentWorkflowId || ''}
            onChange={(e) => loadWorkflow(e.target.value)}
            className="workflow-select"
          >
            <option value="">Load Saved Workflow...</option>
            {savedWorkflows.map((wf) => (
              <option key={wf.id} value={wf.id}>
                {wf.name}
              </option>
            ))}
          </select>
          <button
            onClick={executeWorkflow}
            className="btn btn-success"
            disabled={nodes.length === 0 || !validation.valid}
          >
            Execute Workflow
          </button>
        </div>
      </div>

      {!validation.valid && (
        <div className="validation-errors">
          <h3>Validation Errors</h3>
          {validation.errors.map((error, idx) => (
            <div key={idx} className="error-item">
              <strong>{error.nodeId}</strong>: {error.message}
            </div>
          ))}
        </div>
      )}

      <div className="workflow-content">
        <div className="node-palette">
          <h2>Node Palette</h2>
          <div className="palette-categories">
            {Object.values(NodeCategory).map((category) => (
              <div key={category} className="palette-category">
                <h3>{category}</h3>
                {nodePalette
                  .filter((item) => item.category === category)
                  .map((item) => (
                    <div
                      key={item.type}
                      className="palette-item"
                      draggable
                      onDragStart={(e) => e.dataTransfer.setData('application/reactflow', item.type)}
                      onClick={() => addNode(item.type)}
                    >
                      <span className="palette-icon">{item.icon}</span>
                      <span className="palette-label">{item.label}</span>
                      <span className="palette-desc">{item.description}</span>
                    </div>
                  ))}
              </div>
            ))}
          </div>
        </div>

        <div className="canvas-container" ref={reactFlowWrapperRef}>
          <ReactFlowProvider>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onPaneClick={onPaneClick}
              nodeTypes={nodeTypes}
              fitView
              snapToGrid
              snapGrid={[15, 15]}
              defaultEdgeOptions={{
                animated: true,
                type: 'smoothstep',
                style: { stroke: '#b1b1b1b1', strokeWidth: 2 },
                markerEnd: {
                  type: MarkerType.ArrowClosed,
                  color: '#b1b1b1',
                },
              }}
              deleteKeyCode="Delete"
            >
              <Background color="#f8fafc" variant={BackgroundVariant.Dots} />
              <Controls />
              <MiniMap
                nodeColor={(node) => {
                  const data = node.data as BaseNodeData;
                  switch (data.type) {
                    case NodeType.AGENT:
                      return '#3b82f6';
                    case NodeType.TOOL:
                      return '#06b6d4';
                    case NodeType.MEMORY:
                      return '#8b5cf6';
                    case NodeType.DECISION:
                      return '#eab308';
                    case NodeType.CONNECTOR:
                      return '#6366f1';
                    case NodeType.LLM:
                      return '#10b981';
                    default:
                      return '#6b7280';
                  }
                }}
                nodeStrokeWidth={2}
                zoomable
                pannable
              />
            </ReactFlow>
            
            {/* Node Configuration Panel */}
            <NodeConfigPanel
              node={configPanelNode}
              isOpen={configPanelOpen}
              onClose={handleCloseConfig}
              onSave={handleSaveConfig}
            />
          </ReactFlowProvider>
        </div>
      </div>

      {selectedNode && (
        <div className="node-properties">
          <h3>Node Properties</h3>
          <div className="property-group">
            <label>Node ID:</label>
            <input
              type="text"
              value={selectedNode.id}
              readOnly
              className="property-input"
            />
          </div>
          <div className="property-group">
            <label>Node Type:</label>
            <input
              type="text"
              value={selectedNode.type}
              readOnly
              className="property-input"
            />
          </div>
          {Object.keys(nodeConfig[selectedNode.id] || {}).map((key) => (
            <div key={key} className="property-group">
              <label>{key}:</label>
              <input
                type="text"
                value={JSON.stringify(nodeConfig[selectedNode.id]?.[key])}
                onChange={(e) => {
                  const value = e.target.value;
                  try {
                    const parsed = JSON.parse(value);
                    setNodeConfig((prev) => ({
                      ...prev,
                      [selectedNode.id]: {
                        ...prev[selectedNode.id],
                        [key]: parsed,
                      },
                    }));
                  } catch {
                    setNodeConfig((prev) => ({
                      ...prev,
                      [selectedNode.id]: {
                        ...prev[selectedNode.id],
                        [key]: value,
                      },
                    }));
                  }
                }}
                className="property-input"
              />
            </div>
          ))}
          <div className="property-actions">
            <button
              onClick={() => deleteNode(selectedNode.id)}
              className="btn btn-danger"
            >
              Delete Node
            </button>
          </div>
        </div>
      )}
      <style>{`
        .workflow-builder {
          display: flex;
          flex-direction: column;
          height: 100vh;
          background: #f8fafc;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .workflow-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          background: white;
          border-bottom: 1px solid #e5e7eb;
        }

        .workflow-header h1 {
          margin: 0;
          font-size: 24px;
          color: #1f2937;
        }

        .header-actions {
          display: flex;
          gap:  10px;
          align-items: center;
        }

        .export-buttons {
          display: flex;
          gap: 5px;
        }

        .validation-errors {
          background: #fee2e2;
          border: 1px solid #fecaca;
          border-radius: 8px;
          padding: 15px;
          margin: 10px 20px;
        }

        .validation-errors h3 {
          margin: 0 0 10px 0;
          color: #991b1b;
        }

        .error-item {
          color: #991b1b;
          margin: 5px 0;
        }

        .workflow-content {
          display: flex;
          flex: 1;
          overflow: hidden;
        }

        .node-palette {
          width: 300px;
          background: white;
          border-right: 1px solid #e5e7eb;
          overflow-y: auto;
          padding: 15px;
        }

        .node-palette h2 {
          margin: 0 0 15px 0;
          font-size: 18px;
          color: #1f2937;
        }

        .palette-categories {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .palette-category h3 {
          margin: 0 0 10px 0;
          font-size: 14px;
          color: #6b7280;
          text-transform: uppercase;
        }

        .palette-item {
          padding: 10px;
          background: #f9fafb;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          cursor: pointer;
          margin-bottom: 8px;
          transition: all 0.2s;
        }

        .palette-item:hover {
          background: #e0e7ff;
          border-color: #3b82f6;
        }

        .palette-icon {
          font-size: 24px;
          margin-right: 10px;
        }

        .palette-label {
          font-weight: 600;
          color: #1f2937;
        }

        .palette-desc {
          display: block;
          font-size: 12px;
          color: #6b7280;
          margin-top: 5px;
        }

        .canvas-container {
          flex: 1;
          background: #f8fafc;
          position: relative;
        }

        .react-flow-wrapper {
          height: 100%;
        }

        .node-properties {
          position: fixed;
          right: 20px;
          top: 80px;
          width: 300px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 15px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          max-height: calc(100vh - 100px);
          overflow-y: auto;
        }

        .node-properties h3 {
          margin: 0 0 15px 0;
          font-size: 16px;
          color: #1f2937;
        }

        .property-group {
          margin-bottom: 10px;
        }

        .property-group label {
          display: block;
          margin-bottom: 5px;
          font-size: 12px;
          color: #6b7280;
          font-weight: 600;
        }

        .property-input {
          width: 100%;
          padding: 8px;
          border: 1px solid #e5e7eb;
          border-radius: 4px;
          font-size: 14px;
        }

        .property-actions {
          display: flex;
          gap: 10px;
          margin-top: 15px;
        }

        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-primary {
          background: #3b82f6;
          color: white;
        }

        .btn-primary:hover {
          background: #2563eb;
        }

        .btn-secondary {
          background: #e5e7eb;
          color: #333;
        }

        .btn-secondary:hover {
          background: #d1d5db;
        }

        .btn-danger {
          background: #ef4444;
          color: white;
        }

        .btn-danger:hover {
          background: #dc2626;
        }
      `}</style>
    </div>
  );
}
