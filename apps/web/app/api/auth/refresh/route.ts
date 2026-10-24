import { cookies } from "next/headers"
import { NextResponse } from "next/server"

import { REFRESH_COOKIE, apiBaseUrl } from "@/lib/api"
import { setAuthCookies } from "@/lib/auth-cookies"

export async function POST() {
  const jar = await cookies()
  const refresh = jar.get(REFRESH_COOKIE)?.value
  if (!refresh) {
    return NextResponse.json({ code: "no_refresh", message: "Sem sessão." }, { status: 401 })
  }
  const resp = await fetch(`${apiBaseUrl()}/api/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  })
  const data = await resp.json().catch(() => ({}))
  if (!resp.ok) {
    return NextResponse.json(data, { status: resp.status })
  }
  const res = NextResponse.json({ ok: true })
  setAuthCookies(res, data.access, data.refresh || refresh)
  return res
}
