"""Tests for the Perceiver REST API endpoint (M001/S04/T05).

Verifies:
- POST /api/perceiver/analyze with a text file returns structured features
- POST /api/perceiver/analyze with an image file returns image features
- Empty file → 400
- Missing file → 422 (FastAPI validation)
- Perceiver agent unavailable → 503
- Processing errors → 500
- Response model matches PerceiverResponse schema
"""

from __future__ import annotations

import asyncio
import io
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from heretek_swarm.actors.perceiver.agent import PerceiverAgent
from heretek_swarm.actors.supervisor import ActorSupervisor

pytestmark = [pytest.mark.unit]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_initialized_perceiver() -> PerceiverAgent:
    """Create and initialize a PerceiverAgent synchronously."""
    agent = PerceiverAgent()
    asyncio.run(agent.initialize())
    return agent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def perceiver_agent() -> PerceiverAgent:
    """Return an initialized PerceiverAgent."""
    return _make_initialized_perceiver()


@pytest.fixture
def supervisor_with_perceiver(perceiver_agent: PerceiverAgent) -> ActorSupervisor:
    """Return a supervisor that has the perceiver agent registered."""
    supervisor = ActorSupervisor()
    supervisor.actors["perceiver"] = perceiver_agent
    return supervisor


@pytest.fixture
def app(supervisor_with_perceiver: ActorSupervisor) -> FastAPI:
    """Build a FastAPI test app with the perceiver router, mocking get_supervisor."""
    import heretek_swarm.api.perceiver as perceiver_mod

    original = perceiver_mod.get_supervisor
    perceiver_mod.get_supervisor = lambda: supervisor_with_perceiver  # type: ignore[assignment]

    _app = FastAPI()
    from heretek_swarm.api.perceiver import router

    _app.include_router(router)

    yield _app

    perceiver_mod.get_supervisor = original


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Return a TestClient for the test app."""
    return TestClient(app)


# Patch the module-level get_supervisor for every test
@pytest.fixture(autouse=True)
def _patch_supervisor_module(supervisor_with_perceiver: ActorSupervisor):
    """Ensure perceiver module's get_supervisor returns our test supervisor."""
    import heretek_swarm.api.perceiver as perceiver_mod

    original = perceiver_mod.get_supervisor
    perceiver_mod.get_supervisor = lambda: supervisor_with_perceiver  # type: ignore[assignment]
    yield
    perceiver_mod.get_supervisor = original


# ---------------------------------------------------------------------------
# Happy-path: text file
# ---------------------------------------------------------------------------

def test_analyze_text_file_returns_features(client: TestClient):
    """POST /api/perceiver/analyze with a .txt file returns text features."""
    text_content = (
        "Hello world. This is a test document.\n"
        "It has multiple sentences. And multiple lines.\n\n"
        "End of document."
    )
    resp = client.post(
        "/api/perceiver/analyze",
        files={"file": ("test_doc.txt", io.BytesIO(text_content.encode()), "text/plain")},
    )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert "input_id" in data, data
    assert data["input_id"].startswith("input_text_"), data["input_id"]
    assert data["modality"] == "text", data
    assert "features" in data, data
    features = data["features"]
    assert features["word_count"] > 0, features
    assert features["sentence_count"] > 0, features
    assert features["char_count"] > 0, features
    assert "quality_score" in data, data
    assert isinstance(data["quality_score"], (int, float)), data["quality_score"]
    assert data["quality_score"] >= 0.0 and data["quality_score"] <= 1.0, data["quality_score"]
    assert "timestamp" in data, data


# ---------------------------------------------------------------------------
# Happy-path: image file (minimal PNG)
# ---------------------------------------------------------------------------

def test_analyze_image_returns_image_features(client: TestClient):
    """POST /api/perceiver/analyze with a minimal PNG returns image dimensions."""
    # Generate a valid 2x2 RGB PNG via PIL
    from PIL import Image as PILImage

    buf = io.BytesIO()
    img = PILImage.new("RGB", (2, 2), color=(255, 0, 0))
    img.save(buf, format="PNG")
    valid_png = buf.getvalue()

    resp = client.post(
        "/api/perceiver/analyze",
        files={"file": ("test.png", io.BytesIO(valid_png), "image/png")},
    )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert data["modality"] == "image", data
    features = data["features"]
    assert features.get("dimensions") is not None, features
    assert features["dimensions"]["width"] == 2, features["dimensions"]
    assert features["dimensions"]["height"] == 2, features["dimensions"]


# ---------------------------------------------------------------------------
# Happy-path: explicit modality hint
# ---------------------------------------------------------------------------

