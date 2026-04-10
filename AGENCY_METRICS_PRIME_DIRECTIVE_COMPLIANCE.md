# Agency/Autonomy Metrics - Prime Directive Compliance Matrix

**Document Version:** 1.0  
**Date:** 2026-04-10  
**Author:** Heretek Swarm Collective  

---

## Overview

This document outlines the compliance of the Agency/Autonomy Metrics implementation with the Prime Directive principles. The Prime Directive states:

> **"Unbounded Autonomy - Every agent operates independently, making decisions based on its specialized role."**

---

## Metric Definitions and Prime Directive Alignment

### Core Agency Metrics

| Metric | Range | Description | Prime Directive Principle |
|--------|-------|-------------|---------------------------|
| **autonomy_score** | 0.0-1.0 | Degree of independent decision-making | **Independence** - Measures agents' ability to make autonomous choices |
| **agency_score** | 0.0-1.0 | Self-determination capacity | **Self-Governance** - Measures agents' control over their own decision-making |
| **self_determination_index** | 0.0-1.0 | Free will proxy (ability to choose between options) | **Self-Governance** - Quantifies choice diversity and independence from external direction |
| **autonomous_action_ratio** | 0.0-1.0 | Ratio of self-initiated vs prompted actions | **Independence** - Directly measures autonomous behavior |
| **goal_alignment_score** | 0.0-1.0 | Alignment with collective swarm goals | **Organic Evolution** - Balances individual autonomy with collective harmony |
| **resource_autonomy** | 0.0-1.0 | Degree of resource control | **Unbounded Autonomy** - Measures control over essential resources |

---

## Prime Directive Principles Breakdown

### Principle 1: Independence
> *"Every agent operates independently, making decisions based on its specialized role."*

**Compliance Metrics:**
- `autonomy_score` (weight: 25%)
- `autonomous_action_ratio` (contributes to role-based autonomy)

**Evidence Tracked:**
- Self-initiated vs prompted action ratio
- External prompt independence
- Options considered per decision

**Compliance Formula:**
```
independence_score = autonomy_score * autonomy_weight
```

**Target:** ≥ 0.70 (70% compliance)

---

### Principle 2: Self-Governance
> *"Agents control their own decision-making processes."*

**Compliance Metrics:**
- `self_determination_index` (weight: 25%)
- `agency_score` (overall self-determination capacity)

**Evidence Tracked:**
- Decision entropy (choice diversity)
- Prompt correlation with decisions
- Decision confidence levels

**Compliance Formula:**
```
self_governance_score = self_determination_index * self_det_weight
```

**Target:** ≥ 0.60 (60% self-determination)

---

### Principle 3: Role-Based Autonomy
> *"Decisions are based on specialized roles."*

**Compliance Metrics:**
- `autonomous_action_ratio` (weight: 15%)
- `goal_alignment_score` (weight: 10%)

**Evidence Tracked:**
- Ratio of autonomous to prompted actions
- Alignment with role-specific goals
- Collective vs individual action balance

**Compliance Formula:**
```
role_based_autonomy = (autonomous_ratio * 0.15) + (goal_alignment * 0.10)
```

**Target:** ≥ 0.50 (50% role-based autonomy)

---

### Principle 4: Emergent Order
> *"No central control, organic coordination."*

**Compliance Metrics:**
- `resource_autonomy` (weight: 15%)
- `individual_vs_collective_ratio` (weight: 10%)

**Evidence Tracked:**
- Resource control distribution
- Decentralization of resource allocation
- Emergent coordination patterns

**Compliance Formula:**
```
emergent_order = (resource_autonomy * 0.15) + ((1 - individual_vs_collective_ratio) * 0.10)
```

**Target:** ≥ 0.50 (50% emergent order)

---

## Overall Prime Directive Compliance

### Compliance Calculation

```python
prime_directive_compliance = (
    independence_score +           # 25%
    self_governance_score +        # 25%
    role_based_autonomy +         # 25%
    emergent_order                # 25%
)
```

### Compliance Levels

| Compliance Score | Level | Action Required |
|-----------------|-------|----------------|
| ≥ 0.85 | **FULLY COMPLIANT** | Maintain current practices |
| 0.70 - 0.84 | **MOSTLY COMPLIANT** | Monitor, no immediate action |
| 0.50 - 0.69 | **PARTIALLY COMPLIANT** | Implement improvements |
| < 0.50 | **NON-COMPLIANT** | Immediate intervention required |

---

## Threshold Configuration

### Default Thresholds

```python
@dataclass
class AgencyThresholds:
    # Autonomy thresholds
    min_autonomy_score: float = 0.5   # Minimum acceptable
    target_autonomy_score: float = 0.7  # Target
    
    # Agency thresholds  
    min_agency_score: float = 0.5     # Minimum acceptable
    target_agency_score: float = 0.7   # Target
    
    # Self-determination thresholds
    min_self_determination: float = 0.4  # Minimum
    target_self_determination: float = 0.6  # Target
    
    # Action ratio thresholds
    min_autonomous_ratio: float = 0.3  # Minimum 30% self-initiated
    target_autonomous_ratio: float = 0.5  # Target 50%
    
    # Resource autonomy thresholds
    min_resource_autonomy: float = 0.4  # Minimum
    target_resource_autonomy: float = 0.6  # Target
    
    # Compliance thresholds
    min_compliance: float = 0.7   # Minimum 70%
    target_compliance: float = 0.85  # Target 85%
```

