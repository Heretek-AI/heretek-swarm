"""Integration test suite for the perception pipeline (M001/S04/T06).

Covers:
- Image: PIL extraction, PIL+LLM merge, metadata fallback on ImportError
- Audio: ffprobe extraction from generated WAV, metadata fallback on ffprobe error
- Video: ffprobe extraction from generated MP4, metadata fallback on ffprobe error
- Document: markdown text stats, JSON structure detection, binary blob fallback
- API: happy-path text upload, missing perceiver → 503, missing file → 422
"""

from __future__ import annotations

import asyncio
import base64
import builtins
import io
import os
import subprocess
import tempfile
from typing import Any
from unittest.mock import patch

import pytest

from heretek_swarm.actors.perceiver.agent import PerceiverAgent
from heretek_swarm.actors.supervisor import ActorSupervisor


# ---------------------------------------------------------------------------
# Session-scoped generated test media
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def small_png_bytes() -> bytes:
    """Generate a 10x10 RGB PNG via PIL and return raw bytes."""
    from PIL import Image as PILImage

    buf = io.BytesIO()
    img = PILImage.new("RGB", (10, 10), color=(120, 80, 60))
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(scope="session")
def small_png_base64(small_png_bytes: bytes) -> str:
    """Base64-encoded small PNG (no data: prefix)."""
    return base64.b64encode(small_png_bytes).decode()


@pytest.fixture(scope="session")
def test_wav_bytes() -> bytes:
    """Generate a 0.5s 440 Hz mono WAV and return raw bytes."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpf:
        wav_path = tmpf.name
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", "sine=frequency=440:duration=0.5",
                "-ac", "1", "-ar", "44100",
                wav_path, "-loglevel", "quiet",
            ],
            check=True,
        )
        with open(wav_path, "rb") as f:
            return f.read()
    finally:
        with _suppress_oserror():
            os.unlink(wav_path)


@pytest.fixture(scope="session")
def test_wav_base64(test_wav_bytes: bytes) -> str:
    """Base64-encoded test WAV."""
    return base64.b64encode(test_wav_bytes).decode()


@pytest.fixture(scope="session")
def test_mp4_bytes() -> bytes:
    """Generate a 320x240, 25fps, 5-frame MPEG4 video and return raw bytes."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmpf:
        mp4_path = tmpf.name
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", "testsrc=duration=1:size=320x240:rate=25",
                "-vcodec", "mpeg4", "-frames:v", "5",
                mp4_path, "-loglevel", "quiet",
            ],
            check=True,
        )
        with open(mp4_path, "rb") as f:
            return f.read()
    finally:
        with _suppress_oserror():
            os.unlink(mp4_path)


@pytest.fixture(scope="session")
def test_mp4_base64(test_mp4_bytes: bytes) -> str:
    """Base64-encoded test MP4."""
    return base64.b64encode(test_mp4_bytes).decode()


def _suppress_oserror():
    """Context manager that suppresses OSError (like file cleanup)."""
    import contextlib

    return contextlib.suppress(OSError)


# ---------------------------------------------------------------------------
# Per-agent fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def agent() -> PerceiverAgent:
    """Fresh PerceiverAgent for each test."""
    return PerceiverAgent(agent_id="perceiver-pipeline-test")


# ===========================================================================
# Image Tests (3)
# ===========================================================================


@pytest.mark.asyncio
async def test_image_pil_extraction_returns_dimensions_and_colors(agent, small_png_base64):
    """Generate a small PNG via PIL, base64-encode, call _extract_image_features,
    and verify dimensions, channels, color_stats, and dominant_color populated."""
    result = await agent._extract_image_features(small_png_base64, "png")

    assert result["dimensions"] == {"width": 10, "height": 10}
    assert result["mode"] == "RGB"
    assert result["channels"] == 3
    assert "color_stats" in result
    # Color stats should have R, G, B bands
    for band in ("R", "G", "B"):
        assert band in result["color_stats"], f"Missing color band {band}"
        assert "mean" in result["color_stats"][band]
        assert "stddev" in result["color_stats"][band]
    assert "dominant_color_rgb" in result
    assert len(result["dominant_color_rgb"]) == 3
    assert result["analyzed_by"] == "pil"
    assert result["format"] == "png"


