"""
Heretek Swarm CLI

Command-line interface for Heretek Swarm deployment and management.
"""

from pathlib import Path

import click


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Heretek Swarm - Next-generation multi-agent system."""


@cli.command()
@click.option("--production", is_flag=True, help="Deploy to production mode")
@click.option("--scale", default=1, type=int, help="Number of agent instances (default: 1)")
@click.option("--nats-url", default="nats://localhost:4222", help="NATS server URL")
def deploy(production: bool, scale: int, nats_url: str) -> None:
    """Deploy Heretek Swarm agents."""
    click.echo(f"Deploying Heretek Swarm (production={production}, scale={scale})")

    if production:
        click.echo("Starting in PRODUCTION mode")

    click.echo(f"Connecting to NATS at {nats_url}")

    # Check if docker compose is available
    compose_file = Path("docker-compose.yml")
    if compose_file.exists():
        click.echo(
            "Found docker-compose.yml - use 'docker compose up -d' "
            "for containerized deployment"
        )

    click.echo("Deploy command requires full installation: pip install heretek-swarm[full]")


@cli.command()
@click.option("--version", default="latest", help="Version to update to")
def update(version: str) -> None:
    """Update Heretek Swarm to a new version."""
    click.echo(f"Updating Heretek Swarm to version {version}")

    if version == "latest":
        click.echo("Fetching latest version from PyPI...")
        click.echo("Run: pip install --upgrade heretek-swarm")
    else:
        click.echo(f"Run: pip install --upgrade heretek-swarm=={version}")


@cli.command()
def status() -> None:
    """Check Heretek Swarm status."""
    click.echo("Heretek Swarm Status")
    click.echo("Run tests: pytest tests/")
    click.echo("Run linter: ruff check src tests")


def main() -> None:
    """Entry point for the CLI."""
    cli(prog_name="heretek-swarm")


if __name__ == "__main__":
    main()
