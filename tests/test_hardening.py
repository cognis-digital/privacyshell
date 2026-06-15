"""Edge-case and error-path tests added during production hardening.

All new paths introduced in this hardening pass are covered here.
No existing tests are modified.
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from privacyshell.core import (  # noqa: E402
    Engine,
    audit_userjs,
    build_profile,
    render_brave_policy,
    render_userjs,
)
from privacyshell.cli import main  # noqa: E402


def _run(argv, stdin_text: str | None = None):
    """Run main() capturing stdout; optionally inject stdin text."""
    out = io.StringIO()
    err = io.StringIO()
    old_stdin = sys.stdin
    if stdin_text is not None:
        sys.stdin = io.StringIO(stdin_text)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
    finally:
        sys.stdin = old_stdin
    return code, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# core.py — Engine.rank with unknown profile
# ---------------------------------------------------------------------------
class TestEngineRank(unittest.TestCase):
    def test_unknown_profile_raises_valueerror(self):
        """Engine.rank must raise ValueError, not KeyError, on bad profile."""
        eng = Engine(browser="firefox", profile="unknown")
        with self.assertRaises(ValueError) as ctx:
            _ = eng.rank
        self.assertIn("unknown", str(ctx.exception))


# ---------------------------------------------------------------------------
# core.py — render_userjs validates required keys
# ---------------------------------------------------------------------------
class TestRenderUserjs(unittest.TestCase):
    def test_missing_keys_raises_valueerror(self):
        """render_userjs must raise ValueError when required keys are absent."""
        with self.assertRaises(ValueError) as ctx:
            render_userjs({"browser": "firefox"})  # missing profile/settings/setting_count
        self.assertIn("missing required keys", str(ctx.exception))

    def test_empty_settings_list_produces_header_only(self):
        """render_userjs with an empty settings list still produces a valid header."""
        obj = {
            "browser": "firefox",
            "profile": "balanced",
            "setting_count": 0,
            "settings": [],
        }
        text = render_userjs(obj)
        self.assertIn("PRIVACYSHELL generated user.js", text)
        self.assertEqual(text.count("user_pref("), 0)


# ---------------------------------------------------------------------------
# core.py — render_brave_policy validates required keys
# ---------------------------------------------------------------------------
class TestRenderBravePolicy(unittest.TestCase):
    def test_missing_settings_key_raises_valueerror(self):
        with self.assertRaises(ValueError) as ctx:
            render_brave_policy({})
        self.assertIn("settings", str(ctx.exception))

    def test_empty_settings_returns_empty_json_object(self):
        import json
        result = render_brave_policy({"settings": []})
        self.assertEqual(json.loads(result), {})


# ---------------------------------------------------------------------------
# core.py — audit_userjs with None text
# ---------------------------------------------------------------------------
class TestAuditUserjs(unittest.TestCase):
    def test_none_text_raises_valueerror(self):
        with self.assertRaises(ValueError) as ctx:
            audit_userjs(None, "firefox", "hardened")  # type: ignore[arg-type]
        self.assertIn("None", str(ctx.exception))

    def test_empty_text_all_missing(self):
        """An empty file string should mark all expected prefs as missing."""
        result = audit_userjs("", "firefox", "balanced")
        self.assertFalse(result["pass"])
        self.assertTrue(result["missing"])
        self.assertEqual(result["score"], 0)

    def test_unknown_browser_raises_valueerror(self):
        with self.assertRaises(ValueError):
            audit_userjs("", "ie", "hardened")

    def test_unknown_profile_raises_valueerror(self):
        with self.assertRaises(ValueError):
            audit_userjs("", "firefox", "nuclear")


# ---------------------------------------------------------------------------
# cli.py — audit of a non-UTF-8 binary file returns exit code 2
# ---------------------------------------------------------------------------
class TestCLIUnicodeError(unittest.TestCase):
    def test_binary_file_exits_2(self):
        """Feeding a binary (non-UTF-8) file to audit must exit 2 with a clear error."""
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False) as tmp:
            # Write bytes that are invalid UTF-8
            tmp.write(b"\xff\xfe bad bytes \x80\x81\x82")
            tmp_path = tmp.name
        try:
            code, _out, err = _run(["audit", tmp_path])
            self.assertEqual(code, 2)
            self.assertIn("UTF-8", err)
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# cli.py — audit of an explicitly missing file returns exit code 2 with message
# ---------------------------------------------------------------------------
class TestCLIMissingFile(unittest.TestCase):
    def test_missing_file_error_message(self):
        """Missing-file error message should mention the path."""
        code, _out, err = _run(["audit", "/definitely/does/not/exist.js"])
        self.assertEqual(code, 2)
        self.assertIn("not found", err.lower())


# ---------------------------------------------------------------------------
# cli.py — audit of a valid file that fully passes exits 0
# ---------------------------------------------------------------------------
class TestCLIAuditFullPass(unittest.TestCase):
    def test_perfect_userjs_exits_0(self):
        """A fully-compliant user.js must exit 0 (pass)."""
        obj = build_profile("firefox", "balanced")
        from privacyshell.core import render_userjs as _ruj
        text = _ruj(obj)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(text)
            tmp_path = tmp.name
        try:
            code, _out, _err = _run(["audit", tmp_path, "--profile", "balanced"])
            self.assertEqual(code, 0)
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
