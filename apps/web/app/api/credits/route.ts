import { NextResponse } from "next/server"

import { apiFetchWithAuth } from "@/lib/api"
import { setAuthCookies } from "@/lib/auth-cookies"

export async function GET() {
  const { resp, newAccess, newRefresh } = await apiFetchWithAuth("/api/credits/me/")
  const text = await resp.text()
  const out = new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  })
  if (newAccess && newRefresh) {
    setAuthCookies(out, newAccess, newRefresh)
  }
  return out
}
