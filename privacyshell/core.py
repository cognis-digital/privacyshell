"""PRIVACYSHELL — auto-generated detector core."""
from __future__ import annotations
import re, time
from pathlib import Path
from cognis_core import Finding, ScanResult, score

TOOL_NAME = "PRIVACYSHELL"
TOOL_VERSION = "0.1.0"

PATTERNS = [('PS-TELEM-001', 'medium', 2.0, 'TELEMETRY_ON', '(?i)user_pref\\(\\s*"(?:privacy\\.do_not_track|toolkit\\.telemetry\\.enabled)"\\s*,\\s*(false|true)', 'Disable telemetry: set privacy.do_not_track=true and toolkit.telemetry.enabled=false.'), ('PS-SAFEB-001', 'low', 1.5, 'SAFEBROWSING_HASH_LEAK', '(?i)user_pref\\(\\s*"browser\\.safebrowsing\\.malware\\.enabled"\\s*,\\s*true', 'Consider disabling or routing through privacy-respecting service.'), ('PS-WEBRTC-001', 'high', 2.5, 'WEBRTC_IP_LEAK', '(?i)user_pref\\(\\s*"media\\.peerconnection\\.enabled"\\s*,\\s*true', 'Disable WebRTC or apply ICE mDNS only policy.')]
FILE_GLOBS = ['user.js', 'prefs.js', '*.cfg']

def scan(target: str, **opts) -> ScanResult:
    t0 = time.time()
    result = ScanResult(tool_name=TOOL_NAME, tool_version=TOOL_VERSION, target=str(target))
    p = Path(target)
    files: list[Path] = []
    if p.is_dir():
        for g in FILE_GLOBS:
            files.extend(p.rglob(g))
    elif p.is_file():
        files = [p]
    result.items_scanned = len(files)
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for rid,sev,w,title,pat,rem in PATTERNS:
            for m in re.finditer(pat, text):
                line = text.count(chr(10), 0, m.start()) + 1
                result.add(Finding(
                    id=rid, severity=sev, weight=w, title=title,
                    description=f"{title}: `{m.group(0)[:80]}`",
                    location=f"{f}:{line}", remediation=rem, category="browser-hardening",
                ))
    result.composite_score, result.risk_level = score(result.findings)
    result.scan_duration_ms = int((time.time()-t0)*1000)
    return result
