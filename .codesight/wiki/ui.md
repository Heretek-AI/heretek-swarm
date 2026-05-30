# UI

> **Navigation aid.** Component inventory and prop signatures extracted via AST. Read the source files before adding props or modifying component logic.

**89 components** (react)

## Client Components

- **ExampleCanvas** — `heretek-swarm\apps\app\src\components\example-canvas\index.tsx`
- **TodoCard** — props: todo, onToggleStatus, onDelete, onUpdateTitle, onUpdateDescription, onUpdateEmoji — `heretek-swarm\apps\app\src\components\example-canvas\todo-card.tsx`
- **TodoColumn** — props: title, todos, emptyMessage, showAddButton, onAddTodo, onToggleStatus, onDelete, onUpdateTitle, onUpdateDescription, onUpdateEmoji — `heretek-swarm\apps\app\src\components\example-canvas\todo-column.tsx`
- **TodoList** — props: todos, onUpdate, isAgentRunning — `heretek-swarm\apps\app\src\components\example-canvas\todo-list.tsx`
- **ExampleLayout** — props: chatContent, appContent — `heretek-swarm\apps\app\src\components\example-layout\index.tsx`
- **ThreadsDrawer** — props: agentId, threadId, onThreadChange — `heretek-swarm\apps\app\src\components\threads-drawer\threads-drawer.tsx`
- **ToolReasoning** — props: name, args, status — `heretek-swarm\apps\app\src\components\tool-rendering.tsx`
- **ActionButton** — props: label, doneLabel, action — `heretek-swarm\apps\app\src\declarative-generative-ui\renderers.tsx`
- **ThemeProvider** — `heretek-swarm\apps\app\src\hooks\use-theme.tsx`

## Components

