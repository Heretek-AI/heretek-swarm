"""Test T02: Verify PerceiverAgent._extract_audio_features uses ffprobe/ffmpeg.

Validates real structured audio feature extraction with ffprobe for stream
metadata and ffmpeg volumedetect for volume stats, plus graceful fallback.
"""

import asyncio
import base64
import os
import subprocess
import tempfile

import pytest

from heretek_swarm.actors.perceiver.agent import PerceiverAgent


@pytest.fixture(scope="session")
def test_wav_bytes() -> bytes:
    """Generate a 1.5s 440 Hz sine wave WAV and return raw bytes."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpf:
        wav_path = tmpf.name
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", "sine=frequency=440:duration=1.5",
                "-ac", "1", "-ar", "44100",
                wav_path, "-loglevel", "quiet",
            ],
            check=True,
        )
        with open(wav_path, "rb") as f:
            return f.read()
    finally:
        with suppress_oserror():
            os.unlink(wav_path)


@pytest.fixture(scope="session")
def test_wav_base64(test_wav_bytes: bytes) -> str:
    """Base64-encoded test WAV (no data URL prefix)."""
    return base64.b64encode(test_wav_bytes).decode()


@pytest.fixture
def agent() -> PerceiverAgent:
    """Fresh PerceiverAgent for each test."""
    return PerceiverAgent(agent_id="perceiver-audio-test")


def suppress_oserror():
    """Context manager that suppresses OSError (like file cleanup)."""
    import contextlib
    return contextlib.suppress(OSError)


# --- ffprobe extraction ---


@pytest.mark.asyncio
async def test_bytes_input_returns_full_features(agent, test_wav_bytes):
    """Raw bytes should produce sample_rate, channels, codec, bit_rate, duration, volumes."""
    result = await agent._extract_audio_features(test_wav_bytes, "wav")

    assert result["sample_rate"] == 44100
    assert result["channels"] == 1
    assert result["codec_name"] == "pcm_s16le"
    assert result["bit_rate"] == 705600
    assert result["duration"] == 1.5
    assert result["analyzed_by"] == "ffprobe"
    assert isinstance(result["mean_volume"], float)
    assert isinstance(result["max_volume"], float)
    assert result["mean_volume"] <= result["max_volume"]


@pytest.mark.asyncio
async def test_data_url_input_decodes_and_extracts(agent, test_wav_base64):
    """data:audio/wav;base64,... should decode and extract like raw bytes."""
    data_url = f"data:audio/wav;base64,{test_wav_base64}"
    result = await agent._extract_audio_features(data_url, None)

    assert result["sample_rate"] == 44100
    assert result["channels"] == 1
    assert result["analyzed_by"] == "ffprobe"
    assert result["mime_type"] == "audio/wav"


@pytest.mark.asyncio
async def test_plain_base64_input_extracts(agent, test_wav_base64):
    """Plain base64 string (no data: prefix) still extracts via ffprobe."""
    result = await agent._extract_audio_features(test_wav_base64, "wav")

    assert result["sample_rate"] == 44100
    assert result["codec_name"] == "pcm_s16le"
    assert result["analyzed_by"] == "ffprobe"


@pytest.mark.asyncio
async def test_mp3_format_extracts(agent, test_wav_bytes):
    """Format hint 'mp3' for a WAV file should still work (ffprobe detects real codec)."""
    result = await agent._extract_audio_features(test_wav_bytes, "mp3")

    # Format in result reflects the hint; codec reflects actual content
    assert result["format"] == "mp3"
    assert result["codec_name"] == "pcm_s16le"
    assert result["analyzed_by"] == "ffprobe"


# --- Fallback ---


@pytest.mark.asyncio
async def test_invalid_data_falls_back_to_metadata(agent):
    """Non-audio binary data triggers fallback with analyzed_by='metadata'."""
    result = await agent._extract_audio_features(b"not-audio-data", None)

    assert result["analyzed_by"] == "metadata"
    assert "note" in result
    assert "ffprobe" in result["note"].lower() or "exited" in result["note"].lower()
    assert result["size_bytes"] == 14


@pytest.mark.asyncio
async def test_text_string_falls_back(agent):
    """A plain text string (not base64, not data URL) falls back to metadata."""
    result = await agent._extract_audio_features("hello world", "txt")

    assert result["analyzed_by"] == "metadata"
    assert result["size_bytes"] > 0


# --- Helper methods ---


def test_decode_audio_bytes_data_url():
    """_decode_audio_bytes strips data URL prefix and base64-decodes."""
    raw = b"\x00\x01\x02"
    b64 = base64.b64encode(raw).decode()
    data_url = f"data:audio/wav;base64,{b64}"
    decoded, mime = PerceiverAgent._decode_audio_bytes(data_url)
    assert decoded == raw
    assert mime == "audio/wav"


def test_decode_audio_bytes_plain_bytes():
    """_decode_audio_bytes passes bytes through unchanged."""
    raw = b"\xff\xfb\x90\x00"  # MP3 frame header
    decoded, mime = PerceiverAgent._decode_audio_bytes(raw)
    assert decoded == raw
    assert mime == "application/octet-stream"


def test_decode_audio_bytes_plain_base64():
    """_decode_audio_bytes base64-decodes a plain string (no data: prefix)."""
    raw = b"audio-data"
    b64 = base64.b64encode(raw).decode()
    decoded, _ = PerceiverAgent._decode_audio_bytes(b64)
    assert decoded == raw


def test_audio_suffix_from_format_hint():
    """_audio_suffix_from_format returns .ext for known formats."""
    assert PerceiverAgent._audio_suffix_from_format("wav", "") == ".wav"
    assert PerceiverAgent._audio_suffix_from_format("MP3", "") == ".mp3"
    assert PerceiverAgent._audio_suffix_from_format("flac", "") == ".flac"
    assert PerceiverAgent._audio_suffix_from_format("ogg", "") == ".ogg"
    assert PerceiverAgent._audio_suffix_from_format("aac", "") == ".aac"


def test_audio_suffix_from_mime_type():
    """_audio_suffix_from_format falls back to MIME type mapping."""
    assert PerceiverAgent._audio_suffix_from_format(None, "audio/mpeg") == ".mp3"
    assert PerceiverAgent._audio_suffix_from_format(None, "audio/ogg") == ".ogg"
    assert PerceiverAgent._audio_suffix_from_format(None, "audio/flac") == ".flac"


def test_audio_suffix_unknown():
    """Unknown format/mime gets .audio fallback or uses format_hint as-is."""
    assert PerceiverAgent._audio_suffix_from_format(None, "audio/opus") == ".audio"
    assert PerceiverAgent._audio_suffix_from_format("xyz", "") == ".xyz"
