/**
 * Workflow Builder Types
 *
 * Defines node types for visual workflow builder.
 * Based on Flowise and ReactFlow patterns.
 */

import type { Edge, Position } from 'reactflow';

// ============================================================================
// Node Types
// ============================================================================

/**
 * Base interface for all workflow nodes
 */
export interface BaseNodeData {
  id: string;
  type: NodeType;
  position: Position;
}

/**
 * Node type identifiers
 */
export enum NodeType {
  // Agent nodes
  AGENT = 'agent',  
  // Tool nodes
  TOOL = 'tool',  
  // Memory nodes
  MEMORY = 'memory',  
  // Decision nodes
  DECISION = 'decision',  
  // Connector nodes
  CONNECTOR = 'connector',  
  // Input/Output nodes
  INPUT = 'input',
  OUTPUT = 'output',  
  // LLM nodes
  LLM = 'llm',  
  // Template nodes
  TEMPLATE = 'template',
}

/**
 * Agent node data
 */
export interface AgentNodeData {
  agentId: string;
  agentType: AgentType;
  config: Record<string, any>;
}

/**
 * Agent types
 */
export enum AgentType {
  STEWARD = 'steward',
  ALPHA = 'alpha',
  BETA = 'beta',
  CHARLIE = 'charlie',
  HISTORIAN = 'historian',
  EXPLORER = 'explorer',
  EXAMINER = 'examiner',
  CODER = 'coder',
  DREAMER = 'dreamer',
  EMPATH = 'empath',
  CUSTOM = 'custom',
}

/**
 * Tool node data
 */
export interface ToolNodeData {
  toolId: string;
  toolName: string;
  toolType: ToolType;
  config: Record<string, any>;
}

/**
 * Tool types
 */
export enum ToolType {
  CODE_EXECUTION = 'code_execution',
  WEB_BROWSER = 'web_browser',
  FILE_OPERATIONS = 'file_operations',
  API_CONNECTOR = 'api_connector',
  DATABASE = 'database',
  VECTOR_SEARCH = 'vector_search',
  CUSTOM = 'custom',
}

/**
 * Memory node data
 */
export interface MemoryNodeData {
  memoryType: MemoryType;
  memoryId?: string;
  query?: string;
  config: Record<string, any>;
}

/**
 * Memory types
 */
export enum MemoryType {
  EPHEMERAL = 'ephemeral',
  PERSISTENT = 'persistent',
  MEM0 = 'mem0',
  HYBRID = 'hybrid',
}

/**
 * Decision node data
 */
export interface DecisionNodeData {
  condition: string;
  branches: DecisionBranch[];
  config: Record<string, any>;
}

/**
 * Decision branch
 */
export interface DecisionBranch {
  id: string;
  label: string;
  condition: string;
}

/**
 * Connector node data
 */
export interface ConnectorNodeData {
  connectorType: ConnectorType;
  config: Record<string, any>;
}

/**
 * Connector types
 */
export enum ConnectorType {
  AGENT_TO_AGENT = 'agent_to_agent',
  AGENT_TO_TOOL = 'agent_to_tool',
  AGENT_TO_MEMORY = 'agent_to_memory',
  TOOL_TO_MEMORY = 'tool_to_memory',
  MEMORY_TO_AGENT = 'memory_to_agent',
  CUSTOM = 'custom',
}

/**
 * LLM node data
 */
export interface LLMNodeData {
  model: string;
  provider: string;
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  config: Record<string, any>;
}

/**
 * Template node data
 */
export interface TemplateNodeData {
  templateId: string;
  templateType: TemplateType;
  variables: Record<string, any>;
}

/**
 * Template types
 */
export enum TemplateType {
  PROMPT = 'prompt',
  WORKFLOW = 'workflow',
  TASK = 'task',
  CUSTOM = 'custom',
}

// ============================================================================
// Workflow Definition
// ============================================================================

/**
 * Complete workflow definition
 */
export interface Workflow {
  id: string;
  name: string;
  description?: string;
  nodes: BaseNodeData[];
  edges: Edge[];
  version: number;
  createdAt: string;
  updatedAt: string;
}

/**
 * Workflow execution context
 */
