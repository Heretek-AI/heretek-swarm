"""Test T03: Verify PerceiverAgent._extract_video_features uses ffprobe.

Validates real structured video feature extraction with ffprobe for stream
metadata (width, height, fps, frame_count, codec, pix_fmt, duration, bit_rate),
plus graceful fallback when ffprobe is unavailable or the file has no video stream.
"""

import asyncio
import base64
import os
import subprocess
import tempfile

import pytest

from heretek_swarm.actors.perceiver.agent import PerceiverAgent


@pytest.fixture(scope="session")
def test_mp4_bytes() -> bytes:
    """Generate a 320x240, 25 fps, 10-frame MPEG4 test video and return raw bytes."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmpf:
        mp4_path = tmpf.name
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", "testsrc=duration=2:size=320x240:rate=25",
                "-vcodec", "mpeg4", "-frames", "10",
                mp4_path, "-loglevel", "quiet",
            ],
            check=True,
        )
        with open(mp4_path, "rb") as f:
            return f.read()
    finally:
        with suppress_oserror():
            os.unlink(mp4_path)


@pytest.fixture(scope="session")
def test_mp4_base64(test_mp4_bytes: bytes) -> str:
    """Base64-encoded test MP4 (no data URL prefix)."""
    return base64.b64encode(test_mp4_bytes).decode()


@pytest.fixture
def agent() -> PerceiverAgent:
    """Fresh PerceiverAgent for each test."""
    return PerceiverAgent(agent_id="perceiver-video-test")


def suppress_oserror():
    """Context manager that suppresses OSError (like file cleanup)."""
    import contextlib
    return contextlib.suppress(OSError)


# --- ffprobe extraction ---


@pytest.mark.asyncio
async def test_bytes_input_returns_full_features(agent, test_mp4_bytes):
    """Raw bytes should produce width, height, fps, frame_count, codec, pix_fmt, etc."""
    result = await agent._extract_video_features(test_mp4_bytes, "mp4")

    assert result["width"] == 320
    assert result["height"] == 240
    assert result["fps"] == 25.0
    assert result["frame_rate_raw"] == "25/1"
    assert result["frame_count"] == 10
    assert result["codec_name"] == "mpeg4"
    assert result["pix_fmt"] == "yuv420p"
    assert isinstance(result["duration"], float)
    assert result["duration"] > 0
    assert result["analyzed_by"] == "ffprobe"
    assert result["mime_type"] == "application/octet-stream"


@pytest.mark.asyncio
async def test_data_url_input_decodes_and_extracts(agent, test_mp4_base64):
    """data:video/mp4;base64,... should decode and extract like raw bytes."""
    data_url = f"data:video/mp4;base64,{test_mp4_base64}"
    result = await agent._extract_video_features(data_url, None)

    assert result["width"] == 320
    assert result["height"] == 240
    assert result["fps"] == 25.0
    assert result["frame_count"] == 10
    assert result["codec_name"] == "mpeg4"
    assert result["analyzed_by"] == "ffprobe"
    assert result["mime_type"] == "video/mp4"


@pytest.mark.asyncio
async def test_plain_base64_input_extracts(agent, test_mp4_base64):
    """Plain base64 string (no data: prefix) still extracts via ffprobe."""
    result = await agent._extract_video_features(test_mp4_base64, "mp4")

    assert result["width"] == 320
    assert result["codec_name"] == "mpeg4"
    assert result["analyzed_by"] == "ffprobe"


@pytest.mark.asyncio
async def test_format_hint_preserved(agent, test_mp4_bytes):
    """Format hint is reflected in the result even when actual codec differs."""
    result = await agent._extract_video_features(test_mp4_bytes, "mov")

    assert result["format"] == "mov"
    assert result["codec_name"] == "mpeg4"  # real codec from ffprobe
    assert result["analyzed_by"] == "ffprobe"


# --- Fallback ---


@pytest.mark.asyncio
async def test_invalid_data_falls_back_to_metadata(agent):
    """Non-video binary data triggers fallback with analyzed_by='metadata'."""
    result = await agent._extract_video_features(b"not-video-data", None)

    assert result["analyzed_by"] == "metadata"
    assert "note" in result
    assert "ffprobe" in result["note"].lower() or "exited" in result["note"].lower()
    assert result["size_bytes"] == 14


@pytest.mark.asyncio
async def test_text_string_falls_back(agent):
    """A plain text string (not base64, not data URL) falls back to metadata."""
    result = await agent._extract_video_features("hello world", "txt")

    assert result["analyzed_by"] == "metadata"
    assert result["size_bytes"] > 0


# --- Helper methods ---


def test_decode_video_bytes_data_url():
    """_decode_video_bytes strips data URL prefix and base64-decodes."""
    raw = b"\x00\x01\x02"
    b64 = base64.b64encode(raw).decode()
    data_url = f"data:video/mp4;base64,{b64}"
    decoded, mime = PerceiverAgent._decode_video_bytes(data_url)
    assert decoded == raw
    assert mime == "video/mp4"


def test_decode_video_bytes_plain_bytes():
    """_decode_video_bytes passes bytes through unchanged."""
    raw = b"\x00\x00\x00\x1cftyp"
    decoded, mime = PerceiverAgent._decode_video_bytes(raw)
    assert decoded == raw
    assert mime == "application/octet-stream"


def test_decode_video_bytes_plain_base64():
    """_decode_video_bytes base64-decodes a plain string (no data: prefix)."""
    raw = b"video-data"
    b64 = base64.b64encode(raw).decode()
    decoded, _ = PerceiverAgent._decode_video_bytes(b64)
    assert decoded == raw


def test_video_suffix_from_format_hint():
    """_video_suffix_from_format returns .ext for known formats."""
    assert PerceiverAgent._video_suffix_from_format("mp4", "") == ".mp4"
    assert PerceiverAgent._video_suffix_from_format("AVI", "") == ".avi"
    assert PerceiverAgent._video_suffix_from_format("mov", "") == ".mov"
    assert PerceiverAgent._video_suffix_from_format("webm", "") == ".webm"
    assert PerceiverAgent._video_suffix_from_format("mkv", "") == ".mkv"


def test_video_suffix_from_mime_type():
    """_video_suffix_from_format falls back to MIME type mapping."""
    assert PerceiverAgent._video_suffix_from_format(None, "video/mp4") == ".mp4"
    assert PerceiverAgent._video_suffix_from_format(None, "video/quicktime") == ".mov"
    assert PerceiverAgent._video_suffix_from_format(None, "video/webm") == ".webm"
    assert PerceiverAgent._video_suffix_from_format(None, "video/x-matroska") == ".mkv"


def test_video_suffix_unknown():
    """Unknown format/mime gets .video fallback or uses format_hint as-is."""
    assert PerceiverAgent._video_suffix_from_format(None, "video/unknown") == ".video"
    assert PerceiverAgent._video_suffix_from_format("xyz", "") == ".xyz"


@pytest.mark.parametrize(
    "input_val,expected",
    [
        ("30/1", 30.0),
        ("30000/1001", 29.97),
        ("25/1", 25.0),
        ("24000/1001", 23.98),
        ("1/1", 1.0),
        ("0/0", None),       # zero denominator
        ("/", None),         # malformed
        ("", None),          # empty string
        (None, None),        # None input
        ("abc", None),       # non-numeric
    ],
)
def test_parse_r_frame_rate(input_val, expected):
    assert PerceiverAgent._parse_r_frame_rate(input_val) == expected
