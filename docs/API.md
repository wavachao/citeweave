# API reference

Base URL: your own CiteWeave deployment. JSON endpoints are same-origin by default; cross-origin browser access is not enabled.

## Authentication

Protected searches and cached media accept `Authorization: Bearer <workspace-token>`. The web UI exchanges that same workspace token through `POST /api/session` with `{"token":"…"}` for an eight-hour HttpOnly, SameSite=Strict cookie. HTTPS requests receive a Secure cookie. `DELETE /api/session` clears it.

`GET /api/status` reports whether the current request needs authentication, without returning credentials. With no configured token, only loopback requests can search. Health endpoints and static UI assets are public.

## `POST /api/search`

```json
{
  "query": "How did Eratosthenes measure Earth's circumference?",
  "urls": ["https://en.wikipedia.org/wiki/Eratosthenes"],
  "verify_images": true,
  "refresh": false
}
```

| Field | Type | Behavior |
|---|---|---|
| `query` | string | Required, 2–3,000 characters. |
| `urls` | string[] | Optional, maximum five public HTTP(S) pages. Empty performs search discovery. |
| `verify_images` | boolean | Default true. Uses the local vision model to describe candidate images. |
| `refresh` | boolean | Default false. Bypasses the TTL answer cache when true. |

A successful response includes:

```json
{
  "query": "…",
  "title": "…",
  "blocks": [{"text":"…", "source_ids":["s0"], "image_id":"i0", "image_caption":"…"}],
  "sources": [{"id":"s0", "title":"…", "url":"https://…", "preview_image":{}}],
  "images": [{"id":"i0", "url":"https://…", "render_url":"/cache/…", "source_url":"https://…", "caption":"…"}],
  "mode": "live_web",
  "total_seconds": 18.4,
  "cache_hit": false,
  "created_at": 1792410000.0
}
```

The response also includes generation usage and retrieval diagnostics. `image_id` is null when a block has no illustration. Raw model traces and internal image-file paths are excluded from browser responses.

## Status codes

| Code | Meaning |
|---|---|
| `200` | Completed answer or valid cached answer. |
| `401` | Missing/invalid workspace credential. |
| `409` | The compute worker is busy; inspect `Retry-After`. |
| `413` | Request JSON exceeds 16 KiB. |
| `415` | POST body is not JSON. |
| `422` | Invalid request fields. |
| `429` | Per-address admission limit; inspect `Retry-After`. |
| `503` | Retrieval/model execution could not complete. Use `X-Request-ID` to find server logs. |

`GET /health` checks process liveness; `GET /ready` checks required model configs. Neither endpoint performs GPU inference. The interactive OpenAPI reference is available at `/docs`.
