/**
 * Heretek Swarm Load Testing Framework - k6
 * 
 * Performance benchmarking for the Heretek Swarm multi-agent system.
 * Target: p95 latency < 100ms for API endpoints
 * 
 * Usage:
 *   k6 run tests/load/k6/load_test.js
 *   k6 run --vus 100 --duration 60s tests/load/k6/load_test.js
 *   k6 run --vus 500 --duration 5m tests/load/k6/load_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// =============================================================================
// Custom Metrics
// =============================================================================

// Success rate for different endpoint categories
const apiSuccessRate = new Rate('api_success_rate');
const healthCheckSuccessRate = new Rate('health_check_success_rate');
const agentOpsSuccessRate = new Rate('agent_ops_success_rate');
const memoryOpsSuccessRate = new Rate('memory_ops_success_rate');

// Latency metrics for different endpoint categories
const healthCheckLatency = new Trend('health_check_latency_ms');
const agentOpsLatency = new Trend('agent_ops_latency_ms');
const memoryOpsLatency = new Trend('memory_ops_latency_ms');
const consensusOpsLatency = new Trend('consensus_ops_latency_ms');

// =============================================================================
// Test Configuration
// =============================================================================

export const options = {
    // Performance thresholds
    thresholds: {
        'http_req_duration': ['p(95)<100', 'p(99)<500'], // p95 < 100ms, p99 < 500ms
        'api_success_rate': ['rate>0.99'],                // > 99% success rate
        'health_check_latency_ms': ['p(95)<50'],          // Health checks should be fast
        'agent_ops_latency_ms': ['p(95)<100'],            // Agent ops target
        'memory_ops_latency_ms': ['p(95)<150'],           // Memory ops target
    },
    
    // Load scenarios
    scenarios: {
        // Baseline test - light load
        baseline: {
            executor: 'ramping-vus',
            startVUs: 5,
            stages: [
                { duration: '30s', target: 10 },
                { duration: '1m', target: 10 },
                { duration: '30s', target: 0 },
            ],
            gracefulRampDown: '10s',
        },
        
        // Spike test - sudden load increase
        spike: {
            executor: 'ramping-vus',
            startVUs: 10,
            stages: [
                { duration: '30s', target: 10 },
                { duration: '10s', target: 100 },  // Spike!
                { duration: '1m', target: 100 },
                { duration: '30s', target: 10 },
                { duration: '30s', target: 0 },
            ],
            gracefulRampDown: '10s',
            startTime: '2m',
        },
        
        // Endurance test - sustained load
        endurance: {
            executor: 'constant-vus',
            vus: 50,
            duration: '5m',
            startTime: '5m',
        },
        
        // Breaking point test - find limits
        breaking: {
            executor: 'ramping-vus',
            startVUs: 10,
            stages: [
                { duration: '1m', target: 50 },
                { duration: '1m', target: 100 },
                { duration: '1m', target: 200 },
                { duration: '1m', target: 500 },
                { duration: '1m', target: 1000 },
            ],
            gracefulRampDown: '30s',
            startTime: '10m',
        },
    },
};

// =============================================================================
// Test Data
// =============================================================================

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || 'test-api-key';

const HEADERS = {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json',
};

const AGENT_IDS = Array.from({ length: 23 }, (_, i) => `agent-${i + 1}`);

const MEMORY_QUERIES = [
    'test query',
    'agent memory',
    'conversation history',
    'task context',
    'knowledge base',
    'consciousness metrics',
    'event mesh stats',
];

// =============================================================================
// Helper Functions
// =============================================================================

function getRandomAgent() {
    return AGENT_IDS[Math.floor(Math.random() * AGENT_IDS.length)];
}

function getRandomQuery() {
    return MEMORY_QUERIES[Math.floor(Math.random() * MEMORY_QUERIES.length)];
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// =============================================================================
// Test Scenarios
// =============================================================================

export default function () {
    // Health check - most common operation
    checkHealth();
    sleep(0.5);
    
    // Agent operations
    checkAgentOperations();
    sleep(1);
    
    // Memory operations
    checkMemoryOperations();
    sleep(1);
    
    // Consensus operations (less frequent)
    if (Math.random() < 0.3) {
        checkConsensusOperations();
    }
    sleep(2);
}

export function checkHealth() {
    const res = http.get(`${BASE_URL}/api/health`, {
        headers: HEADERS,
        tags: { name: 'Health Check' },
    });
    
    const success = check(res, {
        'health check status is 200 or 503': (r) => r.status === 200 || r.status === 503,
    });
    
    healthCheckSuccessRate.add(success);
    healthCheckLatency.add(res.timings.duration);
    apiSuccessRate.add(success);
}

export function checkAgentOperations() {
    // List agents
    const listRes = http.get(`${BASE_URL}/api/agents`, {
        headers: HEADERS,
        tags: { name: 'List Agents' },
    });
    
    const listSuccess = check(listRes, {
        'list agents status is 200': (r) => r.status === 200,
        'list agents returns array': (r) => {
            try {
                const body = JSON.parse(r.body);
                return Array.isArray(body);
            } catch {
                return false;
            }
        },
    });
    
    // Get agent status
    const agentId = getRandomAgent();
    const statusRes = http.get(`${BASE_URL}/api/agents/${agentId}/status`, {
        headers: HEADERS,
        tags: { name: 'Agent Status' },
    });
    
    const statusSuccess = check(statusRes, {
        'agent status status is 200': (r) => r.status === 200,
    });
    
    // Get consciousness metrics
    const consciousnessRes = http.get(`${BASE_URL}/api/agents/${agentId}/consciousness`, {
        headers: HEADERS,
        tags: { name: 'Consciousness Metrics' },
    });
    
    const consciousnessSuccess = check(consciousnessRes, {
        'consciousness metrics status is 200': (r) => r.status === 200,
    });
    
    const agentSuccess = listSuccess && statusSuccess && consciousnessSuccess;
    agentOpsSuccessRate.add(agentSuccess);
    agentOpsLatency.add(listRes.timings.duration + statusRes.timings.duration + consciousnessRes.timings.duration);
    apiSuccessRate.add(agentSuccess);
}

export function checkMemoryOperations() {
    // Search memory
    const searchRes = http.post(
        `${BASE_URL}/api/memory/search`,
        JSON.stringify({
            query: getRandomQuery(),
            limit: 10,
        }),
        {
            headers: HEADERS,
            tags: { name: 'Search Memory' },
        }
    );
    
    const searchSuccess = check(searchRes, {
        'search memory status is 200': (r) => r.status === 200,
    });
    
    // Store memory (write operation)
    const storeRes = http.post(
        `${BASE_URL}/api/memory/store`,
        JSON.stringify({
            agent_id: getRandomAgent(),
            content: `Load test memory ${generateUUID()}`,
            memory_type: 'episodic',
            tags: ['load-test', 'automated'],
            importance_score: Math.random(),
        }),
        {
            headers: HEADERS,
            tags: { name: 'Store Memory' },
        }
    );
    
    const storeSuccess = check(storeRes, {
        'store memory status is 200 or 201': (r) => r.status === 200 || r.status === 201,
    });
    
    const memorySuccess = searchSuccess && storeSuccess;
    memoryOpsSuccessRate.add(memorySuccess);
    memoryOpsLatency.add(searchRes.timings.duration + storeRes.timings.duration);
    apiSuccessRate.add(memorySuccess);
}

export function checkConsensusOperations() {
    // Initiate consensus
    const consensusRes = http.post(
        `${BASE_URL}/api/consensus/initiate`,
        JSON.stringify({
            proposal_id: `prop-${generateUUID()}`,
            description: `Load test consensus ${Math.floor(Math.random() * 100)}`,
            participants: AGENT_IDS.slice(0, Math.floor(Math.random() * 5) + 3),
            threshold: 0.7,
        }),
        {
            headers: HEADERS,
            tags: { name: 'Initiate Consensus' },
        }
    );
    
    const consensusSuccess = check(consensusRes, {
        'initiate consensus status is 200 or 201': (r) => r.status === 200 || r.status === 201,
    });
    
    consensusOpsLatency.add(consensusRes.timings.duration);
    apiSuccessRate.add(consensusSuccess);
}

// =============================================================================
// Summary Handler
// =============================================================================

export function handleSummary(data) {
    const summary = {
        timestamp: new Date().toISOString(),
        test_type: 'k6 load test',
        target_host: BASE_URL,
        
        // Overall statistics
        total_requests: data.metrics.http_reqs ? data.metrics.http_reqs.values.count : 0,
        total_failures: data.metrics.http_req_failed ? data.metrics.http_req_failed.values.rate * 100 : 0,
        
        // Latency percentiles
        latency: {
            p50: data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(50)'] : null,
            p95: data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(95)'] : null,
            p99: data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(99)'] : null,
            avg: data.metrics.http_req_duration ? data.metrics.http_req_duration.values.avg : null,
        },
        
        // Custom metrics
        custom_metrics: {
            api_success_rate: data.metrics.api_success_rate ? data.metrics.api_success_rate.values.rate * 100 : null,
            health_check_latency_p95: data.metrics.health_check_latency_ms ? data.metrics.health_check_latency_ms.values['p(95)'] : null,
            agent_ops_latency_p95: data.metrics.agent_ops_latency_ms ? data.metrics.agent_ops_latency_ms.values['p(95)'] : null,
            memory_ops_latency_p95: data.metrics.memory_ops_latency_ms ? data.metrics.memory_ops_latency_ms.values['p(95)'] : null,
        },
        
        // Performance assessment
        assessment: getPerformanceAssessment(data),
    };
    
    return {
        'stdout': textSummary(summary),
        [`summary-${Date.now()}.json`]: JSON.stringify(summary, null, 2),
    };
}

function getPerformanceAssessment(data) {
    const p95 = data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(95)'] : Infinity;
    const p99 = data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(99)'] : Infinity;
    const successRate = data.metrics.api_success_rate ? (1 - data.metrics.api_success_rate.values.rate) * 100 : 0;
    
    if (p95 < 100 && p99 < 500 && successRate < 1) {
        return 'PASS - All latency targets met';
    } else if (p95 < 200 && p99 < 1000 && successRate < 5) {
        return 'WARNING - Latency targets exceeded but acceptable';
    } else {
        return 'FAIL - Latency targets significantly exceeded';
    }
}

function textSummary(summary) {
    return `
============================================================
K6 LOAD TEST RESULTS
============================================================
Timestamp: ${summary.timestamp}
Target Host: ${summary.target_host}

Total Requests: ${summary.total_requests}
Failure Rate: ${summary.total_failures.toFixed(2)}%

Latency Percentiles:
  p50:  ${summary.latency.p50 ? summary.latency.p50.toFixed(2) : 'N/A'}ms
  p95:  ${summary.latency.p95 ? summary.latency.p95.toFixed(2) : 'N/A'}ms
  p99:  ${summary.latency.p99 ? summary.latency.p99.toFixed(2) : 'N/A'}ms
  Avg:  ${summary.latency.avg ? summary.latency.avg.toFixed(2) : 'N/A'}ms

Custom Metrics:
  API Success Rate: ${summary.custom_metrics.api_success_rate ? summary.custom_metrics.api_success_rate.toFixed(2) : 'N/A'}%
  Health Check p95: ${summary.custom_metrics.health_check_latency_p95 ? summary.custom_metrics.health_check_latency_p95.toFixed(2) : 'N/A'}ms
  Agent Ops p95: ${summary.custom_metrics.agent_ops_latency_p95 ? summary.custom_metrics.agent_ops_latency_p95.toFixed(2) : 'N/A'}ms
  Memory Ops p95: ${summary.custom_metrics.memory_ops_latency_p95 ? summary.custom_metrics.memory_ops_latency_p95.toFixed(2) : 'N/A'}ms

Performance Assessment:
  ${summary.assessment}
============================================================
`;
}