export interface WorkflowExecutionContext {
  workflowId: string;
  executionId: string;
  status: ExecutionStatus;
  startTime: string;
  endTime?: string;
  currentNodeId?: string;
  results: ExecutionResult[];
  error?: string;
}

/**
 * Execution status
 */
export enum ExecutionStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

/**
 * Execution result
 */
export interface ExecutionResult {
  nodeId: string;
  nodeName: string;
  status: 'success' | 'error';
  output?: any;
  error?: string;
  duration: number;
  timestamp: string;
}

// ============================================================================
// Node Configuration
// ============================================================================

/**
 * Node configuration schema
 */
export interface NodeConfigSchema {
  type: string;
  properties: ConfigProperty[];
  required: string[];
}

/**
 * Configuration property
 */
export interface ConfigProperty {
  name: string;
  type: PropertyType;
  label: string;
  description?: string;
  default?: any;
  required?: boolean;
  options?: ConfigOption[];
  validation?: ValidationRule[];
}

/**
 * Property types
 */
export enum PropertyType {
  STRING = 'string',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  SELECT = 'select',
  MULTI_SELECT = 'multi_select',
  TEXTAREA = 'textarea',
  JSON = 'json',
  ARRAY = 'array',
  OBJECT = 'object',
}

/**
 * Configuration option
 */
export interface ConfigOption {
  value: any;
  label: string;
  description?: string;
}

/**
 * Validation rule
 */
export interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'pattern' | 'custom';
  value?: any;
  message?: string;
}

// ============================================================================
// Workflow Validation
// ============================================================================

/**
 * Workflow validation result
 */
export interface WorkflowValidation {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

/**
 * Validation error
 */
export interface ValidationError {
  nodeId: string;
  field: string;
  message: string;
  severity: 'error' | 'warning';
}

/**
 * Validation warning
 */
export interface ValidationWarning {
  nodeId: string;
  message: string;
  suggestion?: string;
}

// ============================================================================
// Workflow Execution API
// ============================================================================

/**
 * Execute workflow request
 */
export interface ExecuteWorkflowRequest {
  workflowId: string;
  inputs?: Record<string, any>;
  options?: ExecutionOptions;
}

/**
 * Execution options
 */
export interface ExecutionOptions {
  timeout?: number;
  maxIterations?: number;
  debug?: boolean;
  saveResults?: boolean;
}

/**
 * Execute workflow response
 */
export interface ExecuteWorkflowResponse {
  executionId: string;
  status: ExecutionStatus;
  workflowId: string;
  startTime: string;
  estimatedDuration?: number;
}

// ============================================================================
// Workflow Templates
// ============================================================================

/**
 * Workflow template
 */
export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: TemplateCategory;
  thumbnail?: string;
  nodes: BaseNodeData[];
  edges: Edge[];
  isPublic: boolean;
}

/**
 * Template categories
 */
export enum TemplateCategory {
  AGENT_ORCHESTRATION = 'agent_orchestration',
  DATA_PROCESSING = 'data_processing',
  CODE_GENERATION = 'code_generation',
  RESEARCH = 'research',
  CUSTOM = 'custom',
}

// ============================================================================
// Node Palette
// ============================================================================

/**
 * Node palette item
 */
export interface NodePaletteItem {
  type: NodeType;
  label: string;
  icon: string;
  category: NodeCategory;
  description: string;
  defaultConfig?: Record<string, any>;
}

/**
 * Node categories
 */
export enum NodeCategory {
  AGENTS = 'agents',
  TOOLS = 'tools',
  MEMORY = 'memory',
  LOGIC = 'logic',
  CONNECTORS = 'connectors',
  LLM = 'llm',
  IO = 'io',
  TEMPLATES = 'templates',
}

// ============================================================================
// Workflow History
// ============================================================================

/**
 * Workflow execution history
 */
export interface WorkflowHistory {
  executionId: string;
  workflowId: string;
  workflowName: string;
  status: ExecutionStatus;
  duration: number;
  startTime: string;
  endTime?: string;
  success: boolean;
}

// ============================================================================
// Export Types
// ============================================================================

/**
 * Workflow export format
 */
export type WorkflowExportFormat = 'json' | 'yaml' | 'python';

/**
 * Exported workflow
 */
export interface ExportedWorkflow {
  format: WorkflowExportFormat;
  content: string;
  exportedAt: string;
}
