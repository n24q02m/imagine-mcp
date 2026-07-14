import { describe, expect, it } from 'vitest'
import worker, { ImagineContainer, OUTBOUND_BY_HOST } from '../src/worker'

function fakeEnv() {
  const kv = new Map<string, ArrayBuffer>()
  return {
    KV: {
      get: async (k: string, _type?: 'arrayBuffer') => (kv.has(k) ? kv.get(k)! : null),
      put: async (k: string, v: ArrayBuffer) => void kv.set(k, v),
      delete: async (k: string) => void kv.delete(k),
    },
  }
}

// Invoke an outbound handler DIRECTLY (the production path is the container proxy
// via ImagineContainer.outboundByHost; the handlers are NOT reachable through the
// public `fetch` entrypoint, so tests exercise them through the exported registry).
const kvH = OUTBOUND_BY_HOST['kv.internal']!

describe('outbound registry (KV-only)', () => {
  it('registers a kv.internal outbound handler', () => {
    expect(ImagineContainer.outboundByHost['kv.internal']).toBeDefined()
    expect(OUTBOUND_BY_HOST['kv.internal']).toBeDefined()
  })

  it('does NOT register d1/vectorize handlers (KV-only)', () => {
    expect(OUTBOUND_BY_HOST['d1.internal']).toBeUndefined()
    expect(OUTBOUND_BY_HOST['vectorize.internal']).toBeUndefined()
    expect(ImagineContainer.outboundByHost['d1.internal']).toBeUndefined()
    expect(ImagineContainer.outboundByHost['vectorize.internal']).toBeUndefined()
  })
})

describe('outbound handlers', () => {
  it('KV get 404 then put then get 200 (binary arrayBuffer round-trip)', async () => {
    const env = fakeEnv()
    const key = 'imagine%2Fsubs%2Fuser1%2Fconfig'
    const blob = new Uint8Array([1, 2, 3, 250, 0, 99]).buffer

    let res = await kvH(new Request(`http://kv.internal/${key}`), env as never)
    expect(res.status).toBe(404)

    res = await kvH(new Request(`http://kv.internal/${key}`, { method: 'PUT', body: blob }), env as never)
    expect(res.status).toBe(200)

    res = await kvH(new Request(`http://kv.internal/${key}`), env as never)
    expect(res.status).toBe(200)
    expect(new Uint8Array(await res.arrayBuffer())).toEqual(new Uint8Array(blob))
  })

  it('KV readiness probe: GET __ready -> {ready:true}', async () => {
    const env = fakeEnv()
    const res = await kvH(new Request('http://kv.internal/__ready'), env as never)
    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ ready: true })
  })

  it('KV readiness probe does not shadow a real missing key', async () => {
    const env = fakeEnv()
    // a real key that happens to be absent still 404s (the probe is the reserved __ready only)
    const res = await kvH(new Request('http://kv.internal/imagine%2Fsubs%2Fu1%2Fconfig'), env as never)
    expect(res.status).toBe(404)
  })
})

describe('public fetch entrypoint does NOT expose outbound handlers (security)', () => {
  it('a public request with an internal hostname is NOT serviced by a handler', async () => {
    const env = fakeEnv() // no IMAGINE binding -> DO routing path returns 404
    // Even if an external caller spoofs the hostname to kv.internal, the public
    // fetch must NOT read/write the credential KV — it only routes to the DO.
    const res = await worker.fetch(new Request('http://kv.internal/imagine%2Fconfig'), env as never)
    expect(res.status).toBe(404)
    expect(await res.text()).toBe('not found')
  })
})

describe('single-user DO contract (E.2)', () => {
  function envWithDoSpy() {
    const calls: string[] = []
    return {
      calls,
      env: {
        IMAGINE: {
          idFromName: (n: string) => {
            calls.push(n)
            return { name: n }
          },
          get: (_id: unknown) => ({ fetch: async () => new Response('routed', { status: 200 }) }),
        },
      },
    }
  }

  it('no Bearer token on a non-/mcp path -> routes to the "default" DO', async () => {
    // Uses /authorize, not /mcp: the edge auth gate (added alongside this test)
    // now rejects an unauthenticated /mcp request before extractUserId() is
    // ever reached, so /mcp is no longer a valid path to exercise the DO-naming
    // fallback in isolation. /authorize is unauthenticated by design (it is
    // where mcp-core's OAuth AS itself issues the token) and stays ungated.
    const { calls, env } = envWithDoSpy()
    const res = await worker.fetch(new Request('https://imagine.n24q02m.com/authorize'), env as never)
    expect(res.status).toBe(200)
    expect(calls).toEqual(['default'])
  })

  it('Bearer token without sub -> routes to the "default" DO', async () => {
    const { calls, env } = envWithDoSpy()
    // header.payload.sig where payload has no `sub`
    const jwt = `h.${btoa(JSON.stringify({ aud: 'x' }))}.s`
    // POST, not GET: GET /mcp is declined with 405 at the edge (see "edge gate
    // declines standing GET /mcp SSE stream" below) before extractUserId() is
    // ever reached, so it is no longer a valid path to exercise DO routing.
    await worker.fetch(
      new Request('https://imagine.n24q02m.com/mcp', {
        method: 'POST',
        headers: { authorization: `Bearer ${jwt}` },
      }),
      env as never,
    )
    expect(calls).toEqual(['default'])
  })

  it('Bearer token with sub -> still routes to the "default" DO (SINGLE-DO COLLAPSE, see extractUserId)', async () => {
    const { calls, env } = envWithDoSpy()
    const jwt = `h.${btoa(JSON.stringify({ sub: 'user-123' }))}.s`
    await worker.fetch(
      new Request('https://imagine.n24q02m.com/mcp', {
        method: 'POST',
        headers: { authorization: `Bearer ${jwt}` },
      }),
      env as never,
    )
    expect(calls).toEqual(['default'])
  })
})

