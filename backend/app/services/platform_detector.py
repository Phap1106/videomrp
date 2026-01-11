# app/services/platform_detector.py
import re
from typing import Any

from app.models import Platform


class PlatformDetector:
    """
    Detect platform by URL + provide per-platform rules for /api/platforms
    (keep backward-compatible method names).
    """

    _PATTERNS = [
        (
            Platform.TIKTOK,
            re.compile(r"(tiktok\.com|tiktokv\.com|tiktokcdn\.com)", re.I),
        ),
        (Platform.DOUYIN, re.compile(r"(douyin\.com|iesdouyin\.com)", re.I)),
        (Platform.YOUTUBE, re.compile(r"(youtube\.com|youtu\.be)", re.I)),
        (Platform.FACEBOOK, re.compile(r"(facebook\.com|fb\.watch|fbcdn\.net)", re.I)),
        (Platform.INSTAGRAM, re.compile(r"(instagram\.com|instagr\.am)", re.I)),
    ]

    @staticmethod
    def detect(url: str) -> Platform:
        url = (url or "").strip()
        for p, rx in PlatformDetector._PATTERNS:
            if rx.search(url):
                return p
        return Platform.GENERIC

    @staticmethod
    def detect_platform(url: str) -> Platform:
        return PlatformDetector.detect(url)

    @staticmethod
    def get_platform(url: str) -> Platform:
        return PlatformDetector.detect(url)

    @staticmethod
    def is_supported(url: str) -> bool:
        return PlatformDetector.detect(url) != Platform.GENERIC

    @staticmethod
    def get_platform_rules(platform: Platform | str) -> dict[str, Any]:
        if isinstance(platform, str):
            try:
                platform = Platform(platform)
            except Exception:
                platform = Platform.GENERIC

        rules: dict[str, Any] = {
            "enabled": platform != Platform.GENERIC,
            "min_duration": 5,
            "max_duration": 600,
            "supports_subtitles": True,
            "supports_music_change": True,
            "supports_watermark_removal": True,
            "supports_effects": True,
        }

        if platform == Platform.INSTAGRAM:
            rules["max_duration"] = 180

        return rules
