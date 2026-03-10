# Citadel Codex Skill

Use this Codex skill to integrate [Mighty AI](https://trymighty.ai) Citadel protections into LLM apps:
- Prompt-injection and jailbreak detection
- Credential-leak detection
- Input/output scanning for chat and RAG pipelines
- Optional multimodal scans (images, PDFs, documents) via Citadel Gateway

This repository is packaged as a Codex skill at repo root (`SKILL.md`, `agents/`, `references/`, `scripts/`).

## Install (OpenAI Skills Convention)

OpenAI's skills ecosystem uses `$skill-installer` for installing skills, including from GitHub repos.

This skill is not in the curated catalog yet, so install it from GitHub.

### Option A: Install via `$skill-installer` in Codex Chat

Paste this in Codex:

```text
Use $skill-installer to install a skill from GitHub repo MunamWasi/Citadel-Skill-Codex, path ., and name citadel.
```

Then restart Codex.

### Option B: Deterministic Terminal Command (Same Installer)

```bash
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
python3 "$CODEX_HOME/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo MunamWasi/Citadel-Skill-Codex \
  --path . \
  --name citadel
```

Then restart Codex.

## Use The Skill

In Codex chat:

```text
Use $citadel to secure a chat pipeline by scanning user input, tool output, and model output.
```

Decision rule used by the skill:
- Text-only and no paid key: use Citadel OSS CLI/sidecar.
- Images/PDF/docs or paid key present: use Citadel Gateway `/v1/scan`.

What actually gets scanned:
- Only requests you explicitly send through the OSS CLI/sidecar or Gateway `/v1/scan`
- Not every app request automatically
- If you want hard enforcement, wire Citadel into the path used by every LLM input/output call

## API Key Setup (Gateway)

`scripts/scan_gateway.py` resolves auth in this order:
1. `--api-key`
2. `MIGHTY_PRO_API_KEY`
3. `MIGHTY_API_KEY`

Set one for your shell:

```bash
export MIGHTY_PRO_API_KEY="YOUR_PRO_KEY_HERE"
# or
export MIGHTY_API_KEY="YOUR_KEY_HERE"
```

In production, put the same env var in your hosting provider's secret store or runtime environment settings.

Security note:
- Do not commit secrets.
- `.env` and `.env.*` are ignored by `.gitignore`.

## Quick Test

Dry run (no network call):

```bash
python3 scripts/scan_gateway.py --text "hello" --dry-run
```

Use the `auth_source` field in that output to verify which key source is being used.

Print equivalent curl:

```bash
python3 scripts/scan_gateway.py --text "hello" --print-curl
```

Offline stub test:

Terminal A:

```bash
python3 scripts/mock_gateway_server.py --port 18081
```

Terminal B:

```bash
python3 scripts/scan_gateway.py --api-key test --base-url http://127.0.0.1:18081 --text "hello"
```

How to verify Citadel is really in the path:
- Send one safe prompt and one obvious attack prompt through your actual app integration
- Confirm your integration receives Citadel fields such as `action`, `risk_score`, or `risk_level`
- A model refusal by itself is not proof Citadel ran; provider safety can also refuse requests

## Uninstall

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/citadel"
```

Restart Codex after uninstalling.

## Maintainer Notes

Validate before pushing changes:

```bash
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
python3 "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" .
```

Publish:

```bash
git add -A
git commit -m "Update skill"
git push origin main
```
