import subprocess
from pathlib import Path
from .core.config import settings

def tts_piper(text: str, out_wav: Path) -> None:
    if not settings.piper_model_path:
        raise RuntimeError("Missing PIPER_MODEL_PATH")

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    # Piper CLI đọc text từ stdin
    p = subprocess.run(
        [settings.piper_bin, "--model", settings.piper_model_path, "--output_file", str(out_wav)],
        input=text, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "Piper TTS failed")