- **App** — `heretek-swarm\apps\app\src\App.tsx`
- **ModeToggle** — props: mode, onModeChange — `heretek-swarm\apps\app\src\components\example-layout\mode-toggle.tsx`
- **BarChart** — props: title, description, data — `heretek-swarm\apps\app\src\components\generative-ui\charts\bar-chart.tsx`
- **PieChart** — props: title, description, data — `heretek-swarm\apps\app\src\components\generative-ui\charts\pie-chart.tsx`
- **MeetingTimePicker** — props: status, respond, reasonForScheduling, meetingDuration, title, timeSlots — `heretek-swarm\apps\app\src\components\generative-ui\meeting-time-picker.tsx`
- **HeadlessChat** — `heretek-swarm\apps\app\src\components\headless-chat.tsx`
- **Spinner** — props: className, size — `heretek-swarm\apps\app\src\components\ui\spinner.tsx`
- **DashboardContent** — `swarm-dashboard\src\App.tsx`
- **AgentMetricsGrid** — props: apiBaseUrl, refreshInterval, showFilters, showPagination, pageSize, onAgentSelect — `swarm-dashboard\src\components\AgentMetricsGrid.tsx`
- **AgentCard** — props: agent, instances, onDeploy, onStart, onStop, onSelect, compact — `swarm-dashboard\src\components\Agents\AgentCard.tsx`
- **AgentConfigPanel** — props: instanceId, config, onUpdate, onClose — `swarm-dashboard\src\components\Agents\AgentConfigPanel.tsx`
- **AgentControls** — props: instanceId, state, onStart, onStop, onSuspend, onResume, onRemove, compact — `swarm-dashboard\src\components\Agents\AgentControls.tsx`
- **AgentsPage** — `swarm-dashboard\src\components\Agents\AgentsPage.tsx`
- **DeployAgentModal** — props: agentType, isOpen, onClose, onDeploy — `swarm-dashboard\src\components\Agents\DeployAgentModal.tsx`
- **AgentDetailDrawer** — props: agentId, onClose — `swarm-dashboard\src\components\Canvas\AgentDetailDrawer.tsx`
- **AgentNode** — props: id, data, selected — `swarm-dashboard\src\components\Canvas\AgentNode.tsx`
- **CollectiveCanvas** — `swarm-dashboard\src\components\Canvas\Canvas.tsx`
- **CanvasToolbar** — props: onZoomIn, onZoomOut, onFitView, onSaveWorkflow, onLoadWorkflow, onExecuteWorkflow, onClearCanvas, onToggleGrid, gridEnabled, isExecuting — `swarm-dashboard\src\components\Canvas\CanvasToolbar.tsx`
- **ConnectionEdge** — props: id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, style — `swarm-dashboard\src\components\Canvas\ConnectionEdge.tsx`
- **EnhancedCanvas** — `swarm-dashboard\src\components\Canvas\EnhancedCanvas.tsx`
- **TRIAD_CONFIGS** — props: initialNodes, initialEdges, onSave, onExecute — `swarm-dashboard\src\components\Canvas\FlowCanvas.tsx`
- **MetricsOverlay** — props: consciousness, swarmHealth, metricsLoading, onClose — `swarm-dashboard\src\components\Canvas\MetricsOverlay.tsx`
- **NodeConfigPanel** — props: node, onClose, onSave — `swarm-dashboard\src\components\Canvas\NodeConfigPanel.tsx`
- **NodePalette** — props: onDragStart, searchPlaceholder, showTierHeaders — `swarm-dashboard\src\components\Canvas\NodePalette.tsx`
- **ChatInterface** — `swarm-dashboard\src\components\Chat\ChatInterface.tsx`
- **MessageInput** — props: onSendMessage, agents, disabled, placeholder, showAgentSelector, showTypeSelector, defaultAgentId, defaultMessageType, minRows, maxRows — `swarm-dashboard\src\components\Chat\MessageInput.tsx`
- **MessageList** — props: messages, onMessageClick, showTimestamps, showAgentIcons, showFilter, autoScroll, loading — `swarm-dashboard\src\components\Chat\MessageList.tsx`
- **AgentStatusGrid** — props: agents, onAgentClick, showDescriptions, compact — `swarm-dashboard\src\components\Consciousness\AgentStatusGrid.tsx`
- **ConsciousnessDashboard** — `swarm-dashboard\src\components\Consciousness\ConsciousnessDashboard.tsx`
- **ConsciousnessGauge** — props: gwtValue, iitValue, astValue, fepValue, size, showLabels, animated — `swarm-dashboard\src\components\Consciousness\ConsciousnessGauge.tsx`
- **ConsciousnessPage** — `swarm-dashboard\src\components\Consciousness\ConsciousnessPage.tsx`
- **RealTimeAgentPanel** — props: refreshInterval, showConsciousness — `swarm-dashboard\src\components\Consciousness\RealTimeAgentPanel.tsx`
- **ConsciousnessMetricsPanel** — props: apiBaseUrl, refreshInterval, onMetricsUpdate — `swarm-dashboard\src\components\ConsciousnessMetricsPanel.tsx`
- **Dashboard** — `swarm-dashboard\src\components\Dashboard\Dashboard.tsx`
- **DashboardLayout** — props: activeNav, onNavClick, navItems, systemStatus, userName, showHeader, showFooter — `swarm-dashboard\src\components\Dashboard\Layout.tsx`
- **UnifiedDashboard** — `swarm-dashboard\src\components\Dashboard\UnifiedDashboard.tsx`
- **DeliberationPage** — `swarm-dashboard\src\components\Deliberation\DeliberationPage.tsx`
- **HistoricalDeliberations** — `swarm-dashboard\src\components\Deliberation\HistoricalDeliberations.tsx`
- **LiveDeliberationPanel** — props: className — `swarm-dashboard\src\components\Deliberation\LiveDeliberationPanel.tsx`
- **HomePage** — `swarm-dashboard\src\components\Home\HomePage.tsx`
- **LogsPage** — `swarm-dashboard\src\components\Logs\LogsPage.tsx`
- **A2AMessageFlow** — props: agentId, timeRange — `swarm-dashboard\src\components\Observability\A2AMessageFlow.tsx`
- **A2ATracker** — props: natsUrl, refreshInterval, maxMessages — `swarm-dashboard\src\components\Observability\A2ATracker.tsx`
- **ExternalCallsPanel** — props: maxEntries, refreshInterval — `swarm-dashboard\src\components\Observability\ExternalCallsPanel.tsx`
- **LLMTrace** — props: agentId, timeRange — `swarm-dashboard\src\components\Observability\LLMTrace.tsx`
- **Observability** — `swarm-dashboard\src\components\Observability\Observability.tsx`
- **ObservabilityPage** — `swarm-dashboard\src\components\Observability\ObservabilityPage.tsx`
- **PerformancePanel** — `swarm-dashboard\src\components\PerformancePanel.tsx`
- **AgentDefaultsSection** — props: onConfigChange — `swarm-dashboard\src\components\Settings\AgentDefaultsSection.tsx`
- **DeveloperModeToggle** — props: onDeveloperModeChange — `swarm-dashboard\src\components\Settings\DeveloperModeToggle.tsx`
- **ImportExportSection** — props: onImportExport — `swarm-dashboard\src\components\Settings\ImportExportSection.tsx`
- **MCPToolsSection** — `swarm-dashboard\src\components\Settings\MCPToolsSection.tsx`
- **ModelGarage** — `swarm-dashboard\src\components\Settings\ModelGarage.tsx`
- **SettingsPage** — props: onRerunSetup — `swarm-dashboard\src\components\Settings\SettingsPage.tsx`
- **SystemConfigSection** — props: onConfigChange — `swarm-dashboard\src\components\Settings\SystemConfigSection.tsx`
- **SetupWizard** — props: onComplete — `swarm-dashboard\src\components\Setup\SetupWizard.tsx`
- **SwarmControlCenter** — props: defaultView, natsUrl, apiUrl — `swarm-dashboard\src\components\SwarmControlCenter.tsx`
- **SwarmHealthDashboard** — props: apiBaseUrl, refreshInterval, showAgentDetails, showAlerts — `swarm-dashboard\src\components\SwarmHealthDashboard.tsx`
- **ErrorFallback** — props: fallback, onError, className, componentName, logToBackend, retryable — `swarm-dashboard\src\components\UI\ComponentErrorBoundary.tsx`
- **DataTable** — `swarm-dashboard\src\components\UI\DataTable.tsx`
- **DebugPanel** — props: className — `swarm-dashboard\src\components\UI\DebugPanel.tsx`
- **EmptyState** — props: icon, title, description, action, label, onClick — `swarm-dashboard\src\components\UI\EmptyState.tsx`
- **SimpleErrorFallback** — props: fallback, onError, className — `swarm-dashboard\src\components\UI\ErrorBoundary.tsx`
- **LoadingSpinner** — props: size, message, fullScreen, className — `swarm-dashboard\src\components\UI\LoadingSpinner.tsx`
- **MetricCard** — props: title, value, change, changeLabel, icon, sparklineData, color, size, className, tooltip — `swarm-dashboard\src\components\UI\MetricCard.tsx`
- **PerformanceOverlay** — props: className, position — `swarm-dashboard\src\components\UI\PerformanceOverlay.tsx`
- **StatusBadge** — props: status, size, showLabel, className — `swarm-dashboard\src\components\UI\StatusBadge.tsx`
- **LLM_PROVIDERS** — props: node, id, type, data, agentId, agentType, config — `swarm-dashboard\src\components\Workflow\NodeConfigPanel.tsx`
- **AgentNode** — props: data, selected — `swarm-dashboard\src\components\WorkflowBuilder\AgentNode.tsx`
- **ConnectorNode** — props: data, selected — `swarm-dashboard\src\components\WorkflowBuilder\ConnectorNode.tsx`
- **DecisionNode** — props: data, selected — `swarm-dashboard\src\components\WorkflowBuilder\DecisionNode.tsx`
- **HandleTooltip** — props: channelName, channelType, dataType, description — `swarm-dashboard\src\components\WorkflowBuilder\DynamicHandles.tsx`
- **LLMNode** — props: data, selected — `swarm-dashboard\src\components\WorkflowBuilder\LLMNode.tsx`
- **MemoryNode** — props: data, selected — `swarm-dashboard\src\components\WorkflowBuilder\MemoryNode.tsx`
- **CollapseIcon** — props: group, selected, onClick, onDelete, onNameChange, onToggleCollapse, colorScheme — `swarm-dashboard\src\components\WorkflowBuilder\NodeGroup.tsx`
- **ToolNode** — props: data, selected — `swarm-dashboard\src\components\WorkflowBuilder\ToolNode.tsx`
- **ValidationPanel** — props: result, isOpen, onClose, onNodeSelect, onEdgeSelect — `swarm-dashboard\src\components\WorkflowBuilder\ValidationPanel.tsx`
- **WorkflowBuilder** — props: nodes, edges, onNodesChange, onEdgesChange, onConnect, onNodeClick, onPaneClick, nodeTypes, onDrop — `swarm-dashboard\src\components\WorkflowBuilder\WorkflowBuilder.tsx`
- **WorkflowList** — props: isOpen, onClose, onLoad, onReExecute, onRefresh — `swarm-dashboard\src\components\WorkflowBuilder\WorkflowList.tsx`
- **DockerStatusIndicator** — props: status, size — `swarm-dashboard\src\hooks\useDockerDetection.tsx`

---
_Back to [overview.md](./overview.md)_