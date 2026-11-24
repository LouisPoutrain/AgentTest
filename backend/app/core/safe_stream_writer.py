"""
core/safe_stream_writer.py — Wrapper sécurisé pour stdout/stderr.

Empêche les crashs [Errno 5] Input/output error lorsque stdout/stderr
perdent leur TTY (ex: Electron, daemon mode).
"""

from __future__ import annotations

import sys


class SafeStreamWriter:
    """Empêche les crashs [Errno 5] Input/output error lorsque stdout/stderr perdent leur TTY."""
    def __init__(self, target):
        self.target = target

    def write(self, s):
        try:
            if self.target:
                return self.target.write(s)
        except (OSError, IOError, BrokenPipeError):
            pass

    def flush(self):
        try:
            if self.target:
                self.target.flush()
        except (OSError, IOError, BrokenPipeError):
            pass

    def isatty(self):
        try:
            return self.target.isatty()
        except Exception:
            return False

    def __getattr__(self, name):
        return getattr(self.target, name)


def install_safe_streams() -> None:
    """Installe les Safe StreamWriter sur stdout/stderr si ce n'est pas déjà fait."""
    if not isinstance(sys.stdout, SafeStreamWriter):
        sys.stdout = SafeStreamWriter(sys.stdout)
    if not isinstance(sys.stderr, SafeStreamWriter):
        sys.stderr = SafeStreamWriter(sys.stderr)
