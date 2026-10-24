import { NextResponse } from "next/server"

import { apiFetchWithAuth } from "@/lib/api"
import { setAuthCookies, clearAuthCookies } from "@/lib/auth-cookies"

export async function GET() {
  const { resp, newAccess, newRefresh } = await apiFetchWithAuth("/api/auth/me/")
  const data = await resp.json().catch(() => ({}))
  const out = NextResponse.json(data, { status: resp.status })
  if (resp.status === 401) {
    clearAuthCookies(out)
  } else if (newAccess && newRefresh) {
    setAuthCookies(out, newAccess, newRefresh)
  }
  return out
}

export async function PATCH(request: Request) {
  const body = await request.json()
  const { resp, newAccess, newRefresh } = await apiFetchWithAuth("/api/auth/me/", {
    method: "PATCH",
    body: JSON.stringify(body),
  })
  const data = await resp.json().catch(() => ({}))
  const out = NextResponse.json(data, { status: resp.status })
  if (newAccess && newRefresh) {
    setAuthCookies(out, newAccess, newRefresh)
  }
  return out
}
