# Security

Use the latest release and place shared deployments behind HTTPS. A random workspace token is required for network binding. The token is a workspace credential, not a multi-user authorization system.

If you discover a security issue, use GitHub's private vulnerability reporting when available. Do not include active credentials or a usable private target in a public issue. Ordinary reproducible bugs can use the issue template after removing sensitive data.

## Supported boundaries

- Public HTTP(S) fetches validate resolved addresses and redirects and pin connections while keeping TLS verification enabled. Private, loopback, link-local and reserved destinations are blocked.
- Download byte/type/resolution checks limit individual fetched resources. Restrict egress and enforce request-body limits at the reverse proxy for a shared deployment.
- Model output is rendered as text and resolved against known evidence IDs. Never add raw `innerHTML` rendering for model/page content.
- API secrets stay server-side. Browser access uses an HttpOnly, SameSite session cookie; HTTPS adds Secure.
- Query history and cached answers may contain sensitive user input. Configure retention, protect deployment volumes, and avoid public logs containing queries.

Prompt injection and incorrect model answers remain possible. Source attribution is a verification aid, not an assurance that a claim is true. The current service does not provide multi-tenant data separation, an account system, or a distributed rate limiter.
