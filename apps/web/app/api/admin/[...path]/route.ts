import { NextResponse } from "next/server"

import { setAuthCookies } from "@/lib/auth-cookies"
import { apiFetchWithAuth } from "@/lib/api"

type Ctx = { params: Promise<{ path: string[] }> }

async function proxy(request: Request, ctx: Ctx) {
  const { path } = await ctx.params
  const url = new URL(request.url)
  const target = `/api/admin/${path.join("/")}/${url.search}`
  const init: RequestInit = { method: request.method }
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text()
  }
  const { resp, newAccess, newRefresh } = await apiFetchWithAuth(target, init)
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

export const GET = proxy
export const POST = proxy
export const PATCH = proxy
