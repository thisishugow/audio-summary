"""
檔案清理模組 (Purger)

用於定期清理應用程式產生的檔案
"""

from audio_summary.purger.purger import (
    Purger,
    setup_purger,
    start_scheduler,
    stop_scheduler,
    purge_now
)

__all__ = [
    'Purger',
    'setup_purger',
    'start_scheduler',
    'stop_scheduler',
    'purge_now'
]
