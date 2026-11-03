# E-Ink Scoreboard threat model

## Protected assets and boundaries

Protected assets are administrative configuration, local filesystem state, device and
network availability, feed configuration, and the integrity of displayed content. HTTP
requests, external scores and feeds, configuration values, and browser-rendered content
are untrusted. The service may be reachable by other devices on the local network.

## Current deployment assumption

Authentication is optional: `src/api/auth.py` treats requests as authenticated when
`src/.admin_password` is absent. This is an open-admin, trusted-LAN deployment mode,
not a secure default for an untrusted network. Provision a password before exposing
administrative endpoints beyond trusted operators. The controls below are review
requirements, not a claim that every fetch path currently implements them.

## Required controls

- Require the configured administrator session and CSRF validation for write operations.
  Treat a missing password as open access; do not widen network exposure silently.
- Validate configuration types, paths, URLs, sizes, and destinations before filesystem,
  browser, or network use.
- Restrict external fetching to intended HTTPS sources and prevent redirects or resolved
  addresses from reaching local/private network services.
- Escape upstream content before HTML rendering and bound browser, image, and feed work by
  timeout, size, and concurrency.
- Write configuration atomically and keep documented backend/frontend copies synchronized.

Update this model when authentication, network exposure, configuration writes, external
feeds, browser automation, or device-control paths change.
