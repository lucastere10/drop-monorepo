import { cookies } from "next/headers"

export const ACCESS_COOKIE = "drop_access"
export const REFRESH_COOKIE = "drop_refresh"

export function apiBaseUrl() {
  return process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
}

export async function getAccessToken(): Promise<string | undefined> {
  const jar = await cookies()
  return jar.get(ACCESS_COOKIE)?.value
}

/**
 * Server-side fetch to Django API with Bearer token.
 * On 401, tries refresh once via internal cookie update is NOT possible here —
 * Route Handlers should prefer `apiFetchWithRefresh` from session helpers.
 */
export async function apiFetch(path: string, init: RequestInit = {}) {
  const token = await getAccessToken()
  const headers = new Headers(init.headers)
  if (token) headers.set("Authorization", `Bearer ${token}`)
  if (!headers.has("Content-Type") && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json")
  }
  return fetch(`${apiBaseUrl()}${path}`, { ...init, headers, cache: "no-store" })
}

export async function apiFetchWithAuth(path: string, init: RequestInit = {}) {
  const jar = await cookies()
  let token = jar.get(ACCESS_COOKIE)?.value
  const refresh = jar.get(REFRESH_COOKIE)?.value

  const doFetch = (access?: string) => {
    const headers = new Headers(init.headers)
    if (access) headers.set("Authorization", `Bearer ${access}`)
    if (!headers.has("Content-Type") && !(init.body instanceof FormData)) {
      headers.set("Content-Type", "application/json")
    }
    return fetch(`${apiBaseUrl()}${path}`, { ...init, headers, cache: "no-store" })
  }

  let resp = await doFetch(token)
  if (resp.status !== 401 || !refresh) {
    return { resp, newAccess: null as string | null, newRefresh: null as string | null }
  }

  const refreshResp = await fetch(`${apiBaseUrl()}/api/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  })
  if (!refreshResp.ok) {
    return { resp, newAccess: null, newRefresh: null }
  }
  const data = await refreshResp.json().catch(() => ({}))
  if (!data.access) {
    return { resp, newAccess: null, newRefresh: null }
  }
  resp = await doFetch(data.access)
  return {
    resp,
    newAccess: data.access as string,
    newRefresh: (data.refresh as string) || refresh,
  }
}
