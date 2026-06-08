"""Command-line interface for PRIVACYSHELL."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import TOOL_NAME, TOOL_VERSION
from .core import (
    BROWSERS,
    PROFILES,
    build_profile,
    render_userjs,
    render_brave_policy,
    audit_userjs,
)


def _print(obj: Any, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(obj, indent=2))
        return
    # table format
    if isinstance(obj, dict) and "settings" in obj:
        print(f"{obj['browser']} / {obj['profile']}  ({obj['setting_count']} prefs)")
        print("-" * 64)
        for s in obj["settings"]:
            print(f"{s['pref']:<55} {s['value']}")
        if obj["breakage_warnings"]:
            print("-" * 64)
            print(f"{len(obj['breakage_warnings'])} breakage warning(s):")
            for b in obj["breakage_warnings"]:
                print(f"  ! {b['pref']}: {b['breaks']}")
    elif isinstance(obj, dict) and "score" in obj:
        verdict = "PASS" if obj["pass"] else "FAIL"
        print(f"Audit {obj['browser']}/{obj['profile']}: {verdict}  score={obj['score']}/100")
        print(f"  compliant {obj['compliant']}/{obj['expected']}")
        if obj["missing"]:
            print(f"  missing ({len(obj['missing'])}):")
            for p in obj["missing"]:
                print(f"    - {p}")
        if obj["mismatched"]:
            print(f"  mismatched ({len(obj['mismatched'])}):")
            for m in obj["mismatched"]:
                print(f"    ~ {m['pref']}: expected {m['expected']} found {m['found']}")
    else:
        print(json.dumps(obj, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Hardened browser profile generator (Firefox/LibreWolf/Brave).",
    )
    p.add_argument("--version", action="version",
                   version=f"{TOOL_NAME} {TOOL_VERSION}")
    p.add_argument("--format", choices=("table", "json"), default="table",
                   help="output format (default: table)")
    sub = p.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="generate a hardened profile")
    gen.add_argument("--browser", choices=BROWSERS, default="firefox")
    gen.add_argument("--profile", choices=PROFILES, default="hardened")
    gen.add_argument("--emit", choices=("data", "userjs", "brave"), default="data",
                     help="data=structured (honors --format); userjs/brave=raw file")

    aud = sub.add_parser("audit", help="audit an existing user.js file")
    aud.add_argument("path", help="path to user.js (use - for stdin)")
    aud.add_argument("--browser", choices=BROWSERS, default="firefox")
    aud.add_argument("--profile", choices=PROFILES, default="hardened")

    lst = sub.add_parser("list", help="list available browsers and profiles")
    lst.add_argument("_unused", nargs="?", help=argparse.SUPPRESS)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "list":
            _print({"browsers": list(BROWSERS), "profiles": list(PROFILES)},
                   args.format)
            return 0

        if args.command == "generate":
            obj = build_profile(args.browser, args.profile)
            if args.emit == "userjs":
                sys.stdout.write(render_userjs(obj))
            elif args.emit == "brave":
                sys.stdout.write(render_brave_policy(obj))
            else:
                _print(obj, args.format)
            return 0

        if args.command == "audit":
            if args.path == "-":
                text = sys.stdin.read()
            else:
                with open(args.path, "r", encoding="utf-8") as fh:
                    text = fh.read()
            result = audit_userjs(text, args.browser, args.profile)
            _print(result, args.format)
            return 0 if result["pass"] else 1
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser.error("no command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
