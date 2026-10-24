import { cookies } from "next/headers"
import { NextResponse } from "next/server"

import { ACCESS_COOKIE, REFRESH_COOKIE, apiBaseUrl } from "@/lib/api"
import { setAuthCookies } from "@/lib/auth-cookies"

/** Refresh tokens using the httpOnly refresh cookie. Returns new access or null. */
export async function refreshAccessToken(): Promise<string | null> {
  const jar = await cookies()
  const refresh = jar.get(REFRESH_COOKIE)?.value
  if (!refresh) return null

  const resp = await fetch(`${apiBaseUrl()}/api/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  })
  if (!resp.ok) return null
  const data = await resp.json().catch(() => ({}))
  if (!data.access) return null

  // Note: cookie mutation here only works when called from a Route Handler / Server Action
  // that returns a NextResponse. Callers in Route Handlers should use refreshAndApplyCookies.
  return data.access as string
}

export async function refreshAndApplyCookies(res: NextResponse): Promise<string | null> {
  const jar = await cookies()
  const refresh = jar.get(REFRESH_COOKIE)?.value
  if (!refresh) return null

  const resp = await fetch(`${apiBaseUrl()}/api/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  })
  if (!resp.ok) return null
  const data = await resp.json().catch(() => ({}))
  if (!data.access) return null
  setAuthCookies(res, data.access, data.refresh || refresh)
  return data.access as string
}

export async function getAccessTokenRaw(): Promise<string | undefined> {
  const jar = await cookies()
  return jar.get(ACCESS_COOKIE)?.value
}
