// A partially-hardened Firefox user.js (intentionally incomplete + one wrong value).
// Audit it with: python -m privacyshell audit demos/01-basic/sample-user.js --profile hardened

// Telemetry
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("toolkit.telemetry.unified", false);

// Tracking protection
user_pref("privacy.trackingprotection.enabled", true);

// HTTPS - WRONG value on purpose (should be true), the audit will flag this
user_pref("dom.security.https_only_mode", false);

// Cookies
user_pref("network.cookie.cookieBehavior", 5);

// NOTE: many hardened-tier prefs (referer policy, DNS prefetch, WebRTC, etc.)
// are deliberately missing so the audit shows a partial score.
