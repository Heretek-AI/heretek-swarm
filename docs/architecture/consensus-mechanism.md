# Consensus Mechanism Documentation

## Overview

The Consensus Mechanism implements the MAKER (Multi-Agent Knowledge Extraction & Reasoning) algorithm for robust decision aggregation across multiple agents. It provides first-to-ahead-by-k voting, red-flagging for anomalous outputs, reputation-weighted voting, and statistical validation.

## Core Architecture

### MAKER Consensus Algorithm

**Location**: [`src/heretek_swarm/consensus/maker.py`](../src/heretek_swarm/consensus/maker.py)

The [`MAKERConsensus`](../src/heretek_swarm/consensus/maker.py:78) class implements a sophisticated consensus mechanism designed for multi-agent systems.

### Key Features

1. **First-to-Ahead-by-K Voting**: A decision wins when it gets K votes ahead of alternatives
2. **Red-Flagging**: Automatic detection of anomalous outputs
3. **Reputation Weighting**: Agent votes weighted by historical accuracy
4. **Statistical Validation**: Confidence intervals and significance testing
5. **Flexible Thresholds**: Configurable voting parameters

## Consensus States

```python
class ConsensusState(Enum):
    GATHERING = "gathering"    # Collecting votes
    VOTING = "voting"          # Voting in progress
    AGGREGATING = "aggregating" # Computing consensus
    COMPLETED = "completed"     # Consensus reached
    FAILED = "failed"           # Consensus failed
```

## Data Structures

### Vote

```python
@dataclass
class Vote:
    """A single vote from an agent."""
    
    agent_id: str              # Agent identifier
    decision: str              # Agent's decision
    confidence: float          # Confidence level (0.0 to 1.0)
    timestamp: str             # Vote timestamp
    metadata: Dict[str, Any]   # Additional metadata
```

### ConsensusResult

```python
@dataclass
class ConsensusResult:
    """Result of a consensus process."""
    
    decision: str              # Final decision
    confidence: float          # Overall confidence
    votes: List[Vote]          # All votes cast
    state: ConsensusState      # Consensus state
    timestamp: str             # Result timestamp
    red_flags: List[str]       # Red flag messages
    metadata: Dict[str, Any]   # Additional metadata
```

## Core Methods

### Initialization

```python
consensus = MAKERConsensus(
    ahead_by_k=2,              # Votes needed to be ahead
    min_votes=3,               # Minimum votes required
    confidence_threshold=0.6,  # Minimum confidence threshold
    reputation_weights={        # Optional reputation weights
        "alpha": 1.0,
        "beta": 0.9,
        "charlie": 0.8,
    }
)
```

**Parameters**:
- `ahead_by_k`: Number of votes a decision must be ahead to win (default: 2)
- `min_votes`: Minimum number of votes required (default: 3)
- `confidence_threshold`: Minimum confidence threshold (default: 0.6)
- `reputation_weights`: Optional reputation weights per agent

### Starting Consensus

```python
consensus.start_consensus("decision-1")
```

**Parameters**:
- `consensus_id`: Unique identifier for the consensus process

### Adding Votes

```python
consensus.add_vote(
    consensus_id="decision-1",
    agent_id="alpha",
    decision="deploy",
    confidence=0.9,
    metadata={"reasoning": "tests passed"}
)
```

**Parameters**:
- `consensus_id`: Consensus process identifier
- `agent_id`: Agent submitting the vote
- `decision`: Agent's decision
- `confidence`: Confidence level (0.0 to 1.0)
- `metadata`: Optional metadata

### Computing Consensus

```python
result = consensus.compute_consensus("decision-1")

if result.state == ConsensusState.COMPLETED:
    print(f"Decision: {result.decision}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Votes: {len(result.votes)}")
    
    if result.red_flags:
        print(f"Red Flags: {result.red_flags}")
```

**Returns**: [`ConsensusResult`](../src/heretek_swarm/consensus/maker.py:55) or `None` if consensus not reached

## Voting Algorithm

### First-to-Ahead-by-K

The algorithm works as follows:

1. Collect all votes for a decision
2. Group votes by decision option
3. Count votes for each option
4. Check if any option is K votes ahead of others
5. If yes, that option wins
6. If no, continue gathering votes or fail

**Example**:

```python
# Votes: A=3, B=1, K=2
# A is ahead by 2 votes → A wins

# Votes: A=2, B=2, K=2
# A is not ahead → Continue voting
```

### Reputation Weighting

When reputation weights are provided:

1. Each vote is weighted by agent's reputation
2. Weighted votes are summed for each decision
3. Decision with highest weighted sum wins

**Example**:

```python
reputation_weights = {
    "alpha": 1.0,
    "beta": 0.9,
    "charlie": 0.8,
}

# Votes:
# - Alpha: A (1.0)
# - Beta: B (0.9)
# - Charlie: A (0.8)

# Weighted totals:
# - A: 1.0 + 0.8 = 1.8
# - B: 0.9

# A wins
```

### Confidence Calculation

Overall confidence is computed as:

```python
confidence = weighted_average(vote_confidences) * vote_consensus_factor
```

Where:
- `weighted_average`: Weighted by reputation if available
- `vote_consensus_factor`: Higher when votes are more unanimous

### Red-Flagging

Red flags are raised when:

1. **Low Confidence**: Average confidence below threshold
2. **High Variance**: High variance in confidence scores
3. **Outlier Detection**: Votes significantly different from majority
4. **Anomalous Patterns**: Unusual voting patterns

**Example**:

```python
# Red flag conditions
if average_confidence < confidence_threshold:
    red_flags.append("Low confidence")

if confidence_variance > 0.3:
    red_flags.append("High variance in opinions")

if has_outliers(votes):
    red_flags.append("Outlier votes detected")
```