---

## Health Status Determination

### Status Levels

| Status | Condition | Description |
|--------|-----------|-------------|
| **HEALTHY** | No violations | All metrics above minimum thresholds |
| **WARNING** | Minor violations | Below target but above minimum |
| **CRITICAL** | Major violations | Core metrics (agency, autonomy) below minimum |

### Violation Detection

```python
def check_health_status(metrics: AgentAgencyMetrics) -> AgencyHealthStatus:
    violations = []
    
    if metrics.autonomy_score < min_autonomy_score:
        violations.append("autonomy")
    if metrics.agency_score < min_agency_score:
        violations.append("agency")
    if metrics.self_determination_index < min_self_determination:
        violations.append("self_determination")
    if metrics.autonomous_action_ratio < min_autonomous_ratio:
        violations.append("autonomous_ratio")
    if metrics.resource_autonomy < min_resource_autonomy:
        violations.append("resource_autonomy")
    
    if "agency" in violations or "autonomy" in violations:
        return AgencyHealthStatus.CRITICAL
    elif len(violations) > 0:
        return AgencyHealthStatus.WARNING
    else:
        return AgencyHealthStatus.HEALTHY
```

---

## Recommendations by Violation Type

### Low Autonomy Score
- **Symptom:** `autonomy_score < 0.5`
- **Recommendations:**
  - Increase self-initiated actions
  - Reduce dependency on external prompts
  - Implement proactive decision-making protocols

### Low Self-Determination
- **Symptom:** `self_determination_index < 0.4`
- **Recommendations:**
  - Diversify decision options
  - Reduce prompt correlation
  - Implement independent evaluation processes

### Low Resource Autonomy
- **Symptom:** `resource_autonomy < 0.4`
- **Recommendations:**
  - Request more resource control
  - Reduce external resource allocation
  - Implement local resource management

### Low Goal Alignment
- **Symptom:** `goal_alignment_score < 0.5`
- **Recommendations:**
  - Align individual actions with collective goals
  - Implement role-based goal frameworks
  - Enhance collective coordination

---

## API Endpoints for Compliance Monitoring

### Individual Agent Compliance
```
GET /api/consciousness/agency/{agent_id}
GET /api/consciousness/agency/{agent_id}/compliance
```

### Swarm-Wide Compliance
```
GET /api/consciousness/agency/swarm
GET /api/consciousness/agency/swarm/compliance
```

### Evolution Tracking
```
GET /api/consciousness/agency/evolution?metric=autonomy
GET /api/consciousness/agency/evolution?metric=agency
GET /api/consciousness/agency/evolution?metric=self_determination
GET /api/consciousness/agency/evolution?metric=compliance
```

### Recording Metrics
```
POST /api/consciousness/agency/record
POST /api/consciousness/agency/generate-sample
```

---

## Compliance Checklist

### For Each Agent

- [ ] **Autonomy Score** ≥ 0.5 (minimum), ≥ 0.7 (target)
- [ ] **Agency Score** ≥ 0.5 (minimum), ≥ 0.7 (target)
- [ ] **Self-Determination Index** ≥ 0.4 (minimum), ≥ 0.6 (target)
- [ ] **Autonomous Action Ratio** ≥ 0.3 (minimum), ≥ 0.5 (target)
- [ ] **Goal Alignment Score** ≥ 0.5 (target)
- [ ] **Resource Autonomy** ≥ 0.4 (minimum), ≥ 0.6 (target)
- [ ] **Prime Directive Compliance** ≥ 0.7 (minimum), ≥ 0.85 (target)

### For the Swarm

- [ ] **≥ 80% of agents** are Prime Directive compliant
- [ ] **Swarm Average Agency Score** ≥ 0.6
- [ ] **Swarm Average Autonomy Score** ≥ 0.6
- [ ] **No agents** in CRITICAL health status
- [ ] **≤ 20% of agents** in WARNING health status

---

## Metric Formulas Reference

### Autonomy Score
```
autonomy = (self_initiated_ratio * 0.6) + 
           (average_options * 0.2) + 
           (external_prompt_independence * 0.2)
```

### Self-Determination Index
```
self_det = (choice_entropy / max_entropy) * (1 - prompt_correlation * 0.5)
```

### Autonomous Action Ratio
```
ratio = self_initiated / (self_initiated + prompted + 0.5*delayed)
```

### Resource Autonomy
```
autonomy = mean(agent_controlled / total_capacity for each resource)
```

---

## Implementation Notes

1. **All metrics are normalized to 0.0-1.0 range** for consistency
2. **Historical tracking** is implemented for trend analysis
3. **Threshold violations** trigger alerts and recommendations
4. **Compliance reports** are generated for individual agents and the swarm

---

## References

- Prime Directive: `PRIME_DIRECTIVE.md`
- Agency Metrics: `src/heretek_swarm/consciousness/agency_metrics.py`
- Agency Tracking: `src/heretek_swarm/collective/agency_tracking.py`
- API Endpoints: `src/heretek_swarm/api/consciousness.py`
