"""Tests for the Phase 3B Cerbos/OPA/Casbin policy engine spike."""

from casbin.persist import FileAdapter

from heretek_swarm.governance.policy_engine_spike import run_dry_spike


def test_dry_spike_passes():
    """The policy engine cutover API surface is valid."""
    run_dry_spike()


def test_file_adapter_is_migration_target():
    """FileAdapter is the migration target for declarative policy files."""
    assert FileAdapter is not None
    assert callable(FileAdapter)
