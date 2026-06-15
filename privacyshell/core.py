"""Core engine for PRIVACYSHELL.

Real logic: a curated catalog of Firefox/LibreWolf prefs (arkenfox-inspired)
tiered by hardening profile, plus Brave enterprise-policy equivalents.

No network, no third-party deps.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

BROWSERS = ("firefox", "librewolf", "brave")

# Hardening tiers. Each higher tier is a strict superset of the lower one.
PROFILES = ("balanced", "hardened", "paranoid")
_TIER_RANK = {"balanced": 0, "hardened": 1, "paranoid": 2}


@dataclass(frozen=True)
class Setting:
    """A single privacy preference.

    pref:    Firefox about:config key.
    value:   desired value (bool / int / str).
    tier:    minimum profile tier at which this is applied.
    why:     short human rationale.
    breaks:  optional note on what functionality it may break.
    brave:   optional Brave policy (key, value) equivalent; None if N/A.
    """

    pref: str
    value: Any
    tier: str
    why: str
    breaks: str = ""
    brave: tuple[str, Any] | None = None


# --- Curated catalog -------------------------------------------------------
# Inspired by arkenfox/user.js section numbering. Not exhaustive, but real
# and individually defensible.
_CATALOG: list[Setting] = [
    # Telemetry / data collection
    Setting("datareporting.healthreport.uploadEnabled", False, "balanced",
            "Disable Firefox Health Report upload",
            brave=("MetricsReportingEnabled", False)),
    Setting("toolkit.telemetry.enabled", False, "balanced",
            "Disable telemetry collection"),
    Setting("toolkit.telemetry.unified", False, "balanced",
            "Disable unified telemetry"),
    Setting("app.shield.optoutstudies.enabled", False, "balanced",
            "Disable Shield/Normandy studies"),
    Setting("browser.discovery.enabled", False, "balanced",
            "Disable add-on recommendations telemetry"),
    Setting("breakpad.reportURL", "", "hardened",
            "Strip crash-report submission URL"),
    # Safe Browsing (sends URLs/hashes to Google)
    Setting("browser.safebrowsing.malware.enabled", True, "balanced",
            "Keep malware protection (local list) on"),
    Setting("browser.safebrowsing.downloads.remote.enabled", False, "hardened",
            "Stop sending download metadata to Google",
            breaks="Loses remote binary reputation checks"),
    # Search / suggestions
    Setting("browser.search.suggest.enabled", False, "hardened",
            "Disable search suggestions (keystrokes to engine)",
            breaks="No live search suggestions"),
    Setting("browser.urlbar.suggest.searches", False, "hardened",
            "Disable address-bar search suggestions"),
    # Geolocation
    Setting("geo.enabled", False, "hardened",
            "Disable geolocation",
            breaks="Maps/store-locator features",
            brave=("DefaultGeolocationSetting", 2)),
    # WebRTC IP leak
    Setting("media.peerconnection.enabled", True, "balanced",
            "Keep WebRTC but harden it below"),
    Setting("media.peerconnection.ice.default_address_only", True, "hardened",
            "Limit WebRTC to default route (anti IP-leak)"),
    Setting("media.peerconnection.ice.no_host", True, "paranoid",
            "Hide local IPs from WebRTC",
            breaks="Some LAN/P2P apps",
            brave=("WebRtcIPHandling", "disable_non_proxied_udp")),
    # Fingerprinting resistance
    Setting("privacy.resistFingerprinting", True, "paranoid",
            "Enable RFP (uniform UA, canvas, timezone, etc.)",
            breaks="Letterboxing, fixed window size, no custom DPI"),
    Setting("privacy.trackingprotection.enabled", True, "balanced",
            "Enable Enhanced Tracking Protection globally"),
    Setting("privacy.trackingprotection.fingerprinting.enabled", True, "balanced",
            "Block known fingerprinters"),
    Setting("privacy.trackingprotection.cryptomining.enabled", True, "balanced",
            "Block known cryptominers"),
    # Cookies / state
    Setting("network.cookie.cookieBehavior", 5, "balanced",
            "Total Cookie Protection (dFPI, behavior=5)"),
    Setting("privacy.partition.network_state", True, "hardened",
            "Partition network state by first party"),
    Setting("privacy.firstparty.isolate", True, "paranoid",
            "First-Party Isolation",
            breaks="Cross-site logins / federated auth"),
    Setting("network.cookie.lifetimePolicy", 2, "paranoid",
            "Clear cookies at session end",
            breaks="You will be logged out on restart"),
    # Referer
    Setting("network.http.referer.XOriginPolicy", 2, "hardened",
            "Send Referer only on same eTLD+1"),
    Setting("network.http.referer.XOriginTrimmingPolicy", 2, "hardened",
            "Trim cross-origin Referer to origin only"),
    # DNS / connectivity prefetch
    Setting("network.dns.disablePrefetch", True, "hardened",
            "Disable DNS prefetching"),
    Setting("network.prefetch-next", False, "hardened",
            "Disable link prefetching"),
    Setting("network.predictor.enabled", False, "hardened",
            "Disable network predictor"),
    # HTTPS
    Setting("dom.security.https_only_mode", True, "balanced",
            "Enable HTTPS-Only mode",
            brave=("HttpsOnlyMode", "force_enabled")),
    Setting("dom.security.https_only_mode_send_http_background_request", False,
            "paranoid", "No background HTTP probe in HTTPS-Only mode"),
    # Disk leaks / history
    Setting("browser.formfill.enable", False, "paranoid",
            "Disable form autofill history"),
    Setting("signon.autofillForms", False, "paranoid",
            "Disable login autofill",
            breaks="Manual login each time"),
    Setting("browser.cache.disk.enable", False, "paranoid",
            "Disable disk cache (RAM only)",
            breaks="More re-downloads / RAM use"),
]


@dataclass
class Engine:
    """Resolves the catalog against a (browser, profile) request."""

    browser: str
    profile: str
    settings: list[Setting] = field(default_factory=list)

    @property
    def rank(self) -> int:
        try:
            return _TIER_RANK[self.profile]
        except KeyError:
            raise ValueError(
                f"unknown profile {self.profile!r}; choose from {PROFILES}"
            ) from None

    def resolve(self) -> list[Setting]:
        out = [s for s in _CATALOG if _TIER_RANK[s.tier] <= self.rank]
        # Brave can only enforce settings that have a policy equivalent.
        if self.browser == "brave":
            out = [s for s in out if s.brave is not None]
        self.settings = out
        return out


def build_profile(browser: str, profile: str) -> dict[str, Any]:
    """Build a structured profile description (the canonical data object)."""
    browser = browser.lower()
    profile = profile.lower()
    if browser not in BROWSERS:
        raise ValueError(f"unknown browser {browser!r}; choose from {BROWSERS}")
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}; choose from {PROFILES}")

    eng = Engine(browser, profile)
    settings = eng.resolve()
    breakage = [
        {"pref": s.pref, "breaks": s.breaks}
        for s in settings if s.breaks
    ]
    return {
        "browser": browser,
        "profile": profile,
        "setting_count": len(settings),
        "breakage_warnings": breakage,
        "settings": [
            {
                "pref": s.pref,
                "value": s.value,
                "tier": s.tier,
                "why": s.why,
                "breaks": s.breaks,
                "brave_policy": list(s.brave) if s.brave else None,
            }
            for s in settings
        ],
    }


def _js_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))


def render_userjs(profile_obj: dict[str, Any]) -> str:
    """Render a Firefox/LibreWolf user.js file."""
    required = {"browser", "profile", "setting_count", "settings"}
    missing_keys = required - set(profile_obj)
    if missing_keys:
        raise ValueError(
            f"profile_obj is missing required keys: {sorted(missing_keys)}"
        )
    lines = [
        "// PRIVACYSHELL generated user.js",
        f"// browser={profile_obj['browser']} profile={profile_obj['profile']}",
        f"// {profile_obj['setting_count']} prefs. Place in your profile folder.",
        "",
    ]
    for s in profile_obj["settings"]:
        breaks_note = f"  [BREAKS: {s['breaks']}]" if s.get("breaks") else ""
        lines.append(f"// {s['why']}{breaks_note}")
        lines.append(f'user_pref("{s["pref"]}", {_js_literal(s["value"])});')
    lines.append("")
    return "\n".join(lines)


def render_brave_policy(profile_obj: dict[str, Any]) -> str:
    """Render a Brave/Chromium enterprise-policy JSON document."""
    if "settings" not in profile_obj:
        raise ValueError("profile_obj is missing required key: 'settings'")
    policy: dict[str, Any] = {}
    for s in profile_obj["settings"]:
        bp = s.get("brave_policy")
        if bp:
            policy[bp[0]] = bp[1]
    return json.dumps(policy, indent=2, sort_keys=True) + "\n"


_USERPREF_RE = re.compile(
    r'^\s*user_pref\(\s*"([^"]+)"\s*,\s*(.+?)\s*\)\s*;', re.MULTILINE
)


def _parse_userjs(text: str) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for m in _USERPREF_RE.finditer(text):
        key, raw = m.group(1), m.group(2).strip()
        if raw in ("true", "false"):
            val: Any = raw == "true"
        elif raw.startswith('"') and raw.endswith('"'):
            val = raw[1:-1]
        else:
            try:
                val = int(raw)
            except ValueError:
                val = raw
        found[key] = val
    return found


def audit_userjs(text: str, browser: str, profile: str) -> dict[str, Any]:
    """Audit an existing user.js against a target profile.

    Returns missing prefs, mismatched values, and a 0-100 score.
    Raises ValueError for unknown browser/profile or if text is None.
    """
    if text is None:
        raise ValueError("text must be a string, not None")
    target = build_profile(browser, profile)
    expected = {s["pref"]: s["value"] for s in target["settings"]}
    actual = _parse_userjs(text)

    missing, mismatched, ok = [], [], []
    for pref, want in expected.items():
        if pref not in actual:
            missing.append(pref)
        elif actual[pref] != want:
            mismatched.append({"pref": pref, "expected": want, "found": actual[pref]})
        else:
            ok.append(pref)

    total = len(expected)
    score = round(100 * len(ok) / total) if total else 100
    return {
        "browser": browser,
        "profile": profile,
        "expected": total,
        "compliant": len(ok),
        "missing": missing,
        "mismatched": mismatched,
        "score": score,
        "pass": not missing and not mismatched,
    }
