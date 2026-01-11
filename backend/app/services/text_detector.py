# app/services/text_detector.py
from __future__ import annotations

from typing import Any, List, Tuple
from pathlib import Path
import subprocess
import httpx
import json

from app.core.config import settings
from app.core.logger import logger


class TextDetector:
    """Extract transcript and basic segments from video using Deepgram (if configured).

    Falls back to minimal empty transcript/segments when no key is available.
    """

    async def extract_text(self, video_path: str) -> Tuple[str, List[dict[str, Any]]]:
        # 1) If Deepgram key is configured, use their pre-recorded endpoint
        if getattr(settings, "DEEPGRAM_API_KEY", None):
            try:
                return await self._deepgram_transcribe(video_path)
            except Exception as e:
                logger.warning(f"Deepgram transcription failed: {e}")
                # fallthrough to minimal fallback

        # 2) No key or transcription failed -> return minimal safe result
        return "", []

    async def _deepgram_transcribe(self, video_path: str) -> Tuple[str, List[dict[str, Any]]]:
        video_path = str(video_path)
        wav_path = await self._extract_wav(video_path)

        url = "https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true&punctuate=true"
        headers = {
            "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
            "Content-Type": "audio/wav",
        }

        data = Path(wav_path).read_bytes()
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, content=data, headers=headers)
            r.raise_for_status()
            j = r.json()

        alt = j.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0]

        transcript = alt.get("transcript", "") or ""
        words = alt.get("words", []) or []

        # Build segments roughly every ~5s
        segments: List[dict[str, Any]] = []
        buf = []
        seg_start = None
        last_end = None

        for w in words:
            ws = w.get("start")
            we = w.get("end")
            token = w.get("punctuated_word") or w.get("word") or ""

            if seg_start is None and ws is not None:
                seg_start = float(ws)

            if token:
                buf.append(token)
            if we is not None:
                last_end = float(we)

            if seg_start is not None and last_end is not None and (last_end - seg_start) >= 5.0:
                segments.append(
                    {
                        "start_time": seg_start,
                        "end_time": last_end,
                        "text": " ".join(buf).strip(),
                        "has_text": False,
                        "has_face": False,
                    }
                )
                buf = []
                seg_start = None
                last_end = None

        if buf and seg_start is not None and last_end is not None:
            segments.append(
                {
                    "start_time": seg_start,
                    "end_time": last_end,
                    "text": " ".join(buf).strip(),
                    "has_text": False,
                    "has_face": False,
                }
            )

        return transcript, segments

    async def _extract_wav(self, video_path: str) -> str:
        out = Path(settings.TEMP_DIR) / (Path(video_path).stem + ".wav")
        out.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            settings.FFMPEG_PATH,
            "-y",
            "-i",
            video_path,
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(out),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except Exception as e:
            logger.error(f"Failed to extract audio for Deepgram: {e}")
            raise

        return str(out)
