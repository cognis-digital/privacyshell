"""PRIVACYSHELL - Hardened browser profile generator.

Generates privacy-hardened configuration for Firefox / LibreWolf (user.js)
and Brave (policy JSON), in the spirit of arkenfox/user.js.

Standard library only. Zero install.
"""
from .core import (
    BROWSERS,
    PROFILES,
    Setting,
    Engine,
    build_profile,
    render_userjs,
    render_brave_policy,
    audit_userjs,
)

TOOL_NAME = "privacyshell"
TOOL_VERSION = "1.0.0"

__all__ = [
    "TOOL_NAME",
    "TOOL_VERSION",
    "BROWSERS",
    "PROFILES",
    "Setting",
    "Engine",
    "build_profile",
    "render_userjs",
    "render_brave_policy",
    "audit_userjs",
]
