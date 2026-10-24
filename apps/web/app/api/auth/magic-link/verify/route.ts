import { NextResponse } from "next/server"

import { apiBaseUrl } from "@/lib/api"
import { setAuthCookies } from "@/lib/auth-cookies"

export async function POST(request: Request) {
  const body = await request.json()
  const resp = await fetch(`${apiBaseUrl()}/api/auth/magic-link/verify/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  const data = await resp.json().catch(() => ({}))
  if (!resp.ok) {
    return NextResponse.json(data, { status: resp.status })
  }
  const res = NextResponse.json({ user: data.user })
  setAuthCookies(res, data.access, data.refresh)
  return res
}
