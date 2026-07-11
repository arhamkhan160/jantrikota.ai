"""
utils/file_utils.py
File system utility helpers.
"""

import os
import shutil
from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    """Create directory if it does not exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_delete(path: str | Path) -> bool:
    """Delete a file or directory without raising if not found."""
    try:
        p = Path(path)
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
        return True
    except FileNotFoundError:
        return False


def list_files(directory: str | Path, extension: str | None = None) -> list[Path]:
    """List files in a directory, optionally filtered by extension."""
    d = Path(directory)
    if not d.exists():
        return []
    pattern = f"*{extension}" if extension else "*"
    return [f for f in d.glob(pattern) if f.is_file()]


def file_size_mb(path: str | Path) -> float:
    """Return file size in megabytes."""
    return os.path.getsize(path) / (1024 * 1024)