@pytest.mark.asyncio
async def test_image_pil_plus_llm_merge_path(small_png_base64):
    """When swarms_agent is set with LLM, the result includes description
    and analyzed_by becomes 'pil+llm'."""
    import inspect

    class LLMCapablePerceiver(PerceiverAgent):
        """PerceiverAgent with controllable LLM response."""

        async def run_with_llm(self, prompt, timeout=60, **kw):  # noqa: ASYNC109
            return "A solid brownish square on a transparent background."

    agent = LLMCapablePerceiver(agent_id="perceiver-llm-test")
    # Simulate a minimal swarms_agent with an llm attribute
    agent.swarms_agent = type("FakeSwarmsAgent", (), {"llm": type("FakeLLM", (), {})()})()

    result = await agent._extract_image_features(small_png_base64, "png")

    assert result["analyzed_by"] == "pil+llm"
    assert result["description"] == "A solid brownish square on a transparent background."
    assert result["dimensions"] == {"width": 10, "height": 10}


@pytest.mark.asyncio
async def test_image_metadata_fallback_when_pil_unavailable(monkeypatch):
    """Mock ImportError for PIL, verify metadata fallback with analyzed_by='metadata'."""
    original_import = builtins.__import__

    def _mock_pil_import(name, *args, **kwargs):
        if name == "PIL" or name.startswith("PIL."):
            raise ImportError(f"No module named '{name}' (simulated)")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _mock_pil_import)

    # Also need to prevent the cached import in sys.modules
    for mod_key in list(__import__("sys").modules):
        if mod_key.startswith("PIL"):
            monkeypatch.delitem(__import__("sys").modules, mod_key, raising=False)

    agent = PerceiverAgent(agent_id="perceiver-nopil-test")
    result = await agent._extract_image_features(
        base64.b64encode(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR").decode(), "png"
    )

    assert result["analyzed_by"] == "metadata"
    assert result["format"] == "png"
    assert result["size_bytes"] > 0


# ===========================================================================
# Audio Tests (2)
# ===========================================================================


@pytest.mark.asyncio
async def test_audio_ffprobe_extraction_from_generated_wav(agent, test_wav_base64):
    """Generate a WAV via ffmpeg, base64-encode, call _extract_audio_features,
    assert sample_rate=44100, channels=1, codec, duration populated."""
    result = await agent._extract_audio_features(test_wav_base64, "wav")

    assert result["sample_rate"] == 44100
    assert result["channels"] == 1
    assert result["codec_name"] == "pcm_s16le"
    assert result["duration"] > 0
    assert result["analyzed_by"] == "ffprobe"
    assert isinstance(result["mean_volume"], float)
    assert isinstance(result["max_volume"], float)


@pytest.mark.asyncio
async def test_audio_metadata_fallback_on_ffprobe_failure(agent):
    """Non-audio data triggers metadata fallback with analyzed_by='metadata'."""
    result = await agent._extract_audio_features(b"not-valid-audio-data-at-all", None)

    assert result["analyzed_by"] == "metadata"
    assert "note" in result
    assert "ffprobe" in result["note"].lower() or "exited" in result["note"].lower()
    assert result["size_bytes"] > 0


# ===========================================================================
# Video Tests (2)
# ===========================================================================


@pytest.mark.asyncio
async def test_video_ffprobe_extraction_from_generated_mp4(agent, test_mp4_base64):
    """Generate an MP4 via ffmpeg, base64-encode, call _extract_video_features,
    assert width/height/fps/frame_count/codec populated."""
    result = await agent._extract_video_features(test_mp4_base64, "mp4")

    assert result["width"] == 320
    assert result["height"] == 240
    assert result["fps"] == 25.0
    assert result["frame_count"] == 5
    assert result["codec_name"] == "mpeg4"
    assert result["pix_fmt"] == "yuv420p"
    assert isinstance(result["duration"], float)
    assert result["duration"] > 0
    assert result["analyzed_by"] == "ffprobe"


@pytest.mark.asyncio
async def test_video_metadata_fallback_on_ffprobe_failure(agent):
    """Non-video data triggers metadata fallback with analyzed_by='metadata'."""
    result = await agent._extract_video_features(b"this-is-not-video-data", None)

    assert result["analyzed_by"] == "metadata"
    assert "note" in result
    assert "ffprobe" in result["note"].lower() or "exited" in result["note"].lower()
    assert result["size_bytes"] > 0


# ===========================================================================
# Document Tests (3)
# ===========================================================================


@pytest.mark.asyncio
async def test_document_markdown_text_statistics(agent):
    """_extract_document_features with markdown text asserts word_count,
    sentence_count, and line_count."""
    text = """# Test Document

This is the first paragraph. It has two sentences.

## Section Two

This is another paragraph. With more content. And even more!

A final line."""
    result = await agent._extract_document_features(text, "md")

    assert result["analyzed_by"] == "text-stat"
    assert result["word_count"] > 0
    assert result["sentence_count"] > 0
    assert result["line_count"] > 0
    assert result["char_count"] > 0
    assert len(result["text_preview"]) > 0
    assert "structure" in result
    assert result["structure"].get("heading_count", 0) >= 1


@pytest.mark.asyncio
async def test_document_json_structure_detection(agent):
    """_extract_document_features with JSON string asserts structure detection flags."""
    text = '{"name": "Alice", "age": 30, "skills": ["python", "rust"]}'
    result = await agent._extract_document_features(text, "json")

    assert result["analyzed_by"] == "text-stat"
    structure = result["structure"]
    assert structure["json_valid"] is True
    assert structure["json_type"] == "object"
    assert structure["json_keys"] == 3

    # word_count etc still populated
    assert result["word_count"] > 0
    assert result["char_count"] > 0


@pytest.mark.asyncio
async def test_document_binary_blob_fallback(agent):
    """Raw bytes (binary blob) that aren't a recognized text format fall back gracefully."""
    result = await agent._extract_document_features(b"\x00\x01\x02\x03\x04\x05", None)

    # Should still produce a valid result with analyzed_by
    assert "analyzed_by" in result
    assert result["format"] == "unknown"
    assert result["size_bytes"] == 6


# ===========================================================================
# API Endpoint Tests (3)
# ===========================================================================


@pytest.fixture
def perceiver_agent() -> PerceiverAgent:
    """Return an initialized PerceiverAgent."""
    agent = PerceiverAgent()
    asyncio.run(agent.initialize())
    return agent


@pytest.fixture
def supervisor_with_perceiver(perceiver_agent: PerceiverAgent) -> ActorSupervisor:
    """Return a supervisor that has the perceiver agent registered."""
    supervisor = ActorSupervisor()
    supervisor.actors["perceiver"] = perceiver_agent
    return supervisor


@pytest.fixture
def test_app(supervisor_with_perceiver: ActorSupervisor):
    """Build a FastAPI test app with the perceiver router, mocking get_supervisor."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import heretek_swarm.api.perceiver as perceiver_mod

    original = perceiver_mod.get_supervisor
    perceiver_mod.get_supervisor = lambda: supervisor_with_perceiver  # type: ignore[assignment]

    app = FastAPI()
    from heretek_swarm.api.perceiver import router

    app.include_router(router)

    yield TestClient(app)

    perceiver_mod.get_supervisor = original


# Also patch the module-level get_supervisor before every test
@pytest.fixture(autouse=True)
def _patch_supervisor(supervisor_with_perceiver: ActorSupervisor):
    """Ensure perceiver module's get_supervisor returns our test supervisor."""
    import heretek_swarm.api.perceiver as perceiver_mod

    original = perceiver_mod.get_supervisor
    perceiver_mod.get_supervisor = lambda: supervisor_with_perceiver  # type: ignore[assignment]
    yield
    perceiver_mod.get_supervisor = original


def test_api_happy_path_text_file_returns_200(test_app):
    """POST text file returns 200 with structured features."""
    resp = test_app.post(
        "/api/perceiver/analyze",
        files={"file": ("test.txt", io.BytesIO(b"Hello world. This is a test."), "text/plain")},
    )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["modality"] == "text"
    assert data["features"]["word_count"] > 0
    assert "input_id" in data
    assert "quality_score" in data
    assert "timestamp" in data


def test_api_missing_perceiver_returns_503():
    """POST when perceiver is not in supervisor returns 503."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import heretek_swarm.api.perceiver as perceiver_mod

    supervisor = ActorSupervisor()
    supervisor.actors.clear()  # No perceiver registered

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
        assert "not available" in detail["error"].lower()
    finally:
        perceiver_mod.get_supervisor = original


def test_api_missing_file_returns_422(test_app):
    """POST without file returns 422 (FastAPI validation)."""
    resp = test_app.post("/api/perceiver/analyze")

    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


# ===========================================================================
# Cross-pipeline integration: stats increment on successful analysis
# ===========================================================================


def test_api_increments_processing_stats(test_app, supervisor_with_perceiver):
    """Each successful API analysis increments inputs_processed and
    total_features_extracted on the perceiver agent."""
    perceiver = supervisor_with_perceiver.actors["perceiver"]
    before_inputs = perceiver.inputs_processed.get("text", 0)
    before_features = perceiver.total_features_extracted

    resp = test_app.post(
        "/api/perceiver/analyze",
        files={"file": ("doc.txt", io.BytesIO(b"Another test document. For stats."), "text/plain")},
    )

    assert resp.status_code == 200, resp.text
    assert perceiver.inputs_processed.get("text", 0) >= before_inputs + 1
    assert perceiver.total_features_extracted > before_features
