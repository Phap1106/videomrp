import subprocess
from pathlib import Path

import pytest

from app.services.audio_separator import separate_audio


def _fake_subprocess_run(cmd, check=True, capture_output=True):
    # Simulate spleeter creating output_dir/<stemdir>/vocals.wav and accompaniment.wav
    # Find -o <out_dir> in cmd
    try:
        out_index = cmd.index("-o")
        out_dir = Path(cmd[out_index + 1])
    except ValueError:
        # Older spleeter CLI may not include -o; look for directory in args
        out_dir = Path(cmd[-2]) if len(cmd) >= 2 else Path("./")

    # Create directory structure similar to spleeter: out_dir/<basename>/vocals.wav
    stemdir = out_dir / Path(cmd[-1]).stem
    stemdir.mkdir(parents=True, exist_ok=True)
    (stemdir / "vocals.wav").write_bytes(b"\x00\x00")
    (stemdir / "accompaniment.wav").write_bytes(b"\x00\x00")

    # Return a completed process stub
    return subprocess.CompletedProcess(cmd, 0, stdout=b"ok", stderr=b"")


@pytest.mark.asyncio
async def test_separate_audio_creates_stems(monkeypatch, tmp_path):
    src = tmp_path / "sample.wav"
    src.write_bytes(b"\x00\x00")

    # Force shutil.which to return truthy value (simulate spleeter present)
    monkeypatch.setattr("shutil.which", lambda _x: "/usr/bin/spleeter")

    # Patch subprocess.run to our fake implementation that creates files
    monkeypatch.setattr("subprocess.run", _fake_subprocess_run)

    # Use the tmp_path as output dir for isolation
    result = await separate_audio(str(src), output_dir=str(tmp_path / "out"))

    assert result["vocals"] is not None
    assert result["accompaniment"] is not None

    assert Path(result["vocals"]).exists()
    assert Path(result["accompaniment"]).exists()
