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
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import AgentNode, { AgentData } from './AgentNode';

// Use environment variable or relative path (nginx proxies /api to api:8000)
const API_URL = import.meta.env.VITE_API_URL || '';

interface AgentApiResponse {
  id: string;
  type: string;
  status: string;
  lastActivity?: string;
}

const nodeTypes = {
  agentNode: AgentNode,
};

const initialEdges: Edge[] = [];

export function CollectiveCanvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
      
      setNodes(agentNodes);
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
    <div className="w-full h-screen bg-gray-900">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        className="bg-gray-900"
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
    </div>
  );
}

export default CollectiveCanvas;