## Advanced Features

### Agent Reputation Tracking

The system tracks agent reputation over time:

```python
# Update reputation based on vote accuracy
consensus.update_agent_reputation(
    agent_id="alpha",
    was_correct=True,
    confidence=0.9
)

# Get current reputation
reputation = consensus.get_agent_reputation("alpha")
```

### Vote History

Complete vote history is maintained:

```python
# Get vote history for an agent
history = consensus.get_vote_history("alpha")

# Get voting patterns
patterns = consensus.analyze_voting_patterns()
```

### Statistical Validation

Statistical tests can be applied:

```python
# Compute confidence intervals
ci = consensus.compute_confidence_interval(
    consensus_id="decision-1",
    confidence_level=0.95
)

# Perform significance test
significant = consensus.test_significance(
    consensus_id="decision-1",
    alpha=0.05
)
```

## Usage Examples

### Basic Usage

```python
from heretek_swarm import MAKERConsensus

# Initialize
consensus = MAKERConsensus(ahead_by_k=2, min_votes=3)

# Start consensus
consensus.start_consensus("deployment-decision")

# Add votes
consensus.add_vote("deployment-decision", "alpha", "deploy", 0.9)
consensus.add_vote("deployment-decision", "beta", "deploy", 0.85)
consensus.add_vote("deployment-decision", "charlie", "wait", 0.7)

# Compute result
result = consensus.compute_consensus("deployment-decision")

if result:
    print(f"Decision: {result.decision}")
    print(f"Confidence: {result.confidence:.2f}")
else:
    print("Consensus not reached")
```

### With Reputation Weights

```python
# Initialize with reputation weights
consensus = MAKERConsensus(
    ahead_by_k=2,
    min_votes=3,
    reputation_weights={
        "alpha": 1.0,
        "beta": 0.9,
        "charlie": 0.8,
    }
)

# Add votes (will be weighted automatically)
consensus.add_vote("decision-1", "alpha", "A", 0.9)
consensus.add_vote("decision-1", "beta", "B", 0.85)
consensus.add_vote("decision-1", "charlie", "A", 0.7)

# Compute result (reputation-weighted)
result = consensus.compute_consensus("decision-1")
```

### Integration with HeavySwarm

```python
from heretek_swarm import HeavySwarmWorkflow, MAKERConsensus

# Create consensus engine
consensus = MAKERConsensus(ahead_by_k=2, min_votes=3)

# Create workflow with consensus
workflow = HeavySwarmWorkflow(
    triad_agents=["alpha", "beta", "charlie"],
    consensus_engine=consensus,
)

# Execute workflow (uses consensus internally)
result = await workflow.execute(
    topic="Should we deploy to production?",
    context={"tests_passed": True}
)

# Access consensus result
print(f"Decision: {result.final_decision.decision}")
print(f"Confidence: {result.final_decision.confidence:.2f}")
```

## Best Practices

### 1. Configuration

- Set `ahead_by_k` based on number of agents
- Use `min_votes` to ensure sufficient participation
- Adjust `confidence_threshold` based on risk tolerance
- Configure reputation weights based on agent expertise

### 2. Voting

- Encourage agents to provide confidence scores
- Include reasoning in vote metadata
- Use consistent decision options
- Vote in a timely manner

### 3. Red Flags

- Monitor red flags in production
- Investigate patterns in red flags
- Adjust thresholds based on experience
- Use red flags for continuous improvement

### 4. Reputation

- Update reputation based on outcomes
- Use reputation to weight votes appropriately
- Monitor reputation changes over time
- Reset reputation if needed

## Performance Considerations

### Scalability

- Consensus computation is O(n) where n is number of votes
- Reputation tracking adds minimal overhead
- Red-flagging can be computationally expensive
- Consider batching votes for large-scale systems

### Memory Usage

- Vote history can grow over time
- Implement periodic cleanup of old votes
- Use efficient data structures for vote storage
- Consider pagination for large vote histories

### Network

- Minimize number of consensus rounds
- Use efficient serialization for votes
- Consider local caching of reputation weights
- Implement backpressure for vote submission

## Troubleshooting

### Common Issues

1. **Consensus Not Reached**
   - Check if minimum votes threshold met
   - Verify ahead-by-k condition
   - Review vote distribution
   - Consider adjusting thresholds

2. **Low Confidence**
   - Review confidence scores from agents
   - Check for outlier votes
   - Verify reputation weights
   - Consider more votes

3. **Red Flags**
   - Investigate anomalous voting patterns
   - Review agent confidence scores
   - Check for outlier detection
   - Analyze voting history

4. **Performance Issues**
   - Profile consensus computation
   - Optimize red-flagging logic
   - Consider batch processing
   - Implement caching

## API Reference

### MAKERConsensus

See [`src/heretek_swarm/consensus/maker.py`](../src/heretek_swarm/consensus/maker.py) for complete API documentation.

### Key Methods

- [`start_consensus()`](../src/heretek_swarm/consensus/maker.py:141): Start a new consensus process
- [`add_vote()`](../src/heretek_swarm/consensus/maker.py:152): Add a vote to a consensus process
- [`compute_consensus()`](../src/heretek_swarm/consensus/maker.py:193): Compute consensus from collected votes
- [`get_vote_history()`](../src/heretek_swarm/consensus/maker.py): Get vote history for an agent
- [`get_agent_reputation()`](../src/heretek_swarm/consensus/maker.py): Get agent reputation score

## See Also

- [Actors System](./actors-system.md)
- [HeavySwarm Workflow](./orchestration.md)
- [Memory System](./memory.md)
- [State Management](./state.md)