describe('edge auth gate rejects anonymous /mcp before touching the container DO', () => {
  function envWithDoSpy() {
    let stubCalls = 0
    return {
      calls: () => stubCalls,
      env: {
        IMAGINE: {
          idFromName: (n: string) => ({ name: n }),
          get: (_id: unknown) => ({
            fetch: async () => {
              stubCalls++
              return new Response('routed', { status: 200 })
            },
          }),
        },
      },
    }
  }

  it('POST /mcp with no Authorization -> 401, stub never called', async () => {
    const { calls, env } = envWithDoSpy()
    const res = await worker.fetch(new Request('https://imagine.n24q02m.com/mcp', { method: 'POST' }), env as never)
    expect(res.status).toBe(401)
    expect(res.headers.get('WWW-Authenticate')).toMatch(
      /^Bearer resource_metadata="https:\/\/[^"]+\/\.well-known\/oauth-protected-resource"$/,
    )
    expect(await res.text()).toBe('')
    expect(calls()).toBe(0)
  })

  it('OPTIONS /mcp with no Authorization -> 401, stub never called', async () => {
    const { calls, env } = envWithDoSpy()
    const res = await worker.fetch(new Request('https://imagine.n24q02m.com/mcp', { method: 'OPTIONS' }), env as never)
    expect(res.status).toBe(401)
    expect(calls()).toBe(0)
  })

  it('POST //mcp (obfuscated path) with no Authorization -> 401, stub never called', async () => {
    const { calls, env } = envWithDoSpy()
    const res = await worker.fetch(new Request('https://imagine.n24q02m.com//mcp', { method: 'POST' }), env as never)
    expect(res.status).toBe(401)
    expect(calls()).toBe(0)
  })

  it('POST /%2Fmcp (URI-encoded obfuscated path) with no Authorization -> 401, stub never called', async () => {
    const { calls, env } = envWithDoSpy()
    const res = await worker.fetch(new Request('https://imagine.n24q02m.com/%2Fmcp', { method: 'POST' }), env as never)
    expect(res.status).toBe(401)
    expect(calls()).toBe(0)
  })

  it('POST /mcp with a malformed URI (e.g. invalid %) falls back to raw path without crashing', async () => {
    const { calls, env } = envWithDoSpy()
    // A malformed path that decodeURIComponent would throw on, but isn't /mcp
    // envWithDoSpy gives it an IMAGINE stub that returns 200, so it will pass through to the DO.
    const res = await worker.fetch(new Request('https://imagine.n24q02m.com/foo%2'), env as never)
    expect(res.status).toBe(200) // Passes through safely
    expect(calls()).toBe(1)
  })

  it('POST /mcp with Authorization: Bearer anything -> stub called exactly once', async () => {
    const { calls, env } = envWithDoSpy()
    const res = await worker.fetch(
      new Request('https://imagine.n24q02m.com/mcp', {
        method: 'POST',
        headers: { authorization: 'Bearer anything' },
      }),
      env as never,
    )
    expect(res.status).toBe(200)
    expect(calls()).toBe(1)
  })

  it('GET /authorize with no Authorization -> non-/mcp path passes through to the DO', async () => {
    const { calls, env } = envWithDoSpy()
    const res = await worker.fetch(new Request('https://imagine.n24q02m.com/authorize?foo=1'), env as never)
    expect(res.status).toBe(200)
    expect(calls()).toBe(1)
  })
})

describe('edge gate declines the standing GET /mcp SSE stream (405)', () => {
  function envWithDoSpy() {
    let stubCalls = 0
    return {
      calls: () => stubCalls,
      env: {
        IMAGINE: {
          idFromName: (n: string) => ({ name: n }),
          get: (_id: unknown) => ({
            fetch: async () => {
              stubCalls++
              return new Response('routed', { status: 200 })
            },
          }),
        },
      },
    }
  }

  it('GET /mcp with a Bearer token -> 405, Allow: POST, DELETE, stub never called', async () => {
    const { calls, env } = envWithDoSpy()
    const res = await worker.fetch(
      new Request('https://imagine.n24q02m.com/mcp', { headers: { authorization: 'Bearer x' } }),
      env as never,
    )
    expect(res.status).toBe(405)
    expect(res.headers.get('Allow')).toBe('POST, DELETE')
    expect(calls()).toBe(0)
  })

  it('GET /mcp/sub with a Bearer token -> 405, stub never called', async () => {
    const { calls, env } = envWithDoSpy()
    const res = await worker.fetch(
      new Request('https://imagine.n24q02m.com/mcp/sub', { headers: { authorization: 'Bearer x' } }),
      env as never,
    )
    expect(res.status).toBe(405)
    expect(res.headers.get('Allow')).toBe('POST, DELETE')
    expect(calls()).toBe(0)
  })

  it('GET /mcp with no Authorization -> still 401 (bearer gate runs before the 405 decline)', async () => {
    const { calls, env } = envWithDoSpy()
    const res = await worker.fetch(new Request('https://imagine.n24q02m.com/mcp'), env as never)
    expect(res.status).toBe(401)
    expect(calls()).toBe(0)
  })
})
