"""CLI entry point. `python -m tier1 serve` starts the API."""

import argparse
import sys

import uvicorn

from tier1.api.app import create_app
from tier1.config import get_settings


def main() -> int:
    parser = argparse.ArgumentParser(prog="tier1")
    sub = parser.add_subparsers(dest="cmd", required=True)
    serve = sub.add_parser("serve", help="Run the API server")
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)
    serve.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    if args.cmd != "serve":
        parser.error("unknown command")
        return 2

    settings = get_settings()
    app = create_app()
    uvicorn.run(
        app,
        host=args.host or settings.api_host,
        port=args.port or settings.api_port,
        reload=args.reload,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
