# Perceiver Agent - Tool Catalog

## Input Tools

### `subscribe(channel, schema)`
Subscribe to an input channel with schema validation.

**Parameters:**
- `channel` (str): Channel path (e.g., "exterior:user_input")
- `schema` (Schema): Validation schema

**Returns:** Subscription handle

### `unsubscribe(handle)`
Unsubscribe from a channel.

**Parameters:**
- `handle`: Subscription handle from subscribe()

### `fetch(channel, limit=10)`
Fetch recent items from a channel without subscribing.

**Parameters:**
- `channel` (str): Channel path
- `limit` (int): Max items to fetch

**Returns:** List of raw input items

---

## Processing Tools

### `validate(item, schema)`
Validate an item against a schema.

**Parameters:**
- `item` (dict): Item to validate
- `schema` (Schema): Validation schema

**Returns:** ValidationResult {valid: bool, errors: list}

### `enrich(item, metadata)`
Add context metadata to an item.

**Parameters:**
- `item` (dict): Item to enrich
- `metadata` (dict): Metadata to add

**Returns:** Enriched item

### `batch(timeout_ms=100, max_size=100)`
Collect items into batches for efficient processing.

**Parameters:**
- `timeout_ms` (int): Max wait time for batch
- `max_size` (int): Max batch size

**Returns:** Batch of items

---

## Output Tools

### `publish(percept, channel="percepts:raw")`
Publish a processed percept.

**Parameters:**
- `percept` (Percept): Processed percept
- `channel` (str): Output channel

### `flag_conflict(percepts)`
Flag conflicting percepts for Tribunal review.

**Parameters:**
- `percepts` (list[Percept]): Conflicting percepts

### `get_stats()`
Get processing statistics.

**Returns:** PerceiverStats {
    throughput: float,
    latency_ms: float,
    accuracy: float,
    conflict_rate: float
}
