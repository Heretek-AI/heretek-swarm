/**
 * Canvas Components Index
 *
 * Exports all canvas-related components for agent visualization
 * and workflow building with XYFlow.
 */

export { default as AgentNode, type AgentData } from './AgentNode';
export { CollectiveCanvas } from './Canvas';
export { EnhancedCanvas } from './EnhancedCanvas';
export { default as ConnectionEdge, type ConnectionEdgeData, type MessageType } from './ConnectionEdge';
export { NodePalette, type AgentType, type NodePaletteProps } from './NodePalette';
export { CanvasToolbar, type CanvasToolbarProps } from './CanvasToolbar';
