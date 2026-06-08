# Demo 01 - Basic: generate and audit a hardened Firefox profile

PRIVACYSHELL turns a privacy *intent* (browser + hardening tier) into concrete,
arkenfox-style configuration you can drop into a real profile.

## 1. See what's available

```
python -m privacyshell list
```

Browsers: `firefox`, `librewolf`, `brave`. Profiles: `balanced`, `hardened`,
`paranoid` (each tier is a strict superset of the one below it).

## 2. Generate a hardened Firefox user.js

```
python -m privacyshell generate --browser firefox --profile hardened --emit userjs > user.js
```

This writes a real `user.js` with `user_pref(...)` lines and inline rationale.
Copy it into your Firefox profile directory (`about:profiles` -> Root Directory).

For Brave, emit an enterprise-policy JSON instead:

```
python -m privacyshell generate --browser brave --profile paranoid --emit brave
```

## 3. Audit an existing user.js against a target tier

The file `sample-user.js` in this folder is a *partially* hardened config.
Audit it against the `hardened` Firefox tier:

```
python -m privacyshell audit demos/01-basic/sample-user.js --browser firefox --profile hardened
```

It reports missing prefs, value mismatches, and a 0-100 compliance score, and
exits non-zero when the file is not fully compliant - so it works in CI.

Machine-readable output is one flag away:

```
python -m privacyshell audit demos/01-basic/sample-user.js --format json
```
