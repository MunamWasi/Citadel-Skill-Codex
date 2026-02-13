# Mighty Citadel Gateway (paid) - reference

## Endpoint
Base URL: https://gateway.trymighty.ai
POST /v1/scan
Header: X-API-Key: <key>

## Request fields
Required:
- content: string (text) or base64 (image/pdf/document)
- scan_phase: "input" or "output"

Optional (recommended defaults in parentheses):
- content_type: "auto" | "text" | "image" | "pdf" | "document" (auto)
- profile: "strict" | "balanced" | "permissive" | "code_assistant" | "ai_safety" (balanced)
- analysis_mode: "fast" | "secure" | "comprehensive" (secure)
- session_id: string (use for multi-turn attack tracking)
- scan_group_id: UUID (required when scan_phase="output"; reuse for paired input and output)
- request_id: UUID (idempotency; duplicates return cached results)
- context: user_prompt | assistant_response | image_ocr | pdf_text | document_text | vision
- original_prompt: include with output scan to support drift checks
- async: boolean (false). For large image/PDF scans, set true then poll GET /v1/scan/{scan_id}
- webhook_url: only with async=true

## Response fields
- action: ALLOW | WARN | BLOCK
- risk_score: 0-100
- risk_level: MINIMAL | LOW | MEDIUM | HIGH | CRITICAL
- threats: [{category, confidence, reason}, ...]
- content_type_detected: text | image | pdf | document
- extracted_text: OCR excerpt (images/PDFs; truncated)
- scan_id, scan_status, preliminary
- processing_ms

## Common errors
- 400 invalid_content_type / invalid_scan_phase / missing_scan_group_id
- 401 unauthorized
- 402 payment_required
- 413 payload_too_large (50MB default)
- 503 vision_unavailable

## Local tooling
- `scripts/scan_gateway.py` supports:
- `--dry-run` to print the URL/headers/payload without sending a request.
- `--print-curl` to print a copy-pastable curl command (uses `$MIGHTY_API_KEY` to avoid leaking a real key).
- For offline request/response-shape testing, run the local stub server:
- `python scripts/mock_gateway_server.py --port 18081`
- `python scripts/scan_gateway.py --api-key test --base-url http://127.0.0.1:18081 --text "hello"`