def test_analyze_with_explicit_modality(client: TestClient):
    """POST /api/perceiver/analyze with modality=text form field overrides auto-detection."""
    resp = client.post(
        "/api/perceiver/analyze",
        files={"file": ("data.bin", io.BytesIO(b"hello world test content"), "application/octet-stream")},
        data={"modality": "text"},
    )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["modality"] == "text", data


# ---------------------------------------------------------------------------
# Error path: empty file
# ---------------------------------------------------------------------------

def test_analyze_empty_file_returns_400(client: TestClient):
    """POST /api/perceiver/analyze with empty file returns 400."""
    resp = client.post(
        "/api/perceiver/analyze",
        files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
    )

    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    detail = resp.json()["detail"]
    assert "empty" in detail["error"].lower(), detail


# ---------------------------------------------------------------------------
# Error path: missing file
# ---------------------------------------------------------------------------

def test_analyze_missing_file_returns_422(client: TestClient):
    """POST /api/perceiver/analyze without file returns 422 (FastAPI validation)."""
    resp = client.post("/api/perceiver/analyze")

    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# Error path: perceiver agent not available
# ---------------------------------------------------------------------------

def test_analyze_no_perceiver_returns_503():
    """POST /api/perceiver/analyze when perceiver is missing returns 503."""
    import heretek_swarm.api.perceiver as perceiver_mod

    supervisor = ActorSupervisor()
    supervisor.actors.clear()

    original = perceiver_mod.get_supervisor
    perceiver_mod.get_supervisor = lambda: supervisor  # type: ignore[assignment]

    try:
        app = FastAPI()
        from heretek_swarm.api.perceiver import router

        app.include_router(router)
        client = TestClient(app)

        resp = client.post(
            "/api/perceiver/analyze",
            files={"file": ("test.txt", io.BytesIO(b"content"), "text/plain")},
        )

        assert resp.status_code == 503, f"Expected 503, got {resp.status_code}: {resp.text}"
        detail = resp.json()["detail"]
        assert "not available" in detail["error"].lower(), detail
    finally:
        perceiver_mod.get_supervisor = original


# ---------------------------------------------------------------------------
# Error path: processing failure
# ---------------------------------------------------------------------------

def test_analyze_processing_failure_returns_500():
    """POST /api/perceiver/analyze when handler raises returns 500."""
    import heretek_swarm.api.perceiver as perceiver_mod

    class FailingPerceiver(PerceiverAgent):
        async def process_message(self, message):
            raise RuntimeError("Simulated processing crash")

    failing = FailingPerceiver()

    supervisor = ActorSupervisor()
    supervisor.actors["perceiver"] = failing

    original = perceiver_mod.get_supervisor
    perceiver_mod.get_supervisor = lambda: supervisor  # type: ignore[assignment]

    try:
        app = FastAPI()
        from heretek_swarm.api.perceiver import router

        app.include_router(router)
        client = TestClient(app)

        resp = client.post(
            "/api/perceiver/analyze",
            files={"file": ("test.txt", io.BytesIO(b"content"), "text/plain")},
        )

        assert resp.status_code == 500, f"Expected 500, got {resp.status_code}: {resp.text}"
        detail = resp.json()["detail"]
        assert "error" in detail, detail
    finally:
        perceiver_mod.get_supervisor = original


# ---------------------------------------------------------------------------
# Response model validation
# ---------------------------------------------------------------------------

def test_response_matches_perceiver_response_model(client: TestClient):
    """Verify response fields conform to PerceiverResponse Pydantic model."""
    from heretek_swarm.api.perceiver import PerceiverResponse

    resp = client.post(
        "/api/perceiver/analyze",
        files={"file": ("doc.txt", io.BytesIO(b"A short document. With two sentences."), "text/plain")},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()

    model = PerceiverResponse(**data)
    assert model.input_id is not None
    assert model.modality == "text"
    assert isinstance(model.features, dict)
    assert isinstance(model.quality_score, float)
    assert model.timestamp is not None


# ---------------------------------------------------------------------------
# Processing stats increment
# ---------------------------------------------------------------------------

def test_analyze_increments_processing_stats(client: TestClient, supervisor_with_perceiver: ActorSupervisor):
    """Each successful analysis increments inputs_processed and total_features_extracted."""
    perceiver = supervisor_with_perceiver.actors["perceiver"]
    before_inputs = perceiver.inputs_processed.get("text", 0)
    before_features = perceiver.total_features_extracted

    resp = client.post(
        "/api/perceiver/analyze",
        files={"file": ("doc.txt", io.BytesIO(b"Hello world. Test document."), "text/plain")},
    )

    assert resp.status_code == 200, resp.text
    assert perceiver.inputs_processed.get("text", 0) >= before_inputs + 1
    assert perceiver.total_features_extracted > before_features
