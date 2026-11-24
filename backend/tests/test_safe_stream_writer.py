"""Tests for SafeStreamWriter — wrapper that prevents [Errno 5] crashes."""

import io
import sys
from unittest.mock import MagicMock, patch

import pytest

from app.core.safe_stream_writer import SafeStreamWriter, install_safe_streams


class TestSafeStreamWriterInit:
    def test_wraps_any_target(self):
        stream = io.StringIO("hello")
        wrapper = SafeStreamWriter(stream)
        assert wrapper.target is stream

    def test_wraps_none(self):
        wrapper = SafeStreamWriter(None)
        assert wrapper.target is None


class TestSafeStreamWriterWrite:
    def test_writes_to_target(self):
        stream = io.StringIO()
        wrapper = SafeStreamWriter(stream)
        wrapper.write("hello world")
        assert stream.getvalue() == "hello world"

    def test_does_not_crash_on_broken_pipe(self):
        broken = MagicMock()
        broken.write.side_effect = BrokenPipeError("broken pipe")
        wrapper = SafeStreamWriter(broken)
        # Should not raise
        wrapper.write("this will fail")

    def test_does_not_crash_on_os_error(self):
        broken = MagicMock()
        broken.write.side_effect = OSError("device error")
        wrapper = SafeStreamWriter(broken)
        wrapper.write("data")

    def test_does_not_crash_on_io_error(self):
        broken = MagicMock()
        broken.write.side_effect = IOError("io error")
        wrapper = SafeStreamWriter(broken)
        wrapper.write("data")

    def test_noop_when_target_is_none(self):
        wrapper = SafeStreamWriter(None)
        wrapper.write("anything")  # should not raise

    def test_empty_string(self):
        stream = io.StringIO()
        wrapper = SafeStreamWriter(stream)
        wrapper.write("")
        assert stream.getvalue() == ""


class TestSafeStreamWriterFlush:
    def test_flushes_target(self):
        stream = io.StringIO()
        wrapper = SafeStreamWriter(stream)
        wrapper.write("data")
        wrapper.flush()  # should not raise

    def test_noop_on_broken_pipe(self):
        broken = MagicMock()
        broken.flush.side_effect = BrokenPipeError()
        wrapper = SafeStreamWriter(broken)
        wrapper.flush()  # should not raise

    def test_noop_when_target_is_none(self):
        wrapper = SafeStreamWriter(None)
        wrapper.flush()  # should not raise


class TestSafeStreamWriterIsatty:
    def test_returns_true_for_tty(self):
        stream = io.StringIO()
        with patch.object(stream, "isatty", return_value=True):
            wrapper = SafeStreamWriter(stream)
            assert wrapper.isatty() is True

    def test_returns_false_on_exception(self):
        broken = MagicMock()
        broken.isatty.side_effect = Exception("tty error")
        wrapper = SafeStreamWriter(broken)
        assert wrapper.isatty() is False

    def test_returns_false_when_target_is_none(self):
        wrapper = SafeStreamWriter(None)
        assert wrapper.isatty() is False


class TestSafeStreamWriterGetattr:
    def test_delegates_unknown_attrs(self):
        stream = io.StringIO()
        stream.custom_attr = 42
        wrapper = SafeStreamWriter(stream)
        assert wrapper.custom_attr == 42

    def test_delegates_write_and_flush(self):
        stream = io.StringIO()
        wrapper = SafeStreamWriter(stream)
        # write and flush are defined on the class, so __getattr__ won't
        # be called for them — that's fine, they're explicitly defined.
        assert hasattr(wrapper, "write")
        assert hasattr(wrapper, "flush")


class TestInstallSafeStreams:
    @pytest.fixture(autouse=True)
    def _reset_stdout(self, monkeypatch: pytest.MonkeyPatch):
        """Restore real stdout/stderr before each test."""
        monkeypatch.setattr(sys, "stdout", sys.__stdout__)
        monkeypatch.setattr(sys, "stderr", sys.__stderr__)

    def test_installs_on_stdout(self):
        install_safe_streams()
        assert isinstance(sys.stdout, SafeStreamWriter)

    def test_installs_on_stderr(self):
        install_safe_streams()
        assert isinstance(sys.stderr, SafeStreamWriter)

    def test_is_idempotent(self):
        install_safe_streams()
        first = sys.stdout
        install_safe_streams()
        # Should not wrap again
        assert sys.stdout is first

    def test_wraps_wrapped_stdout(self):
        """If stdout is already wrapped, install_safe_streams should not double-wrap."""
        wrapped = SafeStreamWriter(sys.__stdout__)
        with patch.object(sys, "stdout", wrapped):
            install_safe_streams()
            assert isinstance(sys.stdout, SafeStreamWriter)
            # Should be the same object, not a double wrapper
            assert sys.stdout is wrapped
