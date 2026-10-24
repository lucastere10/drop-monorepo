import { cookies } from "next/headers"
import { NextResponse } from "next/server"

import { ACCESS_COOKIE, REFRESH_COOKIE, apiBaseUrl } from "@/lib/api"
import { clearAuthCookies } from "@/lib/auth-cookies"

export async function POST() {
  const jar = await cookies()
  const refresh = jar.get(REFRESH_COOKIE)?.value
  if (refresh) {
    await fetch(`${apiBaseUrl()}/api/auth/logout/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${jar.get(ACCESS_COOKIE)?.value || ""}`,
      },
      body: JSON.stringify({ refresh }),
    }).catch(() => null)
  }
  const res = new NextResponse(null, { status: 204 })
  clearAuthCookies(res)
  return res
}
