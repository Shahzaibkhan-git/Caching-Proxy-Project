# Project Flow and Architecture Guide

## 1. What this project is

`caching-proxy` is a lightweight HTTP proxy that sits between clients and an origin server.

It does three core things:

1. Receives client requests on a local port.
2. Forwards requests to an origin server.
3. Caches repeatable responses (currently `GET`) and serves them faster on future requests.

The project is useful when the same API endpoints are called repeatedly and you want:

- lower latency
- reduced origin load
- better resilience during temporary origin slowness

## 2. High-level flow

```text
Client -> Caching Proxy -> Origin Server
           |        ^
           v        |
        Cache Store
```

Runtime behavior:

1. Client sends request to proxy (`localhost:<port>`).
2. Proxy builds target URL by combining origin + incoming path/query.
3. If method is cacheable (`GET`):
   - Proxy checks cache by key (`METHOD + URL`).
   - If found, returns cached response with `X-Cache: HIT`.
4. If not cached (or non-cacheable method):
   - Proxy forwards request to origin.
   - Returns response to client with `X-Cache: MISS`.
   - If method is cacheable, stores response in cache.


                  User runs command
                        │
                        ▼
               cli.py  ← ENTRY POINT
                        │
                        ▼
            server.py ← Starts proxy server
                        │
                        ▼
   cache.py ← Stores and retrieves cached responses


## 3. Code-level responsibilities

### `src/caching_proxy/cli.py`

Purpose:

- Defines command-line interface.
- Validates startup input.
- Starts server or clears cache.

Key behaviors:

- `--port` + `--origin` start proxy server.
- `--clear-cache` clears stored cache and exits.

### `src/caching_proxy/server.py`

Purpose:

- Handles incoming HTTP requests.
- Forwards requests to origin.
- Applies caching rules.

Key behaviors:

- `GET` is cacheable.
- `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD` are forwarded without caching.
- Adds `X-Cache: HIT` or `X-Cache: MISS`.
- Removes hop-by-hop headers when proxying responses.

### `src/caching_proxy/cache.py`

Purpose:

- Manages persistence of cached responses.

Key behaviors:

- Key generation uses SHA-256 of `METHOD|URL`.
- Cached payload includes status, reason, headers, body.
- Body is Base64-encoded in JSON files.
- Cache directory defaults to:
  - `$XDG_CACHE_HOME/caching-proxy`
  - or `~/.cache/caching-proxy`

## 4. Cache strategy in current implementation

Current policy:

- Cache only `GET` responses.
- No TTL/expiry.
- No conditional revalidation (`ETag`, `If-None-Match`).
- No size-based eviction policy.

What this means:

- Good for learning and small workloads.
- For long-running production use, cache freshness and size controls should be added.

## 5. Where this can be used

Good fit:

- Local dev acceleration for API-heavy frontend apps.
- Internal tooling that repeatedly fetches same endpoints.
- Small edge service reducing traffic to expensive upstream APIs.
- Demo or PoC environments to illustrate caching impact.

Less ideal without extension:

- Highly dynamic data where freshness is critical.
- Multi-node deployments requiring shared cache consistency.
- High-throughput internet-facing gateways.

## 6. How to integrate into complex real projects

## Pattern A: Sidecar proxy per service

Use case:

- Each app/service runs its own nearby caching proxy.

Flow:

1. Service calls local proxy (`http://127.0.0.1:<port>`).
2. Proxy fetches from remote origin and caches.

Benefits:

- Very low network overhead.
- Easy service-specific cache rules.

Tradeoff:

- Cache not shared across instances.

## Pattern B: Shared internal caching gateway

Use case:

- Many services consume the same upstream APIs.

Flow:

1. Services call one central caching proxy cluster.
2. Gateway handles cache and origin routing.

Benefits:

- Shared cache hit rate.
- Centralized monitoring and policy.

Tradeoff:

- Needs high availability and scaling plan.

## Pattern C: Behind API Gateway / Ingress

Use case:

- External traffic enters via API gateway.

Flow:

1. API Gateway handles auth/rate limiting.
2. Gateway routes selected paths to caching proxy layer.
3. Proxy caches origin responses.

Benefits:

- Cleaner separation of concerns.
- Caching added without changing app code.

## 7. Production-hardening roadmap

To move from this learning project to production, add these in order:

1. Cache expiry and invalidation:
   - TTL per route
   - manual purge by key/prefix
   - stale-while-revalidate
2. Shared cache backend:
   - Redis or Memcached
   - support distributed deployments
3. Safety and correctness:
   - cache-control support (`Cache-Control`, `Expires`, `Vary`)
   - bypass caching for auth-specific/private responses
4. Reliability:
   - timeout/retry policy
   - circuit breaker and fallback behavior
5. Observability:
   - metrics (`hit_rate`, latency, upstream errors)
   - structured logs + request IDs
   - tracing integration (OpenTelemetry)
6. Security:
   - strict origin allowlist
   - request/response size limits
   - TLS termination strategy
7. Performance:
   - async server stack or high-performance reverse proxy front
   - connection pooling to origin

## 8. Common integration rules for real systems

Use these rules in complex projects:

- Cache only idempotent safe operations by default (`GET`, maybe `HEAD`).
- Never cache user-private data unless key includes user context and policy allows it.
- Respect upstream caching headers when available.
- Keep cache keys explicit:
  - method
  - full URL
  - relevant request headers from `Vary`
- Monitor and alert on:
  - low hit rate
  - origin latency spikes
  - cache store failures

## 9. Suggested next extensions in this codebase

Practical next steps for this repo:

1. Add TTL metadata in `cache.py`.
2. Add `--cache-ttl` CLI flag in `cli.py`.
3. Implement route-level caching rules in `server.py`.
4. Add tests:
   - unit tests for key generation and TTL behavior
   - integration tests for `MISS -> HIT -> EXPIRED -> MISS`
5. Add optional Redis backend for multi-instance use.

## 10. Summary

This project already demonstrates the essential caching-proxy lifecycle:

- proxying
- caching
- cache hit/miss signaling
- manual invalidation

With TTL, standards-based caching headers, shared cache backend, and observability, the same architecture can be integrated into real, complex production systems.
