"""Smoke tests for PRIVACYSHELL. No network. Stdlib + privacyshell only."""
import io
import json
import os
import sys
import unittest
import contextlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from privacyshell import (  # noqa: E402
    TOOL_NAME,
    TOOL_VERSION,
    BROWSERS,
    PROFILES,
    build_profile,
    render_userjs,
    render_brave_policy,
    audit_userjs,
)
from privacyshell.cli import main  # noqa: E402


def _run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main(argv)
    return code, out.getvalue()


class TestMeta(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(TOOL_NAME, "privacyshell")
        self.assertTrue(TOOL_VERSION)


class TestEngine(unittest.TestCase):
    def test_tiers_are_supersets(self):
        counts = {p: build_profile("firefox", p)["setting_count"] for p in PROFILES}
        self.assertLess(counts["balanced"], counts["hardened"])
        self.assertLess(counts["hardened"], counts["paranoid"])

    def test_balanced_subset_of_hardened(self):
        bal = {s["pref"] for s in build_profile("firefox", "balanced")["settings"]}
        har = {s["pref"] for s in build_profile("firefox", "hardened")["settings"]}
        self.assertTrue(bal.issubset(har))

    def test_brave_only_policy_backed(self):
        obj = build_profile("brave", "paranoid")
        self.assertTrue(obj["settings"])
        for s in obj["settings"]:
            self.assertIsNotNone(s["brave_policy"])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            build_profile("chrome", "hardened")
        with self.assertRaises(ValueError):
            build_profile("firefox", "ultra")

    def test_render_userjs(self):
        obj = build_profile("firefox", "hardened")
        text = render_userjs(obj)
        self.assertIn("user_pref(", text)
        self.assertIn("https_only_mode", text)
        # one user_pref line per setting
        self.assertEqual(text.count("user_pref("), obj["setting_count"])

    def test_render_brave_policy_is_json(self):
        obj = build_profile("brave", "hardened")
        data = json.loads(render_brave_policy(obj))
        self.assertIn("HttpsOnlyMode", data)


class TestAudit(unittest.TestCase):
    def test_generated_passes_its_own_audit(self):
        obj = build_profile("firefox", "hardened")
        text = render_userjs(obj)
        result = audit_userjs(text, "firefox", "hardened")
        self.assertTrue(result["pass"])
        self.assertEqual(result["score"], 100)

    def test_detects_missing_and_mismatch(self):
        bad = (
            'user_pref("toolkit.telemetry.enabled", false);\n'
            'user_pref("dom.security.https_only_mode", false);\n'  # wrong value
        )
        result = audit_userjs(bad, "firefox", "hardened")
        self.assertFalse(result["pass"])
        self.assertTrue(result["missing"])
        prefs = {m["pref"] for m in result["mismatched"]}
        self.assertIn("dom.security.https_only_mode", prefs)
        self.assertLess(result["score"], 100)


class TestCLI(unittest.TestCase):
    def test_list_json(self):
        code, out = _run(["--format", "json", "list"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(set(data["browsers"]), set(BROWSERS))

    def test_generate_userjs(self):
        code, out = _run(["generate", "--browser", "firefox",
                          "--profile", "paranoid", "--emit", "userjs"])
        self.assertEqual(code, 0)
        self.assertIn("resistFingerprinting", out)

    def test_audit_stdin_fail_exit(self):
        bad = 'user_pref("toolkit.telemetry.enabled", false);\n'
        old = sys.stdin
        sys.stdin = io.StringIO(bad)
        try:
            code, out = _run(["--format", "json", "audit", "-",
                             "--profile", "hardened"])
        finally:
            sys.stdin = old
        self.assertEqual(code, 1)  # non-compliant -> non-zero
        self.assertFalse(json.loads(out)["pass"])

    def test_audit_missing_file_exit2(self):
        code, _ = _run(["audit", "/no/such/file.js"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
