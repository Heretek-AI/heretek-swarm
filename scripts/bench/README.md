# scripts/bench/ — Profiling Harness

Standalone benchmark scripts for measuring API latency, actor message processing throughput, and database query performance in the Heretek Swarm.

## Prerequisites

- **Docker Compose stack running:** `docker compose up -d`
- **Python environment:** `pip install -e ".[dev]"` (pytest-benchmark is a dev dependency)
- **CLI tools:** `curl`, `jq`, `bc`, `sort` (available on all Unix-like systems including Git Bash / WSL on Windows)

## Scripts

### `api_latency.sh`

Samples API endpoints and computes latency percentiles (p50, p95, p99, mean, min, max).

```bash
bash scripts/bench/api_latency.sh [NUM_SAMPLES]
```

- `NUM_SAMPLES` — number of curl samples per endpoint (default: 10)
- `API_BASE_URL` — override base URL (default: `http://localhost:8000`)
- Output: `scripts/bench/results/api_latency_YYYYMMDD_HHMMSS.json`

**Endpoints sampled:**
- `GET /api/health/live`
- `GET /api/health/ready`
- `GET /api/agents/instances`
- `GET /api/agents/core/types`
- `GET /api/config`

### `actor_timing.sh`

Runs the `pytest-benchmark` suite for actor message processing throughput.

```bash
bash scripts/bench/actor_timing.sh
```

- Exercised path: `_BenchAgent._process_mailbox() → process_message()` via `tests/test_bench_actor_throughput.py`
- Output: `scripts/bench/results/actor_timing_YYYYMMDD_HHMMSS.json`

### `db_query.sh`

Profiles database query latency by executing standard query patterns (SELECT, JOIN) against the running Postgres instance.

```bash
bash scripts/bench/db_query.sh [REPEATS]
```

- `REPEATS` — number of repetitions per query (default: 5)
- Output: `scripts/bench/results/db_query_YYYYMMDD_HHMMSS.json`

## Output Format

All scripts emit machine-parseable JSON to `scripts/bench/results/`. Timestamps in filenames allow comparison across runs.

## Results Directory

Bench result JSON files are ephemeral and gitignored (`scripts/bench/results/` in `.gitignore`). The `.gitkeep` file ensures the directory survives `git clone`.

## Edge Cases

- **Swarm not running:** `api_latency.sh` and `db_query.sh` exit with error code 1 and a clear diagnostics message
- **Missing tools:** Each script validates required CLI tools before execution
- **Empty results:** Empty runs still produce valid JSON with `null` percentile values
- **Windows:** Run via Git Bash or WSL; all scripts use portable bash syntax
