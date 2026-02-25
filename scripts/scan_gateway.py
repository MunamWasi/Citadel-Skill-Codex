#!/usr/bin/env python3
"""
Scan text or a file (image/pdf/document) using the Mighty Citadel Gateway.

Usage:
  python scripts/scan_gateway.py --text "hello"
  python scripts/scan_gateway.py --file ./contract.pdf --content-type pdf
  python scripts/scan_gateway.py --file ./image.png --scan-phase input --profile balanced --analysis-mode comprehensive

Auth:
  Pass --api-key, or set MIGHTY_PRO_API_KEY / MIGHTY_API_KEY.
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://gateway.trymighty.ai"
DEFAULT_API_KEY_ENV = "MIGHTY_API_KEY"
PRO_API_KEY_ENV = "MIGHTY_PRO_API_KEY"


def b64_file(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def sh_single_quote(value: str) -> str:
    # Wrap in single quotes and escape internal single quotes for safe copy/paste in sh/zsh/bash.
    return "'" + value.replace("'", "'\"'\"'") + "'"


def resolve_api_key(cli_api_key: str | None) -> tuple[str, str]:
    if cli_api_key:
        return cli_api_key, "--api-key"

    pro_api_key = os.getenv(PRO_API_KEY_ENV)
    if pro_api_key:
        return pro_api_key, PRO_API_KEY_ENV

    api_key = os.getenv(DEFAULT_API_KEY_ENV)
    if api_key:
        return api_key, DEFAULT_API_KEY_ENV

    return "", ""


def post_json(url: str, api_key: str, payload: dict, timeout_s: int) -> tuple[int, str]:
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=timeout_s) as resp:
            return resp.getcode(), resp.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return exc.code, body
    except URLError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 0, ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api-key",
        default=None,
        help="Mighty API key (if omitted: MIGHTY_PRO_API_KEY, then MIGHTY_API_KEY)",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--text", help="Text content to scan")
    parser.add_argument("--file", help="Path to file to scan (image/pdf/document)")
    parser.add_argument("--content-type", default="auto", choices=["auto", "text", "image", "pdf", "document"])
    parser.add_argument("--scan-phase", default="input", choices=["input", "output"])
    parser.add_argument(
        "--profile",
        default="balanced",
        choices=["strict", "balanced", "permissive", "code_assistant", "ai_safety"],
    )
    parser.add_argument("--analysis-mode", default="secure", choices=["fast", "secure", "comprehensive"])
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--scan-group-id", default=None, help="Required when --scan-phase=output")
    parser.add_argument("--request-id", default=None)
    parser.add_argument(
        "--context",
        default=None,
        help="user_prompt|assistant_response|image_ocr|pdf_text|document_text|vision",
    )
    parser.add_argument("--original-prompt", default=None, help="For output scan drift checks")
    parser.add_argument("--async", dest="async_", action="store_true", help="Async deep scan (esp. image/pdf)")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds (default: 60)")
    parser.add_argument("--dry-run", action="store_true", help="Print the request payload and exit")
    parser.add_argument("--print-curl", action="store_true", help="Print a curl command and exit")
    args = parser.parse_args()
    api_key, api_key_source = resolve_api_key(args.api_key)

    if bool(args.text) == bool(args.file):
        print("Provide exactly one of --text or --file.", file=sys.stderr)
        return 2

    if args.scan_phase == "output" and not args.scan_group_id:
        print("scan_group_id is required when scan_phase=output.", file=sys.stderr)
        return 2

    if args.text:
        content = args.text
        content_type = "text" if args.content_type == "auto" else args.content_type
    else:
        fpath = Path(args.file)
        if not fpath.exists():
            print(f"File not found: {fpath}", file=sys.stderr)
            return 2
        if args.content_type == "text":
            print("--content-type=text is invalid with --file.", file=sys.stderr)
            return 2
        content = b64_file(fpath)
        content_type = args.content_type

    payload = {
        "content": content,
        "content_type": content_type,
        "scan_phase": args.scan_phase,
        "profile": args.profile,
        "analysis_mode": args.analysis_mode,
        "async": bool(args.async_),
    }

    if args.session_id:
        payload["session_id"] = args.session_id
    if args.scan_group_id:
        payload["scan_group_id"] = args.scan_group_id
    if args.request_id:
        payload["request_id"] = args.request_id
    if args.context:
        payload["context"] = args.context
    if args.original_prompt:
        payload["original_prompt"] = args.original_prompt

    url = f"{args.base_url.rstrip('/')}/v1/scan"

    if args.print_curl:
        # Use env vars to avoid leaking a real key into terminal history.
        json_payload = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        print(
            "curl -sS -X POST "
            f"{sh_single_quote(url)} "
            "-H 'Content-Type: application/json' "
            "-H 'X-API-Key: ${MIGHTY_PRO_API_KEY:-$MIGHTY_API_KEY}' "
            f"--data {sh_single_quote(json_payload)}"
        )
        return 0

    if args.dry_run:
        print(
            json.dumps(
                {
                    "url": url,
                    "headers": {"Content-Type": "application/json", "X-API-Key": "<redacted>"},
                    "auth_source": api_key_source or "<none>",
                    "payload": payload,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if not api_key:
        print(
            "Missing API key. Provide --api-key or set MIGHTY_PRO_API_KEY/MIGHTY_API_KEY.",
            file=sys.stderr,
        )
        return 2

    status_code, body_text = post_json(url=url, api_key=api_key, payload=payload, timeout_s=args.timeout)

    try:
        out = json.loads(body_text)
    except Exception:
        preview = (body_text or "")[:500]
        status_str = status_code if status_code else "unknown"
        print(f"Non-JSON response (status={status_str}): {preview}", file=sys.stderr)
        return 1

    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if 200 <= status_code < 300 else 1


if __name__ == "__main__":
    raise SystemExit(main())
