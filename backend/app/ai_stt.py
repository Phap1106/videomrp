from pathlib import Path
from typing import Tuple
from faster_whisper import WhisperModel

_model = None

def get_model():
    global _model
    if _model is None:
        # "small" chạy ổn trên CPU; bạn có thể đổi "medium"/"large-v3"
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model

def transcribe(audio_or_video_path: Path) -> Tuple[str, list[dict]]:
    model = get_model()
    segments, info = model.transcribe(str(audio_or_video_path), vad_filter=True)
    full = []
    segs = []
    for s in segments:
        full.append(s.text.strip())
        segs.append({"start": s.start, "end": s.end, "text": s.text.strip()})
    return " ".join(full).strip(), segs

def to_srt(segments: list[dict]) -> str:
    def ts(x: float) -> str:
        h = int(x // 3600); x -= h*3600
        m = int(x // 60); x -= m*60
        s = int(x); ms = int((x - s) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{ts(seg['start'])} --> {ts(seg['end'])}")
        lines.append(seg["text"])
        lines.append("")
    return "\n".join(lines).strip() + "\n"
