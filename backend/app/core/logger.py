import sys

try:
    from loguru import logger
except Exception:  # pragma: no cover - fallback when loguru not installed
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("video_reup")

    # Add convenience wrapper methods to match loguru API where possible
    class _LoggerShim:
        def __init__(self, impl):
            self._impl = impl

        def debug(self, *args, **kwargs):
            self._impl.debug(*args, **kwargs)

        def info(self, *args, **kwargs):
            self._impl.info(*args, **kwargs)

        def warning(self, *args, **kwargs):
            self._impl.warning(*args, **kwargs)

        def error(self, *args, **kwargs):
            self._impl.error(*args, **kwargs)

    logger = _LoggerShim(logger)


def setup_logging():
    """Setup logging configuration"""
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    )
    logger.add("logs/app.log", rotation="500 MB", retention="10 days", compression="zip")
