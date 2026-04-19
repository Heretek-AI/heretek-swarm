"""
Integration tests for SPA serving and API priority.

Tests that:
1. GET / returns HTML with <div id="root">
2. GET /nonexistent-path returns HTML (SPA fallback)
3. GET /assets/*.js returns 200 with correct Content-Type
4. GET /api/health (public endpoint) still works alongside static serving
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_app_lifespan():
    """
    Mock the lifespan context manager to avoid database/Redis/NATS connections.
    This allows testing the SPA serving without external dependencies.
    """
    from contextlib import asynccontextmanager
    from fastapi import FastAPI

    # Create a minimal app with just the SPA routes for testing
    app = FastAPI(title="Test SPA App")

    # Mount static files at /assets
    # Calculate project root: tests/api/test_xxx.py -> project root (3 levels up)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    dist_path = os.path.join(project_root, "dashboard", "frontend", "dist")

    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, HTMLResponse
    from fastapi import HTTPException

    if os.path.isdir(dist_path):
        app.mount("/assets", StaticFiles(directory=dist_path), name="dashboard_assets")

    # Add API health endpoint BEFORE the catch-all route
    @app.get("/api/health")
    async def health_check():
        return {"status": "healthy", "message": "API is working"}

    @app.get("/")
    async def root():
        """Root endpoint serving the React dashboard index.html."""
        index_path = os.path.join(dist_path, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        raise HTTPException(404, "Dashboard not available")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """SPA catch-all route - serves index.html for non-API paths."""
        if path.startswith("api/") or path.startswith("metrics") or path.startswith("docs"):
            raise HTTPException(404, "Not found")
        index_path = os.path.join(dist_path, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        raise HTTPException(404, "Dashboard not available")

    return app


@pytest.fixture
def client(mock_app_lifespan):
    """Create a TestClient with the mock SPA app."""
    return TestClient(mock_app_lifespan)


class TestSPARootServing:
    """Tests for GET / serving the React dashboard."""

    def test_root_returns_html(self, client):
        """GET / returns HTML content."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_root_contains_react_root_div(self, client):
        """GET / returns HTML with <div id="root">."""
        response = client.get("/")
        assert response.status_code == 200
        html_content = response.text
        assert '<div id="root">' in html_content, "HTML should contain <div id=\"root\">"

    def test_root_contains_assets_links(self, client):
        """GET / includes links to bundled assets."""
        response = client.get("/")
        assert response.status_code == 200
        html_content = response.text
        # Should reference /assets/ for JS or CSS
        assert "/assets/" in html_content, "HTML should reference assets"


class TestSPAFallback:
    """Tests for SPA catch-all route serving index.html for non-API paths."""

    def test_nonexistent_path_returns_html(self, client):
        """GET /nonexistent-path returns HTML (SPA fallback)."""
        response = client.get("/nonexistent-path")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_nonexistent_path_contains_root_div(self, client):
        """SPA fallback returns HTML with <div id="root">."""
        response = client.get("/nonexistent-path")
        assert response.status_code == 200
        assert '<div id="root">' in response.text

    def test_arbitrary_nested_path_returns_html(self, client):
        """GET /some/nested/path returns HTML (SPA fallback)."""
        response = client.get("/some/nested/path")
        assert response.status_code == 200
        assert '<div id="root">' in response.text

    def test_api_path_does_not_trigger_fallback(self, client):
        """API paths should return 404, not SPA fallback."""
        response = client.get("/api/some-endpoint")
        # The catch-all should not serve HTML for API paths
        # It should return 404 because API paths are not handled
        assert response.status_code == 404


class TestStaticAssets:
    """Tests for static asset serving at /assets/."""

    def test_js_file_returns_200(self, client):
        """GET /assets/assets/*.js returns 200."""
        # The files are at dist/assets/*.js, and mount is at /assets
        # So correct path is /assets/assets/*.js
        response = client.get("/assets/assets/index-Ci41iAkX.js")
        assert response.status_code == 200

    def test_js_file_content_type(self, client):
        """JS files are served with correct Content-Type."""
        response = client.get("/assets/assets/index-Ci41iAkX.js")
        assert response.status_code == 200
        assert "javascript" in response.headers.get("content-type", "").lower()

    def test_css_file_returns_200(self, client):
        """GET /assets/assets/*.css returns 200."""
        response = client.get("/assets/assets/index-BEVSIdd6.css")
        assert response.status_code == 200

    def test_css_file_content_type(self, client):
        """CSS files are served with correct Content-Type."""
        response = client.get("/assets/assets/index-BEVSIdd6.css")
        assert response.status_code == 200
        assert "css" in response.headers.get("content-type", "").lower()

    def test_nonexistent_asset_returns_404(self, client):
        """GET /assets/assets/nonexistent.js returns 404."""
        response = client.get("/assets/assets/nonexistent-file.js")
        assert response.status_code == 404


class TestAPIHealthIntegration:
    """Tests that API endpoints work alongside SPA serving."""

    def test_health_endpoint_still_works(self, client):
        """GET /api/health returns healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_takes_priority_over_spa(self, client):
        """API paths are handled by API routes, not SPA catch-all."""
        response = client.get("/api/health")
        assert response.status_code == 200
        # Should not return HTML
        assert "text/html" not in response.headers.get("content-type", "")


class TestFullAppIntegration:
    """
    Integration tests using the actual main.py app with mocked dependencies.
    These tests verify the real SPA serving behavior.
    """

    @pytest.fixture
    def full_app_client(self):
        """
        Create a TestClient for the full app with mocked external dependencies.
        """
        from heretek_swarm.api.main import app

        # Mock external dependencies that would otherwise fail
        with patch("heretek_swarm.api.main._init_config_service", new_callable=AsyncMock), \
             patch("heretek_swarm.api.main._init_supervisor", new_callable=AsyncMock), \
             patch("heretek_swarm.api.main._init_memory_store", new_callable=AsyncMock), \
             patch("heretek_swarm.api.main._init_mem0", new_callable=AsyncMock), \
             patch("heretek_swarm.api.main._init_nats_bridge", new_callable=AsyncMock), \
             patch("heretek_swarm.api.main._log_startup_complete", new_callable=AsyncMock):

            # Override the lifespan to skip external connections
            from contextlib import asynccontextmanager

            @asynccontextmanager
            async def test_lifespan(app):
                # Skip all external initialization
                yield

            app.router.lifespan_context = test_lifespan

            with TestClient(app) as client:
                yield client

    def test_full_app_root_returns_html(self, full_app_client):
        """GET / returns HTML from actual app."""
        response = full_app_client.get("/")
        assert response.status_code == 200
        assert '<div id="root">' in response.text

    def test_full_app_spa_fallback(self, full_app_client):
        """GET /dashboard returns HTML via SPA fallback from actual app."""
        response = full_app_client.get("/dashboard")
        assert response.status_code == 200
        assert '<div id="root">' in response.text

    def test_full_app_assets_mounted(self, full_app_client):
        """Assets are properly mounted in the full app."""
        response = full_app_client.get("/assets/")
        assert response.status_code == 200

    def test_full_app_api_health(self, full_app_client):
        """Health endpoint works in full app (may return 503 if services unavailable)."""
        response = full_app_client.get("/api/health")
        # Accept both 200 (healthy) and 503 (services unavailable) as valid
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
