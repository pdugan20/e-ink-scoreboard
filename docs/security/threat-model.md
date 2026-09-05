# E-Ink Scoreboard threat model

## Protected assets and boundaries

Protected assets are administrative configuration, local filesystem state, device and
network availability, feed configuration, and the integrity of displayed content. HTTP
requests, external scores and feeds, configuration values, and browser-rendered content
are untrusted. The service may be reachable by other devices on the local network.

## Required controls

- Require the configured administrator session for every write operation and use secure
  defaults when no password has been provisioned.
- Validate configuration types, paths, URLs, sizes, and destinations before filesystem,
  browser, or network use.
- Restrict external fetching to intended HTTPS sources and prevent redirects or resolved
  addresses from reaching local/private network services.
- Escape upstream content before HTML rendering and bound browser, image, and feed work by
  timeout, size, and concurrency.
- Write configuration atomically and keep documented backend/frontend copies synchronized.

Update this model when authentication, network exposure, configuration writes, external
feeds, browser automation, or device-control paths change.
