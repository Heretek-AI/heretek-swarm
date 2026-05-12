---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T02: Make infrastructure/otel/logging.py init_logging() delegate to canonical config

Update `init_logging()` in `heretek_swarm/infrastructure/otel/logging.py` to delegate to `setup_logging()` from `heretek_swarm.logging.config` instead of calling `structlog.configure()` directly. The `LoggingConfig` dataclass fields should be mapped to `setup_logging()` parameters. This ensures there is only one code path that calls `structlog.configure()`. Since nothing currently calls `init_logging()`, this is a safety/API-compatibility change — no runtime behavior changes.

## Inputs

- `heretek-swarm/heretek_swarm/logging/config.py`
- `heretek-swarm/heretek_swarm/infrastructure/otel/logging.py`

## Expected Output

- `heretek-swarm/heretek_swarm/infrastructure/otel/logging.py`

## Verification

grep -c "structlog.configure" heretek-swarm/heretek_swarm/infrastructure/otel/logging.py should return 0 (the only call is in logging/config.py now)
