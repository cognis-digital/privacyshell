# PRIVACYSHELL — Hardened browser profile generator — Firefox / LibreWolf / Brave

> Part of the **[Cognis Neural Suite](https://github.com/cognis-digital)** by [Cognis Digital](https://cognis.digital)
> MIT License · domain: `privacy`

[![PyPI](https://img.shields.io/pypi/v/cognis-privacyshell.svg)](https://pypi.org/project/cognis-privacyshell/)
[![CI](https://github.com/cognis-digital/privacyshell/actions/workflows/ci.yml/badge.svg)](https://github.com/cognis-digital/privacyshell/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Hardened browser profile generator — Firefox / LibreWolf / Brave.

## Install

```bash
pip install cognis-privacyshell
```

For local development from this repo:

```bash
pip install -e .
```

## Quick start

```bash
privacyshell --version
privacyshell scan demos/                          # run against bundled demo
privacyshell scan demos/ --format sarif --out r.sarif --fail-on high
privacyshell mcp                                   # start as MCP server (Cognis.Studio / Claude Desktop / Cursor)
```

## Built-in demo scenarios

Every scenario folder includes a `SCENARIO.md` describing what it represents and what findings to expect.

- `demos/01-default-firefox-prefs/` — see [`SCENARIO.md`](demos/01-default-firefox-prefs/SCENARIO.md)
- `demos/02-hardened-arkenfox/` — see [`SCENARIO.md`](demos/02-hardened-arkenfox/SCENARIO.md)
- `demos/03-partial-librewolf/` — see [`SCENARIO.md`](demos/03-partial-librewolf/SCENARIO.md)

## How it fits the Cognis Neural Suite

This tool is one of 52 in the [Cognis Neural Suite](https://github.com/cognis-digital). The full suite + launcher lives at:

- Suite landing: https://cognis.digital
- All 52 repos: https://github.com/cognis-digital
- Cognis.Studio (Enterprise AI Workforce, MCP host): https://cognis.studio

Every Suite tool ships an MCP server, so Cognis.Studio agents can call them as scoped capabilities.

## License

MIT. See [LICENSE](LICENSE).

## About

**[Cognis Digital](https://cognis.digital)** — Wyoming, USA · *Making Tomorrow Better Today: Advanced Cybersecurity, AI Innovation, and Blockchain Expertise.*
